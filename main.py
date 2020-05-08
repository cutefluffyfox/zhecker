from json import load
import time
import datetime
from os import environ
import atexit

from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_restful import Api
from requests import get
from apscheduler.schedulers.background import BackgroundScheduler

import create_environment  # creatng environment variables
from db_session import global_init
import forms
from models import User, Contest, Task, __init__, Attempt
import resources


global_init('database.db')
__init__()
app = Flask(__name__)
app.config['SECRET_KEY'] = environ['APP_KEY']
api = Api(app)
login_manager = LoginManager(app)


def update_server():
    print('Update background task: ', get('https://zhecker.herokuapp.com/'))


scheduler = BackgroundScheduler()
scheduler.add_job(func=update_server, trigger="interval", minutes=15)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
@app.route('/intro')
def intro():
    """Титульная страница сайта"""
    return render_template('introduction.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация"""
    error, verdict = "", ""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        name = form.name.data
        surname = form.surname.data
        city = form.city.data

        if len(password) < 8:
            error = "Длина Пароля должна быть не менее 8 символов"
        if "@" and "." not in email:
            error = "Неправильный формат электронной почты"
        if len(error) == 0:
            new_user = User.add_user(username=username,
                                    password=password,
                                    email=email,
                                    name=name,
                                    surname=surname,
                                    city=city)

            status = new_user.get("status")
            print(status)
            if status == "ok":
                verdict = 'Мы выслали вам письмо с подтверждением аккаунта'
            elif status == 'username is already taken':
                error = "Пользователь с таким именем пользователя уже существует"
            elif status == "email not send":
                error = "Не удалось отправить письмо"
            elif status == 'email is already taken':
                error = "Пользователь с такой электронной почтой уже существует"

    return render_template('register.html',
                           form=form,
                           error=error,
                           verdict=verdict)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""
    error = ""
    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        user = User.authorize_user(username, password)

        if user is None:
            error = "Неверный логин или пароль"
        else:
            login_user(user, remember=remember)
            return redirect('/contests')

    return render_template('login.html',
                           form=form,
                           error=error)


@app.route('/profile/<int:user_id>')
@login_required
def profile_page(user_id):
    """Профиль"""
    creator, name, surname, city, email, error, api = False, "", "", "", "", "", ""

    user = User.get_user(user_id)
    if user is not None:
        creator = User.get_user(current_user.id).creator
        name = user.name
        surname = user.surname
        email = user.email
        api = user.api_key if user.api_key is not None else ""
        city = user.city if user.city is not None else ""

    else:
        error = "Такого пользователя не существует"

    return render_template('profile.html',
                           type="Профиль",
                           creator=creator,
                           name=name,
                           surname=surname,
                           city=city,
                           email=email,
                           error=error,
                           api=api,
                           current_id=current_user.id)


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people_page():
    """Профиль"""
    results, people, heading = [], [], []

    form = forms.PeopleSearch()
    if form.validate_on_submit():
        username = form.username.data
        people = User.get_users_by_username(username)

    for result in people:
        results.append([result.id, result.username, result.name, result.surname])
    if len(results) != 0:
        heading = ["id", "Имя", "пользователя", "Имя", "Фамилия"]
    return render_template('people.html',
                           type="Люди",
                           form=form,
                           people=results,
                           heading=heading,
                           current_id=current_user.id)


@app.route('/archive', methods=['GET', 'POST'])
@login_required
def archive_page():
    """Архив задач"""

    tasks, tasks_info = [], Task.get_tasks_by_title("")[:20]
    print(tasks_info, "default")
    form = forms.TaskSearch()
    if form.validate_on_submit():
        title = form.title.data
        tasks_info = Task.get_tasks_by_title(title)

    for i in tasks_info:
        tasks.append([i.id, i.title, i.description])
    print(tasks)

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('archive.html',
                           type="Архив",
                           creator=creator,
                           tasks=tasks,
                           form=form,
                           current_id=current_user.id)


@app.route('/task/<int:contest_id>/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_page(contest_id, task_id):
    """Задача"""
    code_file, code, status, error, verdict, attempts = "", "", "", "", "", []
    time_limit, title, author, description, question, input_data, output_data, task_edit, creator, edit = 0.0, "", "", "", "", [], [], "", False, False
    form = forms.CheckTask()

    task = Task.get_task(task_id)

    if task is not None:
        exist = True

        title = task.title
        description = task.description
        data = task.get_tests()[:2]
        input_data, output_data = [], []
        for i in data:
            input_data.append(i.input.split("\n"))
            output_data.append(i.output.split("\n"))

        edit = False
        print(task.creator, current_user.id)
        if task.creator == current_user.id:
            edit = True

        if request.method == "POST":
            if request.files:
                code_file = request.files["code_file"]
                code_file = code_file.read()
                code_file = code_file.decode('utf-8')
                print(code_file)
                form.written_code.data = ""

        if form.validate_on_submit():
            written_code = form.written_code.data
            form.written_code.data = ""

            if written_code:
                code = written_code
            else:
                code = code_file

        if len(code) != 0:
            attempt = Attempt.add_attempt(contest_id, task_id, current_user.id, code)
            status = attempt.get("status")
            print(status)
            if status == "ok":
                verdict = "Задача проверяется"
            elif status == "the same solution has already been sent":
                error = "Вы уже отправляли идетичное решение"


        author = User.get_user(task.creator).username  #-----------------------------------------обработка--------------------------
        print(author)

        creator = User.get_user(current_user.id).creator
        print(creator)
        time_limit = task.time_limit

        attempts = Attempt.get_attempts(contest_id, task_id, current_user.id)
        print(attempts)

    else:
        exist = False
        error = "Такой задачи не существуе"


    return render_template('task.html',
                           type="Задача",
                           exist=exist,
                           title=title,
                           question=description,
                           input_data=input_data,
                           output_data=output_data,
                           task_edit=edit,
                           form=form,
                           creator=creator,
                           task_id=task_id,
                           contest_id=contest_id,
                           verdict=verdict,
                           error=error,
                           author=author,
                           attempts=attempts,
                           time_limit=time_limit,
                           current_id=current_user.id)


@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    reference, error = "", ""
    tests = []
    form = forms.CreateTask()

    if request.method == "POST":
        if request.files:
            reference = request.files["reference"]
            reference = reference.read()
            reference = reference.decode('utf-8')

            tests = request.files["tests"]
            if tests:
                tests = load(tests)

    if form.validate_on_submit():
        creator = current_user.id
        title = form.title.data
        description = form.description.data
        time_limit = form.time_limit.data

        status = Task.add_task(creator, time_limit, title, description, reference, tests).get("status")
        if len(reference) == 0:
            error = "Некорректный формат эталона решения"

        elif status == "same task has already been added":
            error = "Такой турнир уже существует"

        elif status == "reference failed on tests, got error status'":
            error = "Вы не загрузили тесты"

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('create_task.html',
                           type="Создать задачу",
                           creator=creator,
                           form=form,
                           error=error,
                           current_id=current_user.id)


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):

    form = forms.EditTask()

    error, creator, verdict, new_reference, task_edit, edit = "", "", "", "", False, False
    task = Task.get_task(task_id)

    if task is not None:
        exist = True
        if request.method == "GET":
            print("GET success")
            form.title.data = task.title
            form.time_limit.data = task.time_limit
            form.description.data = task.description

        if request.method == "POST":
            print("POST success")
            if request.files:
                reference = request.files["reference"]
                reference = reference.read()
                new_reference = reference.decode('utf-8')

        if form.validate_on_submit():
            print("VALIDATE success")
            new_title = form.title.data
            new_description = form.description.data
            new_time_limit = form.time_limit.data

            if len(new_reference) == 0:
                new_reference = task.reference

            status = task.change_data(time_limit=new_time_limit if new_time_limit != task.time_limit else None,
                             title=new_title if new_title != task.title else None,
                             description=new_description if new_description != task.description else None,
                             reference=new_reference if new_reference != task.reference else None).get("status")

            print(status)
            if status == "ok":
                verdict = "Данные успешно изменены"
            if status == "same task has already been added":
                error = "Вы не внесли изменений"

        edit = False
        if task.creator == current_user.id:
            edit = True

        creator = User.get_user(current_user.id).creator
        print(creator)

    else:
        error = "Такой задачи не существует"
        exist = False

    return render_template('edit_task.html',
                           type="Изменить задачу",
                           exist=exist,
                           creator=creator,
                           form=form,
                           task_id=task_id,
                           task_edit=edit,
                           verdict=verdict,
                           error=error,
                           current_id=current_user.id)


@app.route('/system')
@login_required
def system():
    """О системе"""
    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('system.html',
                           type="О системе",
                           creator=creator,
                           current_id=current_user.id)


@app.route('/contests', methods=['GET', 'POST'])
@login_required
def contests_page():
    """Турниры"""
    """это нужно заменить на sql разумеется"""

    contests, contests_info = [], Contest.get_contest_by_title("")[1:21]

    form = forms.ContestSearch()
    if form.validate_on_submit():
        title = form.title.data
        contests_info = Contest.get_contest_by_title(title)

    for i in contests_info:
        contests.append([i.id,
                         i.title,
                         i.description,
                         datetime.datetime.fromtimestamp(i.start_time).strftime('%Y-%m-%d %H:%M:%S'),
                         datetime.datetime.fromtimestamp(i.end_time).strftime('%Y-%m-%d %H:%M:%S')])

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('contests.html',
                           type="Контесты",
                           creator=creator,
                           name=current_user.username,
                           contests=contests,
                           form=form,
                           current_id=current_user.id)


@app.route('/contest/<int:contest_id>')
@login_required
def contest_page(contest_id):
    """Турнир"""

    contest = Contest.get_contest(contest_id)
    creator, error, results, edit = "", "", [], False

    if contest is not None:
        exist = True
        tasks = contest.get_tasks()
        results = []
        for i in tasks:
            last_result = Attempt.get_last_result(contest_id, i.id, current_user.id)

            results.append([i.id, i.title, last_result.status if last_result is not None else ""])

        edit = False
        if str(current_user.id) in contest.creators.split(","):
            edit = True

        print(edit)

        creator = User.get_user(current_user.id).creator
        print(creator)

    else:
        error= "Такого контеста не существует"
        exist = False

    return render_template('contest.html',
                           type="Контест",
                           exist=exist,
                           creator=creator,
                           tasks=results,
                           contest_edit=edit,
                           current_id=current_user.id,
                           error=error,
                           contest_id=contest_id)


@app.route('/edit_contest/<int:contest_id>', methods=['GET', 'POST'])
@login_required
def edit_contest(contest_id):
    error, verdict, creator, edit = "", "", False, False

    form = forms.CreateContest()
    contest = Contest.get_contest(contest_id)
    if contest is not None:
        exist = True
        if request.method == "GET":
            form.title.data = contest.title
            form.creators.data = contest.creators
            form.description.data = contest.description
            form.tasks.data = contest.tasks

            start = datetime.datetime.fromtimestamp(contest.start_time).strftime('%Y-%m-%d %H:%M:%S').split()
            form.start_date.data = start[0]  #нужно распарсить аремя на date и time
            form.start_time.data = start[1]

            end = datetime.datetime.fromtimestamp(contest.end_time).strftime('%Y-%m-%d %H:%M:%S').split()
            form.end_date.data = end[0]
            form.end_time.data = end[1]

            print(form.start_time.data, form.end_time.data)

        if form.validate_on_submit():
            new_creators = tuple(form.creators.data.split(','))
            new_title = form.title.data
            new_description = form.description.data
            new_tasks = tuple(str(form.tasks.data).split(','))

            start_date = form.start_date.data
            start_time = form.start_time.data
            start = f"{start_date} {start_time}"
            start = time.strptime(start, "%Y-%m-%d %H:%M:%S")
            new_start = int(time.mktime(start))

            end_date = form.end_date.data
            end_time = form.end_time.data
            end = f"{end_date} {end_time}"
            end = time.strptime(end, "%Y-%m-%d %H:%M:%S")
            new_end = int(time.mktime(end))

            print(new_start, new_end)
            if new_start >= new_end:
                error = "Неправильный формат даты проведения турнира"

            status = contest.change_data(creators=new_creators if new_creators != contest.creators else None,
                                    title=new_title if new_title != contest.title else None,
                                    description=new_description if new_description != contest.description else None,
                                    tasks=new_tasks if new_tasks != contest.tasks else None,
                                    start_time=new_start if new_start != contest.start_time else None,
                                    end_time=new_end if new_end != contest.end_time else None).get("status")
            print(status)
            if status == "ok":
                verdict = "Данные успешно изменены"
            if status == "same contest has already been added":
                error = "Не были внесены изменения"

        creator = User.get_user(current_user.id).creator
        print(creator)

        edit = False
        print(current_user.id, contest.creators)
        if current_user.id in contest.creators.split(','):
            edit = True

    else:
        exist = False
        error = "Такого Контеста не существует"

    return render_template('edit_contest.html',
                           type="Изменить контест",
                           exist=exist,
                           form=form,
                           contest_edit=edit,
                           error=error,
                           creator=creator,
                           verdict=verdict,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/create_contest', methods=['GET', 'POST'])
@login_required
def create_contest():
    error = ""
    form = forms.CreateContest()
    if form.validate_on_submit():
        creators = form.creators.data
        creators = creators.replace(" ", "")
        creators = tuple(creators.split(','))

        title = form.title.data
        description = form.description.data
        tasks = tuple(str(form.tasks.data).split(','))

        start_date = form.start_date.data
        start_time = form.start_time.data + ":00"
        start = f"{start_date} {start_time}"
        start = time.strptime(start, "%Y-%m-%d %H:%M:%S")
        start = int(time.mktime(start))

        end_date = form.end_date.data
        end_time = form.end_time.data + ":00"
        end = f"{end_date} {end_time}"
        end = time.strptime(end, "%Y-%m-%d %H:%M:%S")
        end = int(time.mktime(end))

        status = Contest.add_contest(creators, title, description, tasks, start, end).get("status")
        print(creators, title, description, tasks, start, end)
        if start >= end:
            error = "Неправильный формат даты проведения турнира"

        elif status == "same contest has already been added":
            error = "Такой турнир уже существует"

    creator = User.get_user(current_user.id).creator
    print(creator)

    return render_template('create_contest.html',
                           type="Создать контест",
                           creator=creator,
                           error=error,
                           form=form,
                           current_id=current_user.id)


@app.route('/results/<int:contest_id>', methods=['GET', 'POST'])
@login_required
def results_page(contest_id):
    """Результаты"""
    title, tasks, creator, edit, rating = "", [], False, False, []
    error = ""
    contest = Contest.get_contest(contest_id)
    if contest is not None and contest_id != 0:
        exist = True
        title = contest.title

        edit = False
        print(current_user.id, contest.creators)
        if current_user.id == str(contest.creators):
            edit = True

        rating = enumerate(contest.get_rating())
        print(rating)
        tasks = [[i.id, i.title] for i in contest.get_tasks()]
        print(tasks)

        creator = User.get_user(current_user.id).creator
        print(creator)

    else:
        exist = False
        error = "Такого контеста не существует"
    return render_template('results.html',
                           type="Результаты",
                           exist=exist,
                           error=error,
                           title=title,
                           tasks=tasks,
                           create=creator,
                           rating=rating,
                           contest_edit=edit,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/attempts/<int:attempt_id>', methods=['GET'])
@login_required
def attempts_page(attempt_id):
    attempt = Attempt.get_attempt(attempt_id)
    tests, error = [], ""
    if attempt is not None:
        exist = True
        tests = enumerate(attempt.get_tests_statuses(), start=1)

    else:
        exist = False
        error = "Такой попытки не существует"

    return render_template('attempts.html',
                           type="Попытки",
                           exist=exist,
                           tests=tests,
                           error=error)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Настройки"""
    form = forms.ChangeSettings()

    user = User.get_user(current_user.id)
    error, verdict = "", ""

    if request.method == "GET":
        form.username.data = current_user.username
        form.name.data = current_user.name
        form.surname.data = current_user.surname
        form.city.data = current_user.city
        form.api.data = current_user.api_key is not None

    if form.validate_on_submit():
        new_username = form.username.data
        new_password = form.password.data
        new_name = form.name.data
        new_surname = form.surname.data
        new_city = form.city.data
        new_api = form.api.data

        if len(new_password) < 8 and len(new_password) != 0:
            error = "Длина пароля должна быть больше 8 символов"

        if len(error) == 0:
            if len(new_password) == 0:
                new_password = None

            print(new_api)
            status = user.change_data(username=new_username if new_username != current_user.username else None,
                                 name=new_name if new_name != current_user.name else None,
                                 surname=new_surname if new_surname != current_user.surname else None,
                                 city=new_city if new_city != current_user.city else None,
                                 password=new_password,
                                 api=new_api).get("status")
            print(status)
            if status == "ok":
                verdict = "Данные успешно изменены"

        print(new_username, new_name, new_surname, new_city, new_password, new_api)

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('settings.html',
                           type="Настройки",
                           creator=creator,
                           verdict=verdict,
                           error=error,
                           form=form,
                           current_id=current_user.id)


@app.route('/email_verification', methods=['GET'])
def email_verification():
    action_type = request.args.get('action_type')
    email = request.args.get('email')
    verification_key = request.args.get('verification_key')
    user = User.email_verification(email, verification_key, action_type)
    if user is not None:
        login_user(user, remember=True)
        return redirect('/contests')
    return redirect('/register')


@app.route('/creator_confirmation', methods=['GET'])
def creator_confirmation():
    action_type = request.args.get('action_type')
    user_id = request.args.get('user_id')
    confirmation_key = request.args.get('confirmation_key')
    User.creator_confirmation(user_id, confirmation_key, action_type)
    return redirect('/contests')


@app.route('/application', methods=['GET', 'POST'])
@login_required
def application():
    error, verdict = "", ""
    user = User.get_user(current_user.id)
    form = forms.Application()

    if form.validate_on_submit():
        reason = form.reason.data
        if len(reason) < 8:
            error = ""
        if len(error) == 0:
            status = user.send_creator_email(reason)
            print(status)
            verdict = "Запрос успешно отправлен"

    return render_template("application.html",
                           form=form,
                           current_id=current_user.id,
                           error=error,
                           verdict=verdict,
                           creator=user.creator)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/delete')
@login_required
def delete():
    user = User.get_user(current_user.id)
    user.delete_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error_pages/404.html'), 404


@app.errorhandler(401)
def page_not_found(e):
    return render_template('error_pages/401.html'), 401


@app.errorhandler(500)
def page_not_found(e):
    return render_template('error_pages/500.html'), 500


# common access
api.add_resource(resources.MeResource, '/api/v1/me')  # get, put
api.add_resource(resources.TasksResource, '/api/v1/tasks')  # get
api.add_resource(resources.ContestsResource, '/api/v1/contests')  # get
api.add_resource(resources.ContestResource, '/api/v1/contests/<int:contest_id>')  # get, put
api.add_resource(resources.ContestTaskResource, '/api/v1/contests/<int:contest_id>/<int:task_id>')  # get, post
api.add_resource(resources.AttemptResource, '/api/v1/attempts/<int:attempt_id>')  # get


app.run(host=environ.get('HOST', '0.0.0.0'), port=int(environ.get("PORT", 5000)))
