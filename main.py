from json import load

from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from models import User, Contest, Task
from db_session import global_init

import time
import datetime

global_init('database.db')
app = Flask(__name__)
with open('config.json', 'r') as file:
    app.config['SECRET_KEY'] = load(file)['APP_KEY']
login_manager = LoginManager(app)


@app.route('/')

@app.route('/intro')
def intro():
    """Титульная страница сайта"""
    return render_template('introduction.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация"""

    form = forms.RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        name = form.name.data
        surname = form.surname.data
        city = form.city.data
        remember = form.remember_me.data
        new_user = User.add_user(username=username,
                                password=password,
                                email=email,
                                name=name,
                                surname=surname,
                                city=city)

        if new_user.get("status") == "ok":
            user = User.get_user(new_user.get('id'))
            login_user(user, remember=remember)
            return redirect('/contests')

    return render_template('register.html',
                           form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""

    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        user = User.authorize_user(username, password)
        login_user(user, remember=remember)
        return redirect('/contests')

    return render_template('login.html',
                           form=form)


@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    """Профиль"""
    user = User.get_user(user_id)
    permission = False
    return render_template('profile.html',
                           type="Профиль",
                           create=permission,
                           name=user.name,
                           surename=user.surname,
                           city=user.city,
                           mail=user.email,
                           current_id=current_user.id)


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people():
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
def archive():
    """Архив задач"""
    tasks = []
    tasks_info = []
    form = forms.TaskSearch()
    if form.validate_on_submit():
        title = form.title.data
        tasks_info = Task.get_tasks_by_title(title)

    for i in tasks_info:
        tasks.append([i.id, i.title, i.description])
    print(tasks)
    permission = True
    return render_template('archive.html',
                           type="Архив",
                           create=permission,
                           tasks=tasks,
                           form=form,
                           current_id=current_user.id)


@app.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    form = forms.CreateTask()
    if form.validate_on_submit():
        creator = current_user.id
        title = form.title.data
        description = form.description.data
        reference = form.reference.data
        time_limit = form.time_limit.data
        # tests = form.tests.data
        print(creator, time_limit, title, description, reference)
        Task.add_task(creator, time_limit, title, description, reference)

        return redirect('/archive')

    permission = True
    return render_template('create_task.html',
                           type="Создать задачу",
                           create=permission,
                           form=form,
                           current_id=current_user.id)

@app.route('/system')
@login_required
def system():
    """О системе"""
    permission = False
    return render_template('system.html',
                           type="О системе",
                           create=permission,
                           current_id=current_user.id)



@app.route('/contests', methods=['GET', 'POST'])
@login_required
def contests():
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
                         datetime.datetime.fromtimestamp(i.end_time).strftime('%Y-%m-%d %H:%M:%S'),])


    permission = True
    return render_template('contests.html',
                           type="Контесты",
                           create=permission,
                           name=current_user.username,
                           contests=contests,
                           form=form,
                           current_id=current_user.id)


@app.route('/contest/<int:contest_id>')
@login_required
def contest(contest_id):
    """Турнир"""


    contest = Contest.get_contest(contest_id)
    print(contest)
    tasks = contest.get_tasks()
    results = []
    for i in tasks:
        results.append([i.id, i.title])
    print(results)

    permission = False
    return render_template('contest.html',
                           type="Контест",
                           create=permission,
                           tasks=results,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/create_contest', methods=['GET', 'POST'])
@login_required
def create_contest():

    form = forms.CreateContest()
    if form.validate_on_submit():
        creators = tuple(form.creators.data.split(','))
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

        print(creators, title, description, tasks, start, end)

        Contest.add_contest(creators, title, description, tasks, start, end)

    permission = True
    return render_template('create_contest.html',
                           type="Создать контест",
                           create=permission,
                           form=form,
                           current_id=current_user.id)


@app.route('/results/<int:contest_id>')
@login_required
def results(contest_id):
    """Результаты"""
    permission = False
    return render_template('results.html',
                           type="Результаты",
                           create=permission,
                           current_id=current_user.id,
                           contest_id=contest_id)


@app.route('/task/<int:task_id>')
@login_required
def task(task_id):
    """Задача"""
    task = Task.get_task(task_id)
    title = task.title
    description = task.description
    input_data = task.get_tests()
    output_data = task.get_tests()

    permission = False
    return render_template('task.html',
                           type="Задача",
                           create=permission,
                           title=title,
                           question=description,
                           input_data=input_data,
                           output_data=output_data,
                           current_id=current_user.id)


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

    permission = False
    return render_template('settings.html',
                           type="Настройки",
                           create=permission,
                           form=form,
                           current_id=current_user.id)


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

app.run()
