from json import load

from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from models import User
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
def profile(user_id):
    """Профиль"""
    user = User.get_user(user_id)
    print(user.name)
    print(user.surname)
    print(user.city)

    return render_template('profile.html',
                           type="Профиль",
                           name=user.name,
                           surename=user.surname,

                           city=user.city)


@app.route('/archive')
def archive():
    """Архив задач"""
    tasks = []
    return render_template('archive.html',
                           type="Архив",
                           tasks=tasks)


@app.route('/system')
def system():
    """О системе"""
    return render_template('system.html',
                           type="О системе")


@app.route('/contests')
@login_required
def cabinet_page():
    """Турниры"""
    """это нужно заменить на sql разумеется"""
    tournaments = []

    return render_template('contests.html',
                           type="Контесты",
                           name=current_user.username,
                           tournaments=tournaments)


@app.route('/tournament')
def tournament():
    """Турнир"""
    tournaments = []

    return render_template('tournament.html',
                           type="Турнир")


@app.route('/results')
def results():
    """Результаты"""

    return render_template('results.html',
                           type="Результаты")


@app.route('/task')
def task():
    """Задание"""
    name = ""
    question = ""

    return render_template('task.html',
                           type="Задача",
                           name=name,
                           question=question)


@app.route('/settings')
def settings():
    """Настройки"""

    return render_template('settings.html',
                           type="Настройки")


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)

app.run()
