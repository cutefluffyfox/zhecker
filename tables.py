all_tasks = """
CREATE TABLE `%table_name%` (
    `id` INTEGER PRIMARY KEY autoincrement,
    `author` TEXT NOT NULL,
    `time_limit` FLOAT NULL,
    `description` TEXT NULL,
    `attempts` INT DEFAULT 0,
    `successful_attempts` INT DEFAULT 0
);
"""


test_example = """
CREATE TABLE `test_%id%` (
    `id` INTEGER PRIMARY KEY autoincrement,
    `input` TEXT NOT NULL,
    `output` TEXT NULL,
    `points` INT NULL
);
"""


all_users = """
CREATE TABLE `%table_name%` (
    `id` INTEGER PRIMARY KEY autoincrement,
    `username` TEXT UNIQUE NOT NULL,
    `password` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `surname` TEXT NOT NULL,
    `city` TEXT NULL
);
"""


user_example = """
CREATE TABLE `user_%id%` (
    `id` INTEGER PRIMARY KEY autoincrement,
    `contest` INT DEFAULT 0,
    `task` INT NOT NULL,
    `code` TEXT NULL,
    `result` INT DEFAULT 0
);
"""
