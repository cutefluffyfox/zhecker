from json import load

from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from models import User, Contest
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
                           mail=user.email)


@app.route('/archive')
def archive():
    """Архив задач"""
    tasks = []
    permission = False
    return render_template('archive.html',
                           type="Архив",
                           create=permission,
                           tasks=tasks)


@app.route('/system')
def system():
    """О системе"""
    permission = False
    return render_template('system.html',
                           type="О системе",
                           create=permission,)


@app.route('/contests')
@login_required
def contests():
    """Турниры"""
    """это нужно заменить на sql разумеется"""
    tournaments = []
    permission = False
    return render_template('contests.html',
                           type="Контесты",
                           create=permission,
                           name=current_user.username,
                           tournaments=tournaments)


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
                           tasks=tasks)


@app.route('/results/<int:contest_id>')
@login_required
def results():
    """Результаты"""
    permission = False
    return render_template('results.html',
                           type="Результаты",
                           create=permission)


@app.route('/task/<int:task_id>')
def task(task_id):
    """Задание"""
    id = task_id
    name = "Мышь"
    question = "МЫШЬ МЫШ МЫШ"
    input_data = [1, 2]
    output_data = [3, 4]
    permission = False
    return render_template('task.html',
                           type="Задача",
                           create=permission,
                           name=name,
                           question=question,
                           input_data=input_data,
                           output_data=output_data,
                           id=id)


@app.route('/settings/<int:user_id>')
@login_required
def settings():
    """Настройки"""
    permission = False
    return render_template('settings.html',
                           type="Настройки",
                           create=permission)


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

app.run()
