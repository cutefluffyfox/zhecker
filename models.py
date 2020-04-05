import sqlalchemy
from db_session import SqlAlchemyBase, create_session
from flask_login import UserMixin
from random import randint
from hashlib import sha3_256
from json import load


class Test(SqlAlchemyBase):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"), nullable=False)
    input = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    output = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    points = sqlalchemy.Column(sqlalchemy.Integer, default=1)


class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    reference = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    attempts = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    successful = sqlalchemy.Column(sqlalchemy.Integer, default=0)


class Contest(SqlAlchemyBase):
    __tablename__ = 'contests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creators = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    tasks = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    start_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    end_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    creator = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    verification = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    contests = sqlalchemy.Column(sqlalchemy.String, default='')

    def __repr__(self):
        return f"{self.username}: {self.email}"

    @staticmethod
    def get_user(user_id: int):
        session = create_session()
        return session.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_username(username: str, password: str):
        session = create_session()
        return session.query(User).filter(User.username == username, User.password == User.__generate_password(password)).first()

    @staticmethod
    def __generate_password(password: str):
        return sha3_256((password + load(open('config.json', 'r', encoding='UTF-8'))['SALT']).encode('UTF-8')).hexdigest()

    @staticmethod
    def add_user(username: str, email: str, password: str, name: str, surname: str, city=None):
        session = create_session()
        session.add(User(username=username,
                         email=email,
                         password=User.__generate_password(password),
                         name=name,
                         surname=surname,
                         city=city,
                         verification="".join([chr(randint(65, 90)) if randint(0, 1) else chr(randint(97, 122)) for _ in range(30)])))
        session.commit()
        return session.query(User).filter(User.username == username).first().id


class Attempt(SqlAlchemyBase):
    __tablename__ = 'attempts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    contest_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("contests.id"), nullable=False)
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"), nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    solution = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    score = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    time = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

