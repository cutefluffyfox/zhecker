import subprocess
from os import remove
from time import time
import models


class Checker:
    RESTRICTED = {'import'}
    time_to_start_process = 0.6  # some extra time before timeout
    errors = {
        'OK': 'successfully',
        'SB': 'solution banned',
        'WA': 'wrong answer',
        'CE': 'compilation error',
        'RE': 'run-time error',
        'TL': 'time limit',
        'TS': 'test skipped'
    }

    @staticmethod
    def get_output(task_id: int, inp: str) -> (str, str):
        try:
            task = models.Task.get_task(task_id)
            file = Checker.__save_file(task.reference)
            if Checker.__check_restricted(file):
                Checker.__close_file(file)
                return 'SB', ''
            result = subprocess.run(["python3.7", f'{file}'], input=inp, text=True, capture_output=True,
                                    timeout=task.time_limit + Checker.time_to_start_process, start_new_session=True)
            Checker.__close_file(file)
            if result.returncode == 0:
                return 'OK', result.stdout
            elif 'SyntaxError' in result.stderr:
                return 'CE', ''
            else:
                return 'RE', ''
        except subprocess.TimeoutExpired:
            Checker.__close_file(file)
            return 'TL', ''

    @staticmethod
    def check_attempt(attempt_id: int):
        attempt = models.Attempt.get_attempt(attempt_id)
        file = Checker.__save_file(attempt.solution)
        task = models.Task.get_task(attempt.task_id)
        status = 'OK'
        score = 0
        for ind, test in enumerate(task.get_tests()):
            if status == 'OK':
                status, output = Checker.__check_test(file, test.input, test.output, task.time_limit if ind != 0 else task.time_limit + 1)
                models.Trial.add_trial(attempt_id=attempt_id, test_id=test.id, status=status, output=(output if output else None))
                score = score + (test.points if status == 'OK' else 0)
            else:
                models.Trial.add_trial(attempt_id=attempt_id, test_id=test.id, status='TS')
        attempt.change_data(status=status, score=score)
        models.Task.get_task(task.id).add_attempt(status == 'OK')
        Checker.__close_file(file)

    @staticmethod
    def __check_test(file: str, inp: str, out: str, tl: int) -> (str, str):
        try:
            if Checker.__check_restricted(file):
                return 'SB', ''
            result = subprocess.run(["python3.7", f'{file}'], input=inp, text=True, capture_output=True, timeout=tl + Checker.time_to_start_process, start_new_session=True)
            if result.returncode == 0 and result.stdout == out:
                return 'OK', ''
            elif result.returncode == 0:
                return 'WA', result.stdout
            elif 'SyntaxError' in result.stderr:
                return 'CE', ''
            else:
                return 'RE', ''
        except subprocess.TimeoutExpired:
            return 'TL', ''

    @staticmethod
    def __save_file(solution: str) -> str:
        file_name = f"{int(time())}_{len(solution)}.py"
        file = open(file_name, 'w', encoding='UTF-8')
        file.write(solution)
        return file_name

    @staticmethod
    def __close_file(file: str):
        remove(file)

    @staticmethod
    def __check_restricted(file: str):
        solution = open(file, 'r', encoding='UTF-8').read()
        for bad_stuff in Checker.RESTRICTED:
            if bad_stuff in solution:
                return True
        return False
