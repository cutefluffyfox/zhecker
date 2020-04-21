from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, FloatField, TextAreaField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Электронная почта', validators=[DataRequired()])
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
    title = StringField('Назавание турнира', validators=[DataRequired()])
    submit = SubmitField('Искать')


class PeopleSearch(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    submit = SubmitField('Искать')


class CreateTask(FlaskForm):
    title = StringField('Назавание задачи', validators=[DataRequired()])
    description = StringField('Описание задачи', validators=[DataRequired()])
    reference = StringField('Файл с эталоном решения', validators=[DataRequired()])
    time_limit = FloatField('Оптимальное время прохождения тестов (секунды)', validators=[DataRequired()])
    # tests = StringField('Файл с тестами', validators=[DataRequired()])
    submit = SubmitField('Создать')


class SubmitTask(FlaskForm):
    file = FileField("Загрузить файл", validators=[DataRequired()])
    code = TextAreaField("Ваш код", validators=[DataRequired()])
    submit = SubmitField('Создать')


class CreateContest(FlaskForm):
    creators = StringField('Создатели  (id через запятую)', validators=[DataRequired()])
    title = StringField('Назавание турнира', validators=[DataRequired()])
    description = StringField('Описание турнира', validators=[DataRequired()])
    tasks = StringField('Задачи турнира (id через запятую)', validators=[DataRequired()])
    start_date = StringField('Начало', validators=[DataRequired()])
    start_time = StringField('Начало', validators=[DataRequired()])
    end_date = StringField('Конец', validators=[DataRequired()])
    end_time = StringField('Конец', validators=[DataRequired()])
    submit = SubmitField('Создать', validators=[DataRequired()])


class ChangeSettings(FlaskForm):
    username = StringField('Новый логин')
    email = StringField('Новая электронная почта')
    password = PasswordField('Новый пароль')
    name = StringField('Новое имя')
    surname = StringField('Новая фамилия')
    city = StringField('Новый город')
    submit = SubmitField('Изменить')
