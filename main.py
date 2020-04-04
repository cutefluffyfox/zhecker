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
    """base of /intro page"""
    return render_template('introduction.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ base of /register page """

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
    """ base of /login page """

    form = forms.LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        user = User.get_user(username, password)
        login_user(user, remember=remember)
        return redirect('/cabinet')
    return render_template('login.html', form=form)


@app.route('/cabinet')
@login_required
def cabinet_page():
    """это нужно заменить на sql разумеется"""
    tournaments = []

    return render_template('cabinet_back.html', name=current_user.username, tournaments=tournaments)


@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = User(user_id)
    print(user.name)
    print(user.surname)
    print(user.city)

    return render_template('profile.html', name=user.name, surename=user.surname, city=user.city)

@app.route('/archive')
def archive():
    return render_template('task_archive_back.html')


@app.route('/documentation')
def documentation():
    return render_template('documentation.html')


@app.route('/system')
def system():
    return render_template('system.html')


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


app.run()
