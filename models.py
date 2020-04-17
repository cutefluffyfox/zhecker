import sqlalchemy
from db_session import SqlAlchemyBase, create_session
from flask_login import UserMixin
from random import randint
from hashlib import sha3_256
from json import load


def _like(text: str) -> str:
    return '%' + text + '%'


class Test(SqlAlchemyBase):
    __tablename__ = 'tests'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    task_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("tasks.id"), nullable=False)
    input = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    output = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    points = sqlalchemy.Column(sqlalchemy.Integer, default=1)

    def change_data(self, inp=None, out=None, points=None):
        """
        Change input/output/points, return
        {'status': 'ok'}
        {'status': 'invalid <input/output/points> type, expected <str/int> or None'}
        {'status': 'same test has already been added'}
        """
        try:
            session = create_session()
            assert inp is None or type(inp) == str, 'invalid input type, expected str'
            assert out is None or type(out) == str, 'invalid output type, expected str'
            assert points is None or type(points) == int, 'invalid input type, expected int'
            assert len(session.query(Test).filter(Test.task_id == self.task_id, Test.input == (self.input if inp is None else inp), Test.output == (self.output if out is None else out)).all()) == 0, 'same test has already been added'
            test = session.query(Test).filter(Test.id == self.id).first()
            if inp is not None:
                self.input = test.input = inp
            if out is not None:
                self.output = test.output = out
            if points is not None:
                self.points = test.points = points
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    @staticmethod
    def get_test(test_id: int):
        """Return Test(**kwargs) by test_id or None if id is invalid"""
        session = create_session()
        return session.query(Test).filter(Test.id == test_id).first()

    @staticmethod
    def add_test(task_id: int, inp: str, out: str, points=None) -> dict:
        """
        Add test to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <input/output/points> type, expected <str/int>'}
        {'status': 'no task with id '<task_id>''}
        {'status': 'same test has already been added'}
        """
        try:
            session = create_session()
            assert len(session.query(Task).filter(Task.id == task_id).all()) == 1, f'no task with id \'{task_id}\''
            assert type(inp) == str, 'invalid input type, expected str'
            assert type(out) == str, 'invalid output type, expected str'
            assert points is None or type(points) == int, 'invalid points type, expected int'
            assert len(session.query(Test).filter(Test.task_id == task_id, Test.input == inp, Test.output == out).all()) == 0, 'same test has already been added'
            test = Test(task_id=task_id,
                        input=inp,
                        output=out,
                        points=points)
            session.add(test)
            session.commit()
            return {'status': 'ok', 'id': session.query(Test).filter(Test.task_id == task_id, Test.input == inp, Test.output == out).first().id}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def __repr__(self):
        return f"Test(input='{self.input}', output='{self.output}')"


