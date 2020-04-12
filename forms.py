from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    city = StringField('Город')
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Регистрация')


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class TaskSearch(FlaskForm):
    title = StringField('Назавание задачи', validators=[DataRequired()])
    submit = SubmitField('Искать')


class ContestSearch(FlaskForm):
    title= StringField('Назавание турнира', validators=[DataRequired()])
    submit = SubmitField('Искать')


class CreateTask(FlaskForm):
    title = StringField('Назавание задачи', validators=[DataRequired()])
    description = StringField('Описание задачи', validators=[DataRequired()])
    """tasks"""
    start_time = StringField('Начало', validators=[DataRequired()])
    end_time = StringField('Конец', validators=[DataRequired()])
    submit = SubmitField('Создать')
    """Тесты как будут подавать сам сделай пж(файлами/не файлами...)"""


class CreateContest(FlaskForm):
    """не знаю, как записать запись добавление нескольктх задач"""
    title = StringField('Назавание турнира', validators=[DataRequired()])
    description = StringField('Назавание турнира')
    submit = SubmitField('Создать')

