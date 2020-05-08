from flask import jsonify
from flask_restful import Resource, reqparse, abort
from models import User, Task, Contest, Attempt


def get_user(api_key: str, is_creator=False) -> User:
    user = User.get_api(api_key)
    if user is None or user.creator != is_creator:
        abort(401, message=f"Invalid api_key")
    return user


class MeResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        args = parser.parse_args()
        user = get_user(args['api_key'])
        return jsonify({'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'name': user.name,
                        'surname': user.surname,
                        'city': user.city,
                        'creator': bool(user.creator),
                        'register_date': user.register_date})

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        parser.add_argument('name')
        parser.add_argument('surname')
        parser.add_argument('city')
        args = parser.parse_args()
        user = get_user(args['api_key'])
        return jsonify(user.change_data(name=args.get('name'), surname=args.get('surname'), city=args.get('city')))


class TasksResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sort_type', required=False)
        args = parser.parse_args()
        return jsonify([{'id': task.id,
                         'title': task.title,
                         'time_limit': task.time_limit,
                         'creator': task.creator,
                         'attempts': task.attempts,
                         'successful': task.successful} for task in Task.get_all(args.get('sort_type', 'easy'))])


class ContestsResource(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('sort_type', required=False)
        args = parser.parse_args()
        return jsonify([{'id': contest.id,
                         'title': contest.title,
                         'creators': contest.creators,
                         'start_time': contest.start_time,
                         'end_time': contest.end_time} for contest in Contest.get_all(args.get('sort_type', 'new'))])


class ContestResource(Resource):
    def get(self, contest_id: int):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        parser.add_argument('show_solution', type=bool, default=False)
        args = parser.parse_args()
        user = get_user(args['api_key'])
        contest = Contest.get_contest(contest_id)
        if contest is None:
            abort(404, message=f'Invalid contest_id: {contest_id}')
        return jsonify({'title': contest.title,
                        'creators': ','.join(user.username for user in contest.get_creators()),
                        'description': contest.description,
                        'start_time': contest.start_time,
                        'end_time': contest.end_time,
                        'tasks': [{'id': task.id,
                                   'title': task.title,
                                   'best_attempt': (lambda attempt: {'id': attempt.id, 'score': attempt.score, 'status': attempt.status, 'time': attempt.time, 'solution': (attempt.solution if args.get('show_solution', False) else None)} if attempt is not None else None)(Attempt.get_best_result(contest.id, task.id, user.id)),
                                   'last_attempt': (lambda attempt: {'id': attempt.id, 'score': attempt.score, 'status': attempt.status, 'time': attempt.time, 'solution': (attempt.solution if args.get('show_solution', False) else None)} if attempt is not None else None)(Attempt.get_last_result(contest.id, task.id, user.id)),
                                   } for task in contest.get_tasks()]})

    def put(self, contest_id: int):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        parser.add_argument('title')
        parser.add_argument('description')
        parser.add_argument('start_time', type=int)
        parser.add_argument('end_time', type=int)
        args = parser.parse_args()
        user = get_user(args['api_key'], is_creator=True)
        contest = Contest.get_contest(contest_id)
        if contest is None:
            abort(404, message=f'Invalid contest_id: {contest_id}')
        if user not in contest.get_creators():
            abort(403, message=f'You are not creator of the contest')
        return jsonify(contest.change_data(title=args.get('title'), descriprion=args.get('description'), start_time=args.get('start_time'), end_time=args.get('end_time')))


class ContestTaskResource(Resource):
    def get(self, contest_id: int, task_id: int):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        parser.add_argument('show_solution', type=bool, default=False)
        args = parser.parse_args()
        user = get_user(args['api_key'])
        task = Task.get_task(task_id)
        if task is None:
            abort(404, message=f'Invalid task_id: {task_id}')
        contest = Contest.get_contest(contest_id)
        if contest is None:
            abort(404, message=f'Invalid contest_id: {contest_id}')
        return jsonify({'title': task.title,
                        'description': task.description,
                        'tests': [{'input': test.input, 'output': test.output} for test in (task.get_tests() if user.id == task.creator else task.get_tests()[:2])],
                        'time_limit': task.time_limit,
                        'creator': User.get_user(task.creator).username,
                        'attempts': {
                            'best_attempt': (lambda attempt: {'id': attempt.id, 'score': attempt.score, 'status': attempt.status, 'time': attempt.time, 'solution': (attempt.solution if args.get('show_solution', False) else None)} if attempt is not None else None)(Attempt.get_best_result(contest_id, task_id, user.id)),
                            'last_attempt': (lambda attempt: {'id': attempt.id, 'score': attempt.score, 'status': attempt.status, 'time': attempt.time, 'solution': (attempt.solution if args.get('show_solution', False) else None)} if attempt is not None else None)(Attempt.get_last_result(contest_id, task_id, user.id)),
                            'all': [{'id': attempt.id, 'score': attempt.score, 'status': attempt.status, 'time': attempt.time, 'solution': (attempt.solution if args.get('show_solution', False) else None)} for attempt in Attempt.get_attempts(contest_id, task_id, user.id)]
                        },
                        'reference': task.reference if user.id == task.creator else None})


class AttemptResource(Resource):
    def get(self, attempt_id):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', required=True)
        args = parser.parse_args()
        user = get_user(args['api_key'])
        attempt = Attempt.get_attempt(attempt_id)
        if attempt is None:
            abort(404, message=f'Invalid attempt_id: {attempt_id}')
        if attempt.user_id != user.id:
            abort(401, message=f'You have no rights to see this attempt')
        return jsonify({'score': attempt.score,
                        'status': attempt.status,
                        'time': attempt.time,
                        'solution': attempt.solution,
                        'tests': [{'status': test.status} for test in attempt.get_tests_statuses()]})
