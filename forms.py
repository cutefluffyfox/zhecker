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
    submit = SubmitField('Готово')


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
    description = TextAreaField('Описание задачи', validators=[DataRequired()])
    reference = FileField('Файл с эталоном решения', validators=[DataRequired()])
    time_limit = FloatField('Оптимальное время прохождения тестов (секунды)', validators=[DataRequired()])
    tests = FileField('Файл с тестами', validators=[DataRequired()])
    submit = SubmitField('Готово')


class EditTask(FlaskForm):
    title = StringField('Назавание задачи')
    description = TextAreaField('Описание задачи')
    reference = FileField('Файл с эталоном решения')
    time_limit = FloatField('Оптимальное время прохождения тестов (секунды)')
    tests = FileField('Файл с тестами')
    submit = SubmitField('Готово')


class SubmitTask(FlaskForm):
    file = FileField("Загрузить файл", validators=[DataRequired()])
    code = TextAreaField("Ваш код", validators=[DataRequired()])
    submit = SubmitField('Готово')


class CreateContest(FlaskForm):
    creators = StringField('Создатели  (id через запятую)', validators=[DataRequired()])
    title = StringField('Назавание турнира', validators=[DataRequired()])
    description = TextAreaField('Описание турнира', validators=[DataRequired()])
    tasks = StringField('Задачи турнира (id через запятую)', validators=[DataRequired()])
    start_date = StringField('Начало', validators=[DataRequired()])
    start_time = StringField('Начало', validators=[DataRequired()])
    end_date = StringField('Конец', validators=[DataRequired()])
    end_time = StringField('Конец', validators=[DataRequired()])
    submit = SubmitField('Готово')


class ChangeSettings(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль')
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Электронная почта', validators=[DataRequired()])
    city = StringField('Город', validators=[DataRequired()])
    submit = SubmitField('Готово')


class CheckTask(FlaskForm):
    code_file = FileField('Файл с решением')
    written_code = TextAreaField('Решение')
    submit = SubmitField('Готово')


class Application(FlaskForm):
    reason = TextAreaField('Обоснование запроса', validators=[DataRequired()])
    submit = SubmitField('Подать заявку')
