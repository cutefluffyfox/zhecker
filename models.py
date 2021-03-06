import sqlalchemy
from db_session import SqlAlchemyBase, create_session
from flask_login import UserMixin
from random import choice
from hashlib import sha3_256
from time import time
from test_system import Checker
from email_sender import send_email
from os import environ
import threading


def __init__():
    session = create_session()
    if Contest.get_contest(contest_id=0) is None:
        session.add(Contest(id=0, creators='', title='Tasks', description='Contest with all tasks', start_time=0, end_time=pow(2, 34), tasks=''))
        session.commit()


def _like(text: str) -> str:
    return '%' + text + '%'


class Test(SqlAlchemyBase):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"), nullable=False)
    input = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    output = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    points = sqlalchemy.Column(sqlalchemy.Integer, default=1)

    def change_data(self, inp=None, points=None):
        """
        Change input/output/points, return
        {'status': 'ok'}
        {'status': 'invalid <input/points> type, expected <str/int> or None'}
        {'status': 'same test has already been added'}
        {'status': 'invalid input for the reference, code gives error <error>'}
        """
        try:
            session = create_session()
            assert inp is None or type(inp) == str, 'invalid input type, expected str'
            assert points is None or type(points) == int, 'invalid input type, expected int'
            assert len(session.query(Test).filter(Test.task_id == self.task_id, Test.input == (self.input if inp is None else inp)).all()) == 0, 'same test has already been added'
            test = session.query(Test).filter(Test.id == self.id).first()
            if inp is not None:
                output = Checker.get_output(self.task_id, inp)
                assert output[0] == 'OK', f'invalid input for the reference, code gives error {output[0]}'
                self.output = test.output = output[1]
                self.input = test.input = inp
            if points is not None:
                self.points = test.points = points
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def delete_test(self):
        """Delete test from database"""
        session = create_session()
        session.delete(session.query(Test).filter(Test.id == self.id).first())
        session.commit()

    @staticmethod
    def get_test(test_id: int):
        """Return Test(**kwargs) by test_id or None if id is invalid"""
        session = create_session()
        return session.query(Test).filter(Test.id == test_id).first()

    @staticmethod
    def add_test(task_id: int, inp: str, points=None) -> dict:
        """
        Add test to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <input/points> type, expected <str/int>'}
        {'status': 'no task with id '<task_id>''}
        {'status': 'same test has already been added'}
        {'status': 'invalid input for the reference, code gives error <error>'}
        """
        try:
            session = create_session()
            assert len(session.query(Task).filter(Task.id == task_id).all()) == 1, f'no task with id \'{task_id}\''
            assert type(inp) == str, 'invalid input type, expected str'
            assert points is None or type(points) == int, 'invalid points type, expected int'
            assert len(session.query(Test).filter(Test.task_id == task_id, Test.input == inp).all()) == 0, 'same test has already been added'
            output = Checker.get_output(task_id, inp)
            assert output[0] == 'OK', f'invalid input for the reference, code gives error {output[0]}'
            session.add(Test(task_id=task_id,
                             input=inp,
                             output=output[1],
                             points=points))
            session.commit()
            return {'status': 'ok', 'id': session.query(Test).filter(Test.task_id == task_id, Test.input == inp).first().id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Test(input='{self.input}', output='{self.output}')"


class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    time_limit = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    reference = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    attempts = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    successful = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    def change_data(self, time_limit=None, title=None, description=None, reference=None):
        """
        Change title/description/reference/time_limit, return
        {'status': 'ok'}
        {'status': 'same task has already been added'}
        {'status': 'invalid <title/description/reference/time_limit> type, expected <str/int/float> or None'}
        """
        try:
            session = create_session()
            assert time_limit is None or type(time_limit) == int or type(time_limit) == float, 'invalid time_limit type, expected float or int or None'
            assert title is None or type(title) == str, 'invalid title type, expected str or None'
            assert description is None or type(description) == str, 'invalid description type, expected str or None'
            assert reference is None or type(reference) == str, 'invalid reference type, expected str or None'
            assert len(session.query(Task).filter(Task.creator == self.creator, Task.time_limit == (self.time_limit if time_limit is None else time_limit), Task.title == (self.title if title is None else title), Task.description == (self.description if description is None else description), Task.reference == (self.reference if reference is None else reference)).all()) == 0, "same task has already been added"
            task = session.query(Task).filter(Task.id == self.id).first()
            if time_limit is not None:
                self.time_limit = task.time_limit = time_limit
            if title is not None:
                self.title = task.title = title
            if description is not None:
                self.description = task.description = description
            if reference is not None:
                status, attempt_id = Attempt.add_attempt(contest_id=0, solution=reference, task_id=self.id, user_id=self.creator)
                assert status == 'OK', f'reference failed on tests, got error {status}'
                self.reference = task.reference = reference
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def get_tests(self):
        """Return [Test(**kwargs), ...] sorted by index (recent added at the back)"""
        session = create_session()
        return session.query(Test).filter(Test.task_id == self.id).order_by(sqlalchemy.desc(~Test.id)).all()

    def add_test(self, inp: str, points=None):
        """Add test to database by using Test.add_test(**kwargs)"""
        return Test.add_test(task_id=self.id, inp=inp, points=points)

    def add_attempt(self, successful=False):
        """Add attempt and successful to database"""
        session = create_session()
        task = session.query(Task).filter(Task.id == self.id).first()
        self.attempts = task.attempts = task.attempts + 1
        self.successful = task.successful = task.successful + successful
        session.commit()

    def delete_attempt(self):
        """Delete attempt from database"""
        session = create_session()
        session.delete(session.query(Attempt).filter(Attempt.id == self.id).first())
        session.commit()

    @staticmethod
    def get_all(sort_type='easy'):
        """Return [Task(**kwargs), ...] sorted by sort_type (see models.py -> class Task() -> method get_all())"""
        sort = {
            'new': Task.id,
            'old': ~Task.id,
            'easy': Task.successful / Task.attempts,
            'hard': ~(Task.successful / Task.attempts),
            'popular': Task.attempts,
            'not_popular': ~Task.attempts,
            'most_success': Task.successful,
            'least_success': ~Task.successful,
        }
        session = create_session()
        return session.query(Task).order_by(sqlalchemy.desc(sort.get(sort_type, sort['easy']))).all()

    @staticmethod
    def get_task(task_id: int):
        """Return Task(**kwargs) by task_id or None if id is invalid"""
        session = create_session()
        return session.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks_by_title(title: str):
        """Return [Task(**kwargs), ...] by title where Task.title like title"""
        session = create_session()
        return session.query(Task).filter(Task.title.like(_like(title))).all()

    @staticmethod
    def add_task(creator: int, time_limit: float, title: str, description: str, reference: str, tests=None) -> dict:
        """
        Add task to database, return:
        {'status': 'ok', 'id': int, 'tests_statuses': list}
        {'status': 'invalid <time_limit/title/description/reference/tests> type, expected <str/int/float/list/tuple/None>'}
        {'status': 'no user with id '<creator>''}
        {'status': 'same task has already been added'}
        """
        try:
            session = create_session()
            assert User.get_user(creator) is not None, f"no user with id '{creator}'"
            assert type(time_limit) == int or type(time_limit) == float, 'invalid time_limit type, expected int or float'
            assert type(title) == str, 'invalid title type, expected str'
            assert type(description) == str, 'invalid description type, expected str'
            assert type(reference) == str, 'invalid reference type, expected str'
            assert tests is None or type(tests) == list or type(tests) == tuple, 'invalid tests type, expected list, tuple or None'
            assert tests is None or all(map(lambda a: type(a) == dict, tests)), 'invalid tests[index] type, expected dict'
            assert len(session.query(Task).filter(Task.creator == creator, Task.time_limit == time_limit, Task.title == title, Task.description == description, Task.reference == reference).all()) == 0, "same task has already been added"
            session.add(Task(creator=creator,
                             time_limit=time_limit,
                             title=title,
                             description=description,
                             reference=reference))
            session.commit()
            task_id = session.query(Task).filter(Task.creator == creator, Task.time_limit == time_limit, Task.title == title, Task.description == description, Task.reference == reference).first().id
            tests_statuses = []
            for test in (tests if tests is not None else []):
                tests_statuses.append(Test.add_test(task_id=task_id, inp=str(test.get('input')), points=test.get('points')))
            return {'status': 'ok', 'id': task_id, 'tests_statuses': tests_statuses}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Task(title='{self.title}', attempts={self.attempts})"


class Contest(SqlAlchemyBase):
    __tablename__ = 'contests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creators = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    tasks = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    start_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    end_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)

    def change_data(self, creators=None, title=None, description=None, tasks=None, start_time=None, end_time=None):
        """
        Change title/description/reference, return
        {'status': 'ok'}
        {'status': 'same task has already been added'}
        {'status': 'no <user/task> with id '{id}''}
        {'status': 'invalid <creators/tasks/title/description/start_time/end_time> type, expected <str/int/tuple/list> or None'}
        """
        try:
            session = create_session()
            assert type(creators) == tuple or type(creators) == list or creators is None, 'invalid creators type, expected list or tuple or None'
            assert type(tasks) == tuple or type(tasks) == list or tasks is None, 'invalid tasks type, expected list or tuple or None'
            assert type(title) == str or title is None, 'invalid title type, expected str or None'
            assert type(description) == str or description is None, 'invalid description type, expected str or None'
            assert type(start_time) == int or start_time is None, 'invalid start_time type, expected int or None'
            assert type(end_time) == int or end_time is None, 'invalid end_time type, expected int or None'
            for creator in ([] if creators is None else creators):
                assert User.get_user(creator) is not None, f"no user with id '{creator}'"
            for task in ([] if tasks is None else tasks):
                assert Task.get_task(task) is not None, f"no task with id '{task}'"
            assert len(session.query(Contest).filter(Contest.creators == (self.creators if creators is None else ','.join(creators)), Contest.title == (self.title if title is None else title), Contest.description == (self.description if description is None else description), Contest.tasks == (self.tasks if tasks is None else ','.join(tasks)), Contest.start_time == (self.start_time if start_time is None else start_time), Contest.end_time == (self.end_time if end_time is None else end_time)).all()) == 0, 'same contest has already been added'
            contest = session.query(Contest).filter(Contest.id == self.id).first()
            if creators is not None:
                self.creators = contest.creators = ','.join(creators)
            if title is not None:
                self.title = contest.title = title
            if description is not None:
                self.description = contest.description = description
            if tasks is not None:
                self.tasks = contest.tasks = ','.join(tasks)
            if start_time is not None:
                self.start_time = contest.start_time = start_time
            if end_time is not None:
                self.end_time = contest.end_time = end_time
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def get_user_results(self, user_id: int):
        """Return [Task(**kwargs), Attempt(**kwargs)] by user_id for """
        return [(task, Attempt.get_best_result(contest_id=self.id, task_id=task.id, user_id=user_id)) for task in self.get_tasks()]

    def get_tasks(self):
        """Return [Task(**kwargs), ...]"""
        return [Task.get_task(task_id) for task_id in map(int, self.tasks.split(','))] if self.tasks else []

    def get_creators(self):
        """Return [User(**kwargs), ...]"""
        return [User.get_user(user_id) for user_id in map(int, self.creators.split(','))]

    def get_rating(self):
        """Return [{'task_id': int, 'user_id': int, 'score': int, 'attempt': int}, ...] for each Attempt send in time"""
        session = create_session()
        return sorted([(User.get_user(user[0]), [Attempt.get_best_result(self.id, task.id, user[0]) for task in self.get_tasks()], Attempt.get_tasks_sum(self.id, user[0])) for user in session.query(Attempt.user_id).filter(Attempt.contest_id == self.id, Attempt.time >= self.start_time, Attempt.time <= self.end_time).distinct()], key=lambda a: a[2], reverse=True)

    def delete_contest(self):
        """Delete contest from database"""
        session = create_session()
        session.delete(session.query(Contest).filter(Contest.id == self.id).first())
        session.commit()

    @staticmethod
    def get_all(sort_type='new'):
        """Return [Contest(**kwargs), ...] sorted by sort_type (see models.py -> class Contest() -> method get_all())"""
        sort = {
            'new': Contest.start_time,
            'old': ~Contest.start_time,
        }
        session = create_session()
        return session.query(Contest).order_by(sqlalchemy.desc(sort.get(sort_type, sort['new']))).all()

    @staticmethod
    def get_contest(contest_id: int):
        """Return Contest(**kwargs) by contest_id or None if id is invalid"""
        session = create_session()
        return session.query(Contest).filter(Contest.id == contest_id).first()

    @staticmethod
    def get_contest_by_title(title: str):
        """Return [Contest(**kwargs), ...] by title where Contest.title like title"""
        session = create_session()
        return session.query(Contest).filter(Contest.title.like(_like(title))).all()

    @staticmethod
    def add_contest(creators: tuple, title: str, description: str, tasks: tuple, start_time: int, end_time: int) -> dict:
        """
        Add contest to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <creators/title/descriptions/tasks/start_time/end_time> type, expected <str/int/list/tuple>'}
        {'status': 'no <user/task> with id '<id>''}
        {'status': 'same contest has already been added'}
        """
        try:
            session = create_session()
            assert type(creators) == tuple or type(creators) == list, 'invalid creators type, expected list or tuple'
            assert type(tasks) == tuple or type(tasks) == list, 'invalid tasks type, expected list or tuple'
            assert type(title) == str, 'invalid title type, expected str'
            assert type(description) == str, 'invalid description type, expected str'
            assert type(start_time) == int, 'invalid start_time type, expected int'
            assert type(end_time) == int, 'invalid end_time type, expected int'
            for creator in creators:
                assert User.get_user(creator) is not None, f"no user with id '{creator}'"
            for task in tasks:
                assert Task.get_task(task) is not None, f"no task with id '{task}'"
            assert len(session.query(Contest).filter(Contest.creators == ','.join(creators), Contest.title == title, Contest.description == description, Contest.tasks == ','.join(tasks), Contest.start_time == start_time, Contest.end_time == end_time).all()) == 0, 'same contest has already been added'
            session.add(Contest(creators=','.join(creators),
                                title=title,
                                description=description,
                                tasks=','.join(tasks),
                                start_time=start_time,
                                end_time=end_time))
            session.commit()
            return {'status': 'ok', 'id': session.query(Contest).filter(Contest.creators == ','.join(creators), Contest.title == title, Contest.description == description, Contest.tasks == ','.join(tasks), Contest.start_time == start_time, Contest.end_time == end_time).first().id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Contest(title='{self.title}', tasks='{self.tasks}')"


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    register_date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    creator = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    verification = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    registered = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    api_key = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)

    def change_data(self, username=None, email=None, name=None, surname=None, city=None, password=None, api=None) -> dict:
        """
        Change username/email/name/surname/city/password, return
        {'status': 'ok'}
        {'status': '<username/email> is already taken'}
        {'status': 'invalid <username/email/name/surname/city/password> type, expected str or None'}
        """
        try:
            session = create_session()
            assert username is None or type(username) == str and username, 'invalid username type, expected str or None'
            assert email is None or type(email) == str and email, 'invalid email type, expected str or None'
            assert name is None or type(name) == str and name, 'invalid name type, expected str or None'
            assert surname is None or type(surname) == str and surname, 'invalid surname type, expected str or None'
            assert city is None or type(city) == str and city, 'invalid city type, expected str or None'
            assert password is None or type(password) == str and password, 'invalid password type, expected str or None'
            assert type(api) == bool or api is None, 'invalid api type, expected bool or None'
            assert len(session.query(User).filter(User.username == username).all()) == 0 or username is None, 'username is already taken'
            assert len(session.query(User).filter(User.email == email).all()) == 0 or email is None, 'email is already taken'
            user = session.query(User).filter(User.id == self.id).first()
            if username is not None:
                user.username = self.username = username
            if email is not None:
                user.email = self.email = email
            if name is not None:
                user.name = self.name = name
            if surname is not None:
                user.surname = self.surname = surname
            if city is not None:
                user.city = self.city = city
            if password is not None:
                user.password = self.password = self.__generate_password(password)
            if api is not None:
                if api:
                    user.generate_api()
                else:
                    user.remove_api()
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def remove_api(self):
        """Removes api_key"""
        session = create_session()
        user = session.query(User).filter(User.id == self.id).first()
        if user.api_key is not None:
            user.api_key = self.api_key = None
        session.commit()

    def generate_api(self):
        """Return api_key, generate if api_key is None"""
        session = create_session()
        user = session.query(User).filter(User.id == self.id).first()
        if user.api_key is None:
            api_key = self.__generate_random()
            while session.query(User).filter(User.api_key == api_key).all():
                api_key = self.__generate_random()
            user.api_key = self.api_key = api_key
        session.commit()
        return user.api_key

    def send_creator_email(self, message: str):
        """Send email to become creator"""
        session = create_session()
        user = session.query(User).filter(User.id == self.id).first()
        user.verification = self.verification = self.__generate_random(50)
        session.commit()
        send_email(environ['MAIL_LOGIN_GOOGLE'], content_type='get_creator', message=message, user_id=self.id, confirmation_key=self.verification)

    @staticmethod
    def __generate_random(length=150):
        return ''.join([choice('1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM') for _ in range(length)])

    def delete_user(self):
        """Delete user from database"""
        session = create_session()
        session.delete(session.query(User).filter(User.id == self.id).first())
        session.commit()

    @staticmethod
    def email_verification(email: str, verification_key: str, action: str):
        """Delete user by email and verification_key"""
        session = create_session()
        user = session.query(User).filter(User.email == email, User.verification == verification_key).first()
        user_id = user.id
        if (action == 'remove' and user is not None and user.verification is not None) or (action == 'submit' and user is not None and user.verification is not None and int(time()) - user.register_date > 60 * 60):
            user.delete_user()
        elif action == 'submit' and user is not None and user.verification is not None and int(time()) - user.register_date <= 60 * 60:
            user.registered = True
            user.verification = None
        session.commit()
        return session.query(User).filter(User.id == user_id, User.registered == True).first()

    @staticmethod
    def creator_confirmation(user_id: int, confirmation_key: str, action: str):
        """Return User(**kwargs) by email and verification_key or None if email/verification_key invalid or timed out"""
        session = create_session()
        user = session.query(User).filter(User.id == user_id, User.verification == confirmation_key).first()
        if action == 'submit' and user is not None and user.verification is not None:
            send_email(user.email, content_type='creator_confirmed', name=user.name, surname=user.surname)
            user.verification = None
            user.creator = True
        elif action == 'deny' and user is not None and user.verification is not None:
            send_email(user.email, content_type='creator_denied', name=user.name, surname=user.surname)
            user.verification = None
        session.commit()

    @staticmethod
    def get_users_by_username(username: str):
        """Return [User(**kwargs), ...] by username where User.username like username"""
        session = create_session()
        return session.query(User).filter(User.username.like(_like(username))).all()

    @staticmethod
    def get_user(user_id: int):
        """Return User(**kwargs) by user_id or None if id is invalid"""
        session = create_session()
        return session.query(User).filter(User.id == user_id, User.registered == True).first()

    @staticmethod
    def get_api(api_key: str):
        """Return user by api_key"""
        session = create_session()
        return session.query(User).filter(User.api_key == api_key, User.registered == True).first()

    @staticmethod
    def authorize_user(username: str, password: str):
        """Return User(**kwargs) by username and not hashed password or None if username or password is invalid"""
        session = create_session()
        return session.query(User).filter(User.username == username, User.password == User.__generate_password(password)).first()

    @staticmethod
    def __generate_password(password: str) -> str:
        """Return hashed password by password"""
        return sha3_256((password + environ['SALT']).encode('UTF-8')).hexdigest()

    @staticmethod
    def add_user(username: str, email: str, password: str, name: str, surname: str, city=None) -> dict:
        """
        Add user to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <password/name/surname/city> type, expected <str/None>'}
        {'status': '<username/email> is already taken'}
        {'status': 'email not send'}
        """
        try:
            session = create_session()
            assert type(password) == str, 'invalid password type, expected str'
            assert type(name) == str, 'invalid name type, expected str'
            assert type(surname) == str, 'invalid surname type, expected str'
            assert city is None or type(city) == str, 'invalid city type, expected str or None'
            assert len(session.query(User).filter(User.username == username).all()) == 0, 'username is already taken'
            assert len(session.query(User).filter(User.email == email).all()) == 0, 'email is already taken'
            verification_key = User.__generate_random(50)
            assert send_email(email, content_type='verification', verification_key=verification_key, email=email), 'email not send'
            session.add(User(username=username,
                             email=email,
                             password=User.__generate_password(password),
                             name=name,
                             surname=surname,
                             city=city,
                             register_date=int(time()),
                             verification=verification_key))
            session.commit()
            user = session.query(User).filter(User.username == username).first()
            return {'status': 'ok', 'id': user.id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"User(username='{self.username}', email='{self.email}')"


class Attempt(SqlAlchemyBase):
    __tablename__ = 'attempts'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    contest_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("contests.id"), nullable=False)
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"), nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    solution = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    time = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    score = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def change_data(self, score=None, status=None):
        """
        Change score/status, return
        {'status': 'ok'}
        {'status': 'invalid <score/status> type, expected <str/int> or None'}
        """
        try:
            session = create_session()
            assert score is None or type(score) == int, 'invalid score type, expected int or None'
            assert status is None or type(status) == str, 'invalid status type, expected str or None'
            attempt = session.query(Attempt).filter(Attempt.id == self.id).first()
            if score is not None:
                self.score = attempt.score = score
            if status is not None:
                self.status = attempt.status = status
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def retry(self):
        """Retry attempt and change values if something changed"""
        thread = threading.Thread(target=Checker.check_attempt, args=(self.id,))
        thread.start()

    def get_tests_statuses(self):
        """Return [Trial(**kwargs) by attempt_id]"""
        session = create_session()
        return session.query(Trial).filter(Trial.attempt_id == self.id).all()

    @staticmethod
    def get_attempt(attempt_id: int):
        """Return Attempt(**kwargs) by attempt_id or None if id is invalid"""
        session = create_session()
        return session.query(Attempt).filter(Attempt.id == attempt_id).first()

    @staticmethod
    def get_attempts(contest_id: int, task_id: int, user_id: int):
        """Return [Attempt(**kwargs), ...] by contest_id, task_id, user_id"""
        session = create_session()
        return session.query(Attempt).filter(Attempt.contest_id == contest_id, Attempt.task_id == task_id, Attempt.user_id == user_id).all()

    @staticmethod
    def get_tasks_sum(contest_id, user_id: int):
        return sum([(lambda a: a.score if a is not None else 0)(Attempt.get_best_result(contest_id, task.id, user_id)) for task in Contest.get_contest(contest_id).get_tasks()])

    @staticmethod
    def get_last_result(contest_id: int, task_id: int, user_id: int):
        """Return new Attempt(**kwargs) by contest_id, task_id, user_id ot None if there is no attempts"""
        session = create_session()
        return session.query(Attempt, sqlalchemy.func.max(Attempt.time)).filter(Attempt.contest_id == contest_id, Attempt.task_id == task_id, Attempt.user_id == user_id).first()[0]

    @staticmethod
    def get_best_result(contest_id: int, task_id: int, user_id: int):
        """Return Attempt(**kwargs) with the biggest score"""
        session = create_session()
        return session.query(Attempt, sqlalchemy.func.max(Attempt.score)).filter(Attempt.contest_id == contest_id, Attempt.task_id == task_id, Attempt.user_id == user_id).first()[0]

    @staticmethod
    def add_attempt(contest_id: int, task_id: int, user_id: int, solution: str):
        """
        Add attempt to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <contest_id/task_id/user_id/solution> type, expected <str/int>'}
        {'status': 'no <contest/task/user> with id '<id>''}
        {'status': 'the same solution has already been sent'}
        """
        try:
            session = create_session()
            assert type(contest_id) == int, 'invalid contest_id type, expected int'
            assert type(task_id) == int, 'invalid task_id type, expected int'
            assert type(user_id) == int, 'invalid user_id type, expected int'
            assert type(solution) == str, 'invalid solution type, expected str'
            assert Contest.get_contest(contest_id) is not None, f"no contest with id '{contest_id}'"
            assert Task.get_task(task_id) is not None, f"no task with id '{task_id}'"
            assert User.get_user(user_id) is not None, f"no user with id '{user_id}'"
            assert len(session.query(Attempt).filter(Attempt.contest_id == contest_id, Attempt.task_id == task_id, Attempt.user_id == user_id, Attempt.solution == solution).all()) == 0, 'the same solution has already been sent'
            session.add(Attempt(contest_id=contest_id,
                                task_id=task_id,
                                user_id=user_id,
                                solution=solution,
                                status='?',
                                time=int(time())))
            session.commit()
            attempt_id = session.query(Attempt).filter(Attempt.contest_id == contest_id, Attempt.task_id == task_id, Attempt.user_id == user_id, Attempt.solution == solution).first().id
            thread = threading.Thread(target=Checker.check_attempt, args=(attempt_id,))
            thread.start()
            return {'status': 'ok', 'id': attempt_id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Attempt(score={self.score}, status='{self.status}')"


class Trial(SqlAlchemyBase):
    __tablename__ = 'trial'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    attempt_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("attempts.id"), nullable=False)
    test_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tests.id"), nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    output = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    @staticmethod
    def get_attempt_trials(attempt_id: int):
        """Return [Trial(**kwargs), ...] by attempt id"""
        session = create_session()
        return session.query(Trial).filter(Trial.attempt_id == attempt_id).all()

    @staticmethod
    def get_trial(trial_id: int):
        """Return Trial(**kwargs) by trial_id or None if id is invalid"""
        session = create_session()
        return session.query(Trial).filter(Trial.id == trial_id).first()

    @staticmethod
    def add_trial(attempt_id: int, test_id: int, status: str, output=None):
        """
        Add attempt_id, test_id, status, output to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <attempt_id/tesk_id/status/output> type, expected <str/int/None>'}
        {'status': 'no <attempt/test> with id '<id>''}
        {'status': 'same trial has already been added'}
        """
        try:
            session = create_session()
            assert type(attempt_id) == int, 'invalid attempt_id type, expected int'
            assert type(test_id) == int, 'invalid test_id type, expected int'
            assert type(status) == str, 'invalid status type, expected int'
            assert output is None or type(output) == str, 'invalid output type, expected str or None'
            assert Attempt.get_attempt(attempt_id) is not None, f"no attempt with id '{attempt_id}'"
            assert Test.get_test(test_id) is not None, f"no test with id '{test_id}'"
            assert len(session.query(Trial).filter(Trial.attempt_id == attempt_id, Trial.test_id == test_id, Trial.status == status, Trial.output == output).all()) == 0, 'same trial has already been added'
            session.add(Trial(attempt_id=attempt_id,
                              test_id=test_id,
                              status=status,
                              output=output))
            session.commit()
            return {'status': 'ok', 'id': session.query(Trial).filter(Trial.attempt_id == attempt_id, Trial.test_id == test_id, Trial.status == status, Trial.output == output).first().id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Trial(output='{self.output}', status='{self.status}')"