class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    reference = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    attempts = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    successful = sqlalchemy.Column(sqlalchemy.Integer, default=0)

    def change_data(self, title=None, description=None, reference=None):
        """
        Change title/description/reference, return
        {'status': 'ok'}
        {'status': 'same task has already been added'}
        {'status': 'invalid <title/description/reference> type, expected str or None'}
        """
        try:
            session = create_session()
            assert title is None or type(title) == str, 'invalid title type, expected str or None'
            assert description is None or type(description) == str, 'invalid description type, expected str or None'
            assert reference is None or type(reference) == str, 'invalid reference type, expected str or None'
            assert len(session.query(Task).filter(Task.creator == self.creator, Task.title == (self.title if title is None else title), Task.description == (self.description if description is None else description), Task.reference == (self.reference if reference is None else reference)).all()) == 0, "same task has already been added"
            task = session.query(Task).filter(Task.id == self.id).first()
            if title is not None:
                self.title = task.title = title
            if description is not None:
                self.description = task.description = description
            if reference is not None:
                self.reference = task.reference = reference
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    def get_tests(self):
        """Return [Test(**kwargs), ...] sorted by index (recent added at the back)"""
        session = create_session()
        return session.query(Test).filter(Test.task_id == self.id).order_by(sqlalchemy.desc(~Test.id)).all()

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
        return session.query(Task).order_by(sqlalchemy.desc(sort[sort_type])).all()

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
    def add_task(creator: int, title: str, description: str, reference: str) -> dict:
        """
        Add task to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <title/description/reference> type, expected str'}
        {'status': 'no user with id '<creator>''}
        {'status': 'same task has already been added'}
        """
        try:
            session = create_session()
            user = session.query(User).filter(User.id == creator).first()
            assert user is not None, f"no user with id '{creator}'"
            assert type(title) == str, 'invalid title type, expected str'
            assert type(description) == str, 'invalid description type, expected str'
            assert type(reference) == str, 'invalid reference type, expected str'
            assert len(session.query(Task).filter(Task.creator == creator, Task.title == title, Task.description == description, Task.reference == reference).all()) == 0, "same task has already been added"
            task = Task(creator=creator,
                        title=title,
                        description=description,
                        reference=reference)
            session.add(task)
            session.commit()
            return {'status': 'ok', 'id': session.query(Task).filter(Task.creator == creator, Task.title == title, Task.description == description, Task.reference == reference).first().id}
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

    @staticmethod
    def get_contest(contest_id):
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
            contest = Contest(
                creators=','.join(creators),
                title=title,
                description=description,
                tasks=','.join(tasks),
                start_time=start_time,
                end_time=end_time
            )
            session.add(contest)
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
    city = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    creator = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    verification = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    contests = sqlalchemy.Column(sqlalchemy.String, default='')

    def change_data(self, username=None, email=None, name=None, surname=None, city=None, password=None) -> dict:
        """
        Change username/email/name/surname/city/password, return
        {'status': 'ok'}
        {'status': '<username/email> is already taken'}
        {'status': 'invalid <username/email/name/surname/city/password> type, expected str or None'}
        """
        try:
            session = create_session()
            assert username is None or type(username) == str, 'invalid username type, expected str or None'
            assert email is None or type(email) == str, 'invalid email type, expected str or None'
            assert name is None or type(name) == str, 'invalid name type, expected str or None'
            assert surname is None or type(surname) == str, 'invalid surname type, expected str or None'
            assert city is None or type(city) == str, 'invalid city type, expected str or None'
            assert password is None or type(password) == str, 'invalid password type, expected str or None'
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
            session.commit()
            return {'status': 'ok'}
        except AssertionError as ex:
            return {'status': ex.args[0]}

    @staticmethod
    def get_users_by_username(username: str):
        """Return [User(**kwargs), ...] by username where User.username like username"""
        session = create_session()
        return session.query(User).filter(User.username.like(_like(username))).all()

    @staticmethod
    def get_user(user_id: int):
        """Return User(**kwargs) by user_id or None if id is invalid"""
        session = create_session()
        return session.query(User).filter(User.id == user_id).first()

    @staticmethod
    def authorize_user(username: str, password: str):
        """Return User(**kwargs) by username and not hashed password or None if username or password is invalid"""
        session = create_session()
        return session.query(User).filter(User.username == username, User.password == User.__generate_password(password)).first()

    @staticmethod
    def __generate_password(password: str) -> str:
        return sha3_256((password + load(open('config.json', 'r', encoding='UTF-8'))['SALT']).encode('UTF-8')).hexdigest()

    @staticmethod
    def add_user(username: str, email: str, password: str, name: str, surname: str, city=None) -> dict:
        """
        Add user to database, return:
        {'status': 'ok', 'id': int}
        {'status': 'invalid <password/name/surname> type, expected str'}
        {'status': '<username/email> is already taken'}
        """
        try:
            session = create_session()
            assert type(password) == str, 'invalid password type, expected str'
            assert type(name) == str, 'invalid name type, expected str'
            assert type(surname) == str, 'invalid surname type, expected str'
            assert len(session.query(User).filter(User.username == username).all()) == 0, 'username is already taken'
            assert len(session.query(User).filter(User.email == email).all()) == 0, 'email is already taken'
            session.add(User(username=username,
                             email=email,
                             password=User.__generate_password(password),
                             name=name,
                             surname=surname,
                             city=city,
                             verification="".join([chr(randint(65, 90)) if randint(0, 1) else chr(randint(97, 122)) for _ in range(30)])))
            session.commit()
            return {'status': 'ok', 'id': session.query(User).filter(User.username == username).first().id}
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
    score = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    time = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    def __repr__(self):
        return f"Attempt(score={self.score}, status='{self.status}')"

