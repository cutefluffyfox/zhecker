import json

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from database import User, CreateDatabase

CreateDatabase()
app = Flask(__name__)
with open('config.json', 'r') as file:
    app.config['SECRET_KEY'] = json.load(file)['APP_KEY']
login_manager = LoginManager(app)


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
        user_id = User.add_user(username, password, name, surname, city)
        user = User(user_id)
        login_user(user, remember=remember)
        return redirect('/cabinet')
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""

    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        user = User.get_user(username, password)
        login_user(user, remember=remember)
        return redirect('/cabinet')
    return render_template('login.html', form=form)


@app.route('/contests')
@login_required
def cabinet_page():
    """Личный кабинет"""
    """это нужно заменить на sql разумеется"""
    tournaments = []

    return render_template('contests_back.html', name=current_user.username, tournaments=tournaments)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    """Профиль"""
    user = User(user_id)
    print(user.name)
    print(user.surname)
    print(user.city)

    return render_template('profile_icon.html', name=user.name, surename=user.surname, city=user.city)


@app.route('/archive')
def archive():
    """Архив задач"""
    tasks = []
    return render_template('task_archive_back.html', tasks=tasks)


@app.route('/system')
def system():
    """О системе"""
    return render_template('system.html')

@app.route('/contests')
def contests():
    """О системе"""
    return render_template('contests_back.html')

@app.route('/test')
def tests():
    """О системе"""
    return render_template('bar.html')


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


app.run()
