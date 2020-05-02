from os import environ, listdir, getcwd
from json import load

if 'config.json' in listdir(getcwd()):
    with open('config.json', 'r', encoding='UTF-8') as file:
        json = load(file)
        for key, value in json.items():
            environ[key] = value
