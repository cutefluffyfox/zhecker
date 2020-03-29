import json

from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_required, login_user, current_user

import forms
from database import User, CreateDatabase

CreateDatabase()
app = Flask(__name__)
with open('config.json', 'r') as file:
    app.config['SECRET_KEY'] = json.load(file)['APP_KEY']
login_manager = LoginManager(app)


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
        return redirect('/main')
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
        return redirect('/main')
    return render_template('login.html', form=form)


@app.route('/main')
@login_required
def main_page():
    return 'Hi ' + current_user.username


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


app.run()
