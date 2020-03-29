from sqlite3 import connect
from os import mkdir, listdir, getcwd
from hashlib import sha3_256
import tables
from flask_login import UserMixin
import json


def sha256(text: str):
    return sha3_256((text + json.load(open('config.json', 'r'))['SALT']).encode('UTF-8')).hexdigest()


class CreateDatabase:
    database = {
        'tasks.db': {
            'all_tasks': tables.all_tasks,
        },
        'users.db': {
            'all_users': tables.all_users,
        }
    }

    def __init__(self):
        if 'database' not in listdir(getcwd()):
            mkdir('database')

        for database_name in self.database:
            if database_name not in listdir('database'):
                db = open(f'database/{database_name}', 'w')
                db.close()
            con = connect(f'database/{database_name}')
            cur = con.cursor()
            for table_name in self.database[database_name]:
                if not cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchall():
                    cur.execute(self.database[database_name][table_name].replace('%table_name%', table_name))
                    con.commit()

    @staticmethod
    def drop():
        for database_name in CreateDatabase.database:
            db = open(f'database/{database_name}', 'w')
            db.close()


class User(UserMixin):
    def __init__(self, user_id: int):
        self.id = user_id
        self.username = self.password = self.name = self.surname = self.city = ""
        self.__update()

    def change_password(self, new_password: str):
        con, cur = self.__get_con_cur()
        cur.execute(f"UPDATE all_users SET password = '{sha256(new_password)}' WHERE id = {self.id}")
        con.commit()
        self.__update()

    def __update(self):
        con, cur = self.__get_con_cur()
        self.username, self.password, self.name, self.surname, self.city = cur.execute(f'SELECT * FROM all_users WHERE id = {self.id}').fetchall()[0][1:]

    @staticmethod
    def __get_con_cur():
        con = connect('database/users.db')
        cur = con.cursor()
        return con, cur

    @staticmethod
    def get_user(username: str, password: str):
        con, cur = User.__get_con_cur()
        hashed_password = sha256(password)
        user = cur.execute(f"SELECT id FROM all_users WHERE username = '{username}' AND password = '{hashed_password}'").fetchall()
        assert len(user) == 1
        return User(user[0][0])

    @staticmethod
    def add_user(username: str, password: str, name: str, surname: str, city: str) -> int:
        con, cur = User.__get_con_cur()
        hashed_password = sha256(password)
        cur.execute(f"INSERT INTO all_users(username, password, `name`, surname, city) VALUES('{username}', '{hashed_password}', '{name}', '{surname}', '{city}')")
        con.commit()
        user_id = cur.execute(f"SELECT id FROM all_users WHERE username = '{username}'").fetchall()[0][0]
        cur.execute(tables.user_example.replace('%id%', str(user_id)))
        con.commit()
        return user_id
