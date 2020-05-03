from json import load
import time
import datetime
from os import environ

from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, current_user

import create_environment  # creatng environment variables
from db_session import global_init
import forms
from models import User, Contest, Task, __init__, Attempt


global_init('database.db')
__init__()
app = Flask(__name__)
app.config['SECRET_KEY'] = environ['APP_KEY']
login_manager = LoginManager(app)


@app.route('/')
@app.route('/intro')
def intro():
    """Титульная страница сайта"""
    return render_template('introduction.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация"""
    error = ""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        name = form.name.data
        surname = form.surname.data
        city = form.city.data
        if "@" not in email:
            error = "Неправильный формат электронной почты"
        else:
            new_user = User.add_user(username=username,
                                    password=password,
                                    email=email,
                                    name=name,
                                    surname=surname,
                                    city=city)
            status = new_user.get("status")
            if status == "ok":
                error = 'Мы выслали вам письмо с подтверждением аккаунта'
            elif status == 'username is already taken':
                error = "Пользователь с таким именем пользователя уже существует"
            elif status == 'email is already taken':
                error = "Пользователь с такой электронной почтой уже существует"

    return render_template('register.html',
                           form=form,
                           error=error)


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
    user = User.get_user(user_id)
    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('profile.html',
                           type="Профиль",
                           creator=creator,
                           name=user.name,
                           surename=user.surname,
                           city=user.city,
                           mail=user.email,
                           current_id=current_user.id)


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people_page():
    """Профиль"""
    results = []
    people = []
    form = forms.PeopleSearch()
    if form.validate_on_submit():
        username = form.username.data
        people = User.get_users_by_username(username)

    for result in people:
        results.append([result.id, result.username, result.name, result.surname])

    return render_template('people.html',
                           type="Люди",
                           form=form,
                           people=results,
                           current_id=current_user.id)


@app.route('/archive', methods=['GET', 'POST'])
@login_required
def archive_page():
    """Архив задач"""

    tasks, tasks_info = [], []
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
    code_file, code, status, error, verdict = "", "", "", "", ""

    task = Task.get_task(task_id)
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

    form = forms.CheckTask()
    if request.method == "POST":
        if request.files:
            code_file = request.files["code_file"]
            code_file = code_file.read()
            code_file = code_file.decode('utf-8')
            print([code_file])

    if form.validate_on_submit():
        written_code = form.written_code.data

        if len(written_code) > 0 >= len(code_file):
            code = written_code

        elif len(written_code) == 0 > len(code_file):
            code = code_file

    if len(code) != 0:
        status = Attempt.add_attempt(contest_id, task_id, current_user.id, code).get("status")
        print(status)
        if status == "ok":
            verdict = "Задача проверяется"
        elif status == "the same solution has already been sent":
            error = "Вы уже отправляли идетичное решение"
            #дописать вердикт

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('task.html',
                           type="Задача",
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
    task = Task.get_task(task_id)
    form = forms.EditTask()

    error, new_reference = "", ""

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
        if status == "same task has already been added":
            error = "Вы не внесли изменений"

    edit = False
    if task.creator == current_user.id:
        edit = True

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('edit_task.html',
                           type="Изменить задачу",
                           creator=creator,
                           form=form,
                           task_id=task_id,
                           task_edit=edit,
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

    contests = []
    contests_info = []
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
    tasks = contest.get_tasks()
    results = []
    for i in tasks:
        results.append([i.id, i.title])

    edit = False
    print(current_user.id, contest.creators)
    print(type(current_user.id), type(contest.creators))
    if str(current_user.id) in contest.creators.split(","):
        edit = True

    print(edit)

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('contest.html',
                           type="Контест",
                           creator=creator,
                           tasks=results,
                           contest_edit=edit,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/edit_contest/<int:contest_id>', methods=['GET', 'POST'])
@login_required
def edit_contest(contest_id):
    error = ""
    form = forms.CreateContest()
    contest = Contest.get_contest(contest_id)

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
        if status == "same contest has already been added":
            error = "Не были внесены изменения"

    creator = User.get_user(current_user.id).creator
    print(creator)

    edit = False
    print(current_user.id, contest.creators)
    if current_user.id in contest.creators.split(','):
        edit = True

    return render_template('edit_contest.html',
                           type="Изменить контест",
                           form=form,
                           contest_edit=edit,
                           error=error,
                           creator=creator,
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
    contest = Contest.get_contest(contest_id)
    title = contest.title

    edit = False
    print(current_user.id, contest.creators)
    if current_user.id == str(contest.creators):
        edit = True

    rating = contest.get_rating()
    print(rating)
    rating = [User.get_user(i.get("user_id")) for i in rating]
    print(rating)
    rating = [[i.username, i.name, i.surname] for i in rating]
    print(rating)
    tasks = [Task.get_task(i) for i in list(map(int, contest.tasks.split(",")))]
    tasks = [[i.id, i.title] for i in tasks]
    print(tasks)

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('results.html',
                           type="Результаты",
                           title=title,
                           tasks=tasks,
                           create=creator,
                           people_info=rating,
                           contest_edit=edit,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Настройки"""
    form = forms.ChangeSettings()

    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.name.data = current_user.name
        form.surname.data = current_user.surname
        form.city .data = current_user.city

    if form.validate_on_submit():
        new_username = form.username.data
        new_email = form.email.data
        new_password = form.password.data
        new_name = form.name.data
        new_surname = form.surname.data
        new_city = form.city.data

        User.get_user(current_user.id).change_data(username=new_username if new_username != current_user.username else None,
                                                   email=new_email if new_email != current_user.email else None,
                                                   name=new_name if new_name != current_user.name else None,
                                                   surname=new_surname if new_surname != current_user.surname else None,
                                                   city=new_city if new_city != current_user.city else None,
                                                   password=new_password if new_password != current_user.password else None)

        print(new_username, new_email, new_name, new_surname, new_city, new_password)
        print(User.get_user(current_user.id).change_data(new_username, new_email, new_name, new_surname, new_city, new_password))

    creator = User.get_user(current_user.id).creator
    print(creator)
    return render_template('settings.html',
                           type="Настройки",
                           creator=creator,
                           form=form,
                           current_id=current_user.id)


@app.route('/email_verification', methods=['GET'])
def email_verification():
    action_type = request.args.get('action_type')
    email = request.args.get('email')
    verification_key = request.args.get('verification_key')
    user = None
    if action_type == 'submit':
        user = User.check_verification_key(email, verification_key)
    elif action_type == 'remove':
        User.delete_by_verification(email, verification_key)
    if user is not None:
        login_user(user, remember=True)
        return redirect('/contests')
    return redirect('/register')


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


app.run(host=environ.get('HOST', '0.0.0.0'), port=int(environ.get("PORT", 5000)))
