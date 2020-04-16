from json import load

from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from models import User, Contest, Task
from db_session import global_init

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
        name = form.name.data
        surname = form.surname.data
        city = form.city.data
        remember = form.remember_me.data
        user_id = User.add_user(username=username,
                                password=password,
                                email='@ADD@',
                                name=name,
                                surname=surname,
                                city=city)
        user = User.get_user(user_id)
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
        user = User.get_user_by_username(username, password)
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


@app.route('/people')
@login_required
def preople():
    """Профиль"""

    permission = False
    return render_template('people.html',
                           type="Профиль"
)


@app.route('/archive', methods=['GET', 'POST'])
def archive():
    """Архив задач"""
    tasks = []
    tasks_info = []
    form = forms.TaskSearch()
    if form.validate_on_submit():
        title = form.title.data
        tasks_info = Task.get_task_by_title(title)

    for i in tasks_info:
        tasks.append([i.id, i.title, i.description])
    permission = True
    return render_template('archive.html',
                           type="Архив",
                           create=permission,
                           tasks=tasks,
                           form=form,
                           current_id=current_user.id)


@app.route('/create_task', methods=['GET', 'POST'])
def create_task():
    form = forms.CreateTask()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        reference = form.reference.data
        Task.add_task(current_user.id, title, description, reference)

        return redirect('/archive')

    permission = True
    return render_template('create_task.html',
                           type="Создать задачу",
                           create=permission,
                           form=form,
                           current_id=current_user.id)

@app.route('/system')
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
    form = forms.ContestSearch()
    if form.validate_on_submit():
        title = form.title.data
        contests = Task.get_contest_by_title(title)

    tournaments = []
    permission = True
    return render_template('contests.html',
                           type="Контесты",
                           create=permission,
                           name=current_user.username,
                           tournaments=tournaments,
                           form=form,
                           current_id=current_user.id)


@app.route('/contest/<int:contest_id>')
@login_required
def contest(contest_id):
    """Турнир"""
    tasks = []
    id = contest_id
    permission = False
    return render_template('contest.html',
                           type="Турнир",
                           create=permission,
                           tasks=tasks,
                           current_id=current_user.id)


@app.route('/create_contest', methods=['GET', 'POST'])
def create_contest():
    form = forms.CreateContest()
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        tasks = form.tasks.data

        return redirect('/archive')

    permission = True
    return render_template('create_contest.html',
                           type="Создать контест",
                           create=permission,
                           current_id=current_user.id)


@app.route('/results/<int:contest_id>')
@login_required
def results():
    """Результаты"""
    permission = False
    return render_template('results.html',
                           type="Результаты",
                           create=permission,
                           current_id=current_user.id)


@app.route('/task/<int:task_id>')
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


@app.route('/settings/<int:user_id>', methods=['GET', 'POST'])
@login_required
def settings(user_id):
    """Настройки"""

    permission = False
    return render_template('settings.html',
                           type="Настройки",
                           create=permission,
                           current_id=current_user.id)


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

app.run()
