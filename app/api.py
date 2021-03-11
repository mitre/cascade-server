# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import json
import traceback
import datetime
from collections import defaultdict
from functools import wraps
from http import HTTPStatus
from itertools import chain


import bson
import mongoengine
from mongoengine.queryset.base import BaseQuerySet
from flask import request, Response

from app import utils
from app.cascade.jobs import AnalyticJob, Job, TuningJob, CustomQueryJob, InvestigateJob
from app.cascade.analytics import AnalyticResult, Analytic, CascadeAnalytic, AnalyticBaseline, ExternalAnalytic, AnalyticConfigurationList, AnalyticConfiguration
from app.cascade.data_model import Host, parser
from app.cascade.data_model.event import DataModelEvent, InvalidFieldError, InvalidActionError, InvalidObjectError, DataModelQuery
from app.cascade.data_model import event_lookup, pivot_lookup
from app.cascade.database import DateRange, AbsoluteRange, RelativeRange
from app.cascade.query_layers import mappings, DataModelQueryLayer
from app.cascade.session import Session, SessionState
from app.cascade.cluster import HierarchicalCluster, ClusterKey
from app.cascade.attack import AttackTactic, AttackTechnique, refresh_attack, TacticSet
from app.cascade.query_layers import DatabaseInfo
from app.server import flask_app
from app import users
from app.utils import json_default, bson_default
from app import settings
#
#  Route the REST API  (output in JSON)
#
api_endpoints = {}


# Wrap dumps in pprint-formatted json
def jsonify(obj, indent=2):
    return json.dumps(obj, sort_keys=True, indent=indent, default=json_default)


def bsonify(obj, indent=2):
    return json.dumps(obj, indent=2, sort_keys=True, default=bson_default)


class JSONResponse(Response):
    _messages = {
        HTTPStatus.NOT_FOUND: 'resource not found',
        HTTPStatus.UNAUTHORIZED: 'login required',
        HTTPStatus.INTERNAL_SERVER_ERROR: 'exception while handling request',
        HTTPStatus.NOT_IMPLEMENTED: 'function not yet implemented'
    }

    def __init__(self, json_obj=None, status=HTTPStatus.OK):
        if status in self._messages:
            json_obj = {'error': self._messages[status]}
        super(JSONResponse, self).__init__(jsonify(json_obj), content_type='application/json', status=status)


def rest_doc(api_function):
    doc = api_function.__doc__
    if doc is not None:
        return "\n".join(_.strip() for _ in doc.strip().splitlines())


def api(uri, login=False, **kwargs):
    def decorator(f):
        @wraps(f)
        def wrapped_f(*func_args, **func_kwargs):
            if login:
                user_token = request.cookies.get('user-token')
                if user_token is not None:
                    try:
                        func_kwargs['user'] = users.validate_token(user_token)
                    except utils.AuthenticationError:
                        return JSONResponse(status=HTTPStatus.UNAUTHORIZED)
                else:
                    return JSONResponse(status=HTTPStatus.UNAUTHORIZED)

            try:
                results, status_code = f(*func_args, **func_kwargs)
                if 'count' in request.args:
                    if isinstance(results, BaseQuerySet):
                        results = results.count()
                    else:
                        results = len(results)

            except mongoengine.ValidationError:
                traceback.print_exc()
                status_code = HTTPStatus.BAD_REQUEST
                results = {"error": "invalid input"}

            except mongoengine.NotUniqueError:
                traceback.print_exc()
                status_code = HTTPStatus.BAD_REQUEST
                results = {"error": "not unique"}

            except Exception as e:
                traceback.print_exc()
                status_code = HTTPStatus.INTERNAL_SERVER_ERROR
                results = None

            if request.args.get('format', 'json') == 'bson':
                output = bsonify(results)  # .json_util.dumps(results, indent=2, sort_keys=True)
                return Response(output, status=status_code, content_type='application/json')
            else:
                return JSONResponse(results, status=status_code)

        endpoint = kwargs.pop('endpoint', f.__name__)  # + str(len(api_endpoints)))
        flask_app.add_url_rule(uri, endpoint, wrapped_f, **kwargs)
        assert endpoint not in api_endpoints
        api_endpoints[endpoint] = f, uri, kwargs.get('methods', ['GET']), rest_doc(f)
        return f
    return decorator


@api('/api', methods=['GET'])
def query_api():
    endpoints = [{'name': name, 'uri': uri.replace('<', '{').replace('>', '}'), 'methods': methods, 'doc': doc}
                 for name, (f, uri, methods, doc) in api_endpoints.items()]
    endpoints.sort(key=lambda x: x['uri'])
    return endpoints, HTTPStatus.OK


@api('/api/debug', methods=['GET', 'POST'], login=True)
def debug(user=None):
    # Turn on debug printing automatically if a debugger is attached
    try:
        import pydevd
        pydevd.settrace()
    except ImportError:
        pass
    return None, HTTPStatus.OK


@api('/api/login', methods=['POST'])
def login():
    if request.args.get('action') == 'reset_password':
        reset_token = request.json.get('token')
        password = request.json.get('password')

        try:
            user = users.reset_password(reset_token, password)
        except users.PasswordPolicyError as error:
            regex, rules = error.args
            return {'violation': {'regex': regex, 'rules': rules}}, HTTPStatus.BAD_REQUEST

        if user is not None:
            return {'username': user.username}, HTTPStatus.OK
        else:
            return None, HTTPStatus.BAD_REQUEST

    elif request.args.get('action') == 'forgot_password':
        email = request.json.get('email')
        if email:
            user = users.User.objects(email=email).first()
            if user is not None:
                user.send_reset_email()
        return None, HTTPStatus.OK

    persistent = request.args.get('persistent', 'true').lower() == 'true'

    try:
        if isinstance(request.json, dict):
            if request.json.get('api_token') is not None:
                token = request.json['api_token']
                user = users.validate_token(token)
                if user is not None:
                    info = {'api_token': token, 'username': user.username, 'full_name': user.full_name, 'email': user.email}
                    return info, HTTPStatus.OK

            elif request.json.get('user') is not None and request.json.get('password') is not None:
                user = users.login(request.json['user'], request.json['password'])
                return {'api_token': user.generate_token(persistent=persistent),
                        'username': user.username,
                        'full_name': user.full_name,
                        'email': user.email}, HTTPStatus.OK

        if request.cookies.get('user-token'):
            user_token = request.cookies.get('user-token')
            user = users.validate_token(user_token)
            return {'api_token': user.generate_token(persistent=persistent),
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email}, HTTPStatus.OK

    except (utils.AuthenticationError, users.AuthenticationError):
        # The default error message returns HTTP 401 regardless
        pass

    return None, HTTPStatus.UNAUTHORIZED


@api('/api/attack', methods=['GET'])
def query_attack():
    if 'refresh' in request.args:
        refresh_attack()
    attack = {'tactics': attack_tactics()[0], 'techniques': attack_techniques()[0]}
    return attack, HTTPStatus.OK


@api('/api/attack', methods=['POST'], login=True)
def update_attack(user):
    if 'refresh' in request.args:
        refresh_attack()
    return query_attack(), HTTPStatus.OK


@api('/api/attack/tactics', methods=['GET'])
def attack_tactics():
    return AttackTactic.objects().order_by('order'), HTTPStatus.OK


@api('/api/attack/techniques', methods=['GET'])
def attack_techniques():
    return AttackTechnique.objects(), HTTPStatus.OK


@api('/api/attack/tactic_sets', methods=['GET', 'POST'])
def tactic_sets():
    if request.method == 'GET':
        return TacticSet.objects, HTTPStatus.OK
    elif request.method == 'POST':
        if isinstance(request.json, dict):
            tactic_set = TacticSet(tactics=request.json['tactics']).save()
            return tactic_set.id, HTTPStatus.OK


@api('/api/attack/tactic_sets/<set_id>', methods=['GET', 'DELETE'])
def tactic_set_query(set_id):
    tactic_set = TacticSet.objects.with_id(set_id)
    if tactic_set is None:
        return {}, HTTPStatus.NOT_FOUND
    if request.method == 'GET':
        return tactic_set, HTTPStatus.OK

    elif request.method == 'DELETE':
        return tactic_set.delete(), HTTPStatus.OK


@api('/api/databases', methods=['GET', 'POST'], login=True)
def query_databases(user=None):
    if request.method == 'GET':
        return DatabaseInfo.objects(), HTTPStatus.OK

    elif request.method == 'POST':
        db_cls = mongoengine.base.get_document(request.json.get('_cls'))
        if db_cls and issubclass(db_cls, DatabaseInfo):
            database = db_cls(**request.json)
            database.save()
            return database.id, HTTPStatus.OK
        else:
            return None, HTTPStatus.BAD_REQUEST


@api('/api/schemas/databases', methods=['GET'], login=True)
def query_database_schemas(user=None):
    if request.method == 'GET':
        return DatabaseInfo.get_schemas(), HTTPStatus.OK


@api('/api/databases/<database_id>', methods=['GET', 'PUT', 'DELETE'], login=True)
def query_database(database_id, user=None):
    database = DatabaseInfo.objects.with_id(database_id)
    if database is None and request.method != 'PUT':
        return None, HTTPStatus.NOT_FOUND

    if request.method == 'GET':
        return database, HTTPStatus.OK

    elif request.method == 'PUT':
        db_info = dict(request.json)
        db_info['id'] = database_id
        return DatabaseInfo(**db_info), HTTPStatus.OK

    elif request.method == 'DELETE':
        return database.delete(), HTTPStatus.OK


@api('/api/user', methods=['GET'], login=True)
def query_user(user):
    user_info = user.to_mongo().to_dict()
    user_info.pop('sha256_hash', None)
    user_info.pop('databases', None)
    return user_info, HTTPStatus.OK


@flask_app.route('/api/user', methods=['POST'])
def create_user():
    if not settings.load()['config'].get('allow_account_creation', False):
        return JSONResponse(status=HTTPStatus.FORBIDDEN)

    """ This API route is used by the create new account template to add a new user into Mongo """
    if isinstance(request.json, dict):
        args = request.json
        if args.get('username') and args.get('password'):
            try:
                user = users.create_user(args['username'], args['password'], args.get('email'), args.get('full_name'))
            except users.PasswordPolicyError as error:
                regex, rules = error.args
                return JSONResponse({'violation': {'regex': regex, 'rules': rules}}, HTTPStatus.BAD_REQUEST)

            if user is not None:
                response = Response(status=HTTPStatus.CREATED)
                response.set_cookie('user-token', user.generate_token(), max_age=datetime.timedelta(days=7))
                return response
            else:
                return JSONResponse({'message': 'Username already exists!'}, status=HTTPStatus.BAD_REQUEST)

    return JSONResponse({'message': 'Username, email and password are required'}, status=HTTPStatus.BAD_REQUEST)


@api('/api/user/databases', methods=['GET', 'POST'], login=True)
def user_databases(user=None):

    if request.method == 'GET':
        user_layers = [{'name': user_db_info.database.name,
                        'username': user_db_info.username,
                        '_id': user_db_info.database.id} for user_db_info in user.databases]
        return user_layers, HTTPStatus.OK

    else:
        if not isinstance(request.json, dict) or 'database' not in request.json or 'action' not in request.args:
            return None, HTTPStatus.BAD_REQUEST

        action = request.args['action']
        database_info = DatabaseInfo.objects.with_id(request.json.pop('database'))
        if database_info is None:
            return None, HTTPStatus.BAD_REQUEST

        if action == 'remove':
            status = user.remove_layer(database_info.id)
            return status, (HTTPStatus.OK if status else HTTPStatus.BAD_REQUEST)

        elif action == 'add' and database_info.id:
            user_db_info = database_info.add_user(**request.json)
            # TODO! handle nicely
            try:
                user_db_info.login()
                user.add_layer(user_db_info)
                return True, HTTPStatus.OK
            except utils.AuthenticationError:
                return {'error': 'login'}, HTTPStatus.BAD_REQUEST
        else:
            return {}, HTTPStatus.BAD_REQUEST


@api('/api/sessions', methods=['GET', 'POST'], login=True)
def all_sessions(user=None):
    """ :type user: User """
    if request.method == 'GET':
        query = {}
        if 'name' in request.args:
            query['name'] = request.args['name']

        sessions = Session.objects(**query).order_by('name')
        return sessions, HTTPStatus.OK

    elif request.method == 'POST':
        if 'clone' in request.args:
            original = Session.objects.with_id(request.args.get('clone'))
            original_id = original.id

            if original is None:
                return {'error': 'source session could not be found'}, HTTPStatus.BAD_REQUEST

            session = original
            session.id = None
            session.name = request.json['name']
            session.save(validate=True)
            # Clone over all of the data model events
            DataModelEvent.objects(sessions=original_id).update(add_to_set__sessions=session.id)
            for result in AnalyticResult.objects(session=original_id):
                result.id = None
                result.session = session
                result.uuid = result.get_uuid()
                result.save()
        else:
            info = request.json

            if info.get('range') is not None and info.get('name') is not None:
                time_range = DateRange.get_range(info['range'])
                session = Session(range=time_range, name=info['name'])
            session.save(validate=True)

        return session.id, HTTPStatus.OK


@api('/api/sessions/<session>', methods=['GET', 'PUT', 'POST', 'DELETE'], login=True)
def query_session(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    session_id = session
    session = Session.objects.with_id(session)

    if request.method == 'GET':
        if session:
            return session, HTTPStatus.OK
        return None, HTTPStatus.NOT_FOUND

    elif request.method == 'PUT':
        # Create a new session if it doesn't exist
        if not session:
            session = Session(id=session_id)
            http_status = HTTPStatus.CREATED
        else:
            http_status = HTTPStatus.OK

        try:
            session.update(**request.json)
            session.validate()
        except mongoengine.ValidationError:
            return {'error': 'schema validation error'}, HTTPStatus.BAD_REQUEST

        session.save()
        return None, http_status

    elif request.method == 'POST':
        if 'reset' in request.args:
            DataModelEvent.objects(sessions=session).update(pull__sessions=session)
            AnalyticResult.objects(session=session).delete()
            Job.objects(session=session).delete()
            # Remove the session state
            session.update(state=SessionState())
            # Is this the right http error code?
            return None, HTTPStatus.RESET_CONTENT

        elif 'refresh' in request.args:
            for analytic_state in session.state.analytics:
                job = AnalyticJob.update_existing(analytic=analytic_state.analytic, mode=analytic_state.mode, user=user, session=session)
                job.submit()
            return None, HTTPStatus.RESET_CONTENT

    # TODO: Implement
    elif request.method == 'DELETE':
        DataModelEvent.objects(sessions=session).update(pull__sessions=session)
        AnalyticResult.objects(session=session).delete()
        Job.objects(session=session).delete()
        session.delete()
        return None, HTTPStatus.NO_CONTENT


@api('/api/sessions/<session>/results', methods=['GET'], login=True)
def session_results(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    if request.method == 'GET':
        session = Session.objects.with_id(session)
        if not session:
            return None, HTTPStatus.NOT_FOUND

        if isinstance(session.range, RelativeRange):
            status = AnalyticResult.objects(session=session, time__lt=session.range.start_time).delete()

        results = AnalyticResult.objects(session=session)

        if request.args.get('format') == 'tree':
            analytic_index = defaultdict(list)
            for analytic_result in results:
                for event in analytic_result.events:
                    state = event.state.to_mongo().to_dict()
                    analytic_index[analytic_result.analytic.id].append(state)

            results = []
            for analytic, result_list in analytic_index.items():
                baseline = HierarchicalCluster()
                # need to get keys field
                # TODO: make smarter choices about these fields (pid, ppid, etc.)
                baseline.keys = [ClusterKey(name=k, status=True) for k in Analytic.objects.with_id(analytic).fields]
                baseline.cluster_events(result_list, min_size=1)
                results.append({'analytic': analytic, 'root': baseline.root, 'keys': baseline.keys})

        return results, HTTPStatus.OK


@api('/api/sessions/<session>/results/<analytic>', methods=['GET'], login=True)
def session_analytic_results(session, analytic, user=None):
    """
    :type session: Session
    :type user: User
    """
    if request.method == 'GET':
        session = Session.objects.with_id(session)
        analytic = Analytic.objects.with_id(analytic)

        if not session or not analytic:
            return None, HTTPStatus.NOT_FOUND

        if isinstance(session.range, RelativeRange):
            status = AnalyticResult.objects(session=session, analytic=analytic, time__lt=session.range.start_time).delete()

        results = AnalyticResult.objects(session=session, analytic=analytic)

        if request.args.get('format') == 'tree':
            result_states = []
            for analytic_result in results:
                for event in analytic_result.events:
                    state = event.state.to_mongo().to_dict()
                    result_states.append(state)

            cluster = HierarchicalCluster()
            # need to get keys field
            keys = request.args.getlist('key')
            cluster.keys = [ClusterKey(name=f, status=not len(keys) or f in keys) for f in analytic.fields]

            cluster.cluster_events(result_states, min_size=1)
            return {'root': cluster.root, 'keys': cluster.keys}, HTTPStatus.OK

        return results, HTTPStatus.OK


@api('/api/sessions/<session>/graphs/alerts', methods=['GET'], login=True)
def alert_graph(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    if request.method == 'GET':
        session = Session.objects.with_id(session)
        if not session:
            return None, HTTPStatus.NOT_FOUND

        # Avoid too many database lookups
        events = {e.id: e for e in DataModelEvent.objects(sessions=session)}

        results = list(AnalyticResult.objects(session=session))
        edges = set()
        result_lookup = defaultdict(list)

        for result in results:
            for event in result.events:
                result_lookup[event.id].append(result.id)

        def descendant_analytics(_event):
            children = []
            for child_event in _event.links:
                # Stop once I hit an analytic
                if child_event.id in result_lookup:
                    children.extend(result_lookup[child_event.id])
                elif child_event.id in events:
                    children.extend(descendant_analytics(events[child_event.id]))
            return children

        for i, result in enumerate(results):
            for event in result.events:
                for similar_result in result_lookup[event.id]:
                    if similar_result is not result:
                        pass
                if event.id in events:
                    for edge in descendant_analytics(events[event.id]):
                        if edge != result.id:
                            edges.add((result.id, edge))

        return {'nodes': results, 'edges': list(edges)}, HTTPStatus.OK


@api('/api/sessions/<session>/attack_timeline', methods=['GET'], login=True)
def attack_timeline(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    timeline = []
    results = AnalyticResult.objects(session=session)
    for result in results:
        for event in result.events:
            for coverage in result.analytic.coverage:
                attack_event = {
                    "technique": coverage.technique.id,
                    "tactics": [] if coverage.tactics is None else [_.id for _ in coverage.tactics],
                    "discovered_time": event.discovered_time,
                    "event_id": event.id
                    # TODO add support for hosts
                }
                timeline.append(attack_event)

    return sorted(timeline, key=lambda k: k['discovered_time']), HTTPStatus.OK


@api('/api/sessions/<session>/graphs/technique', methods=['GET'], login=True)
def technique_graph(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    orig_graph, status = alert_graph(session)
    old_edges = defaultdict(list)

    if status != HTTPStatus.OK:
        return None, status

    edges = set()
    nodes = []
    incoming_edges = defaultdict(set)
    outgoing_edges = defaultdict(set)
    # Cache this to avoid lookups
    analytics = {_.id: _ for _ in Analytic.objects()}

    for result in orig_graph['nodes']:
        coverage = analytics[result.analytic.id].coverage
        if coverage is None or len(coverage) == 0:
            continue

        # Get all of the techniques
        for mapping in coverage:
            # TODO: resolve this case
            if mapping.technique is None:
                continue
            technique = mapping.technique
            technique_node = {'technique': technique.id, 'group': 'technique', 'id': hash((technique.id, result.id))}
            nodes.append(technique_node)
            incoming_edges[result.id].add(technique_node['id'])

            if not mapping.tactics:  # if null or empty
                outgoing_edges[result.id].add(technique_node['id'])
            else:
                for tactic in mapping.tactics:
                    tactic_node = {'tactic': tactic.id, 'group': 'tactic', 'id': hash((technique.id, result.id, tactic.id))}
                    nodes.append(tactic_node)
                    edges.add((technique_node['id'], tactic_node['id']))
                    outgoing_edges[result.id].add(tactic_node['id'])

    for node in orig_graph['nodes']:
        nodes.append({'_id': node.id, 'group': 'event'})
        edges.update([(node.id, next_id) for next_id in incoming_edges[node.id]])

    for source_id, target_id in orig_graph['edges']:
        edges.update([(middle_id, target_id) for middle_id in outgoing_edges[source_id]])

    return {'nodes': nodes, 'edges': list(edges)}, HTTPStatus.OK


@api('/api/sessions/<session>/events', methods=['GET'], login=True)
def session_events(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    if request.method == 'GET':
        session = Session.objects.with_id(session)
        if isinstance(session.range, RelativeRange):
            DataModelEvent.objects(sessions=session, time__lt=session.range.start_time).update(pull__sessions=session)

        return DataModelEvent.objects(sessions=session).order_by('time'), HTTPStatus.OK


@api('/api/sessions/<session>/hosts', methods=['GET'], login=True)
def query_session_hosts(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    host_ids = set()
    for event in DataModelEvent.objects(sessions=session):
        event.update_host()
        if event.host:
            host_ids.add(event.host.id)

    host_list = [Host.objects.with_id(_) for _ in host_ids]
    return host_list, HTTPStatus.OK


@api('/api/jobs', methods=['GET', 'POST', 'DELETE'], login=True)
def query_jobs(query_filter=None, user=None):
    """ :type user: User """

    query_filter = {} if query_filter is None else query_filter.copy()
    query_filter.update(dict(request.args.items()))
    query_filter.pop('count', None)

    format = query_filter.pop('format', None)
    multiple = query_filter.pop('multi', False)

    jobs = Job.objects()
    if 'type' in query_filter:
        query_filter['_cls'] = query_filter.pop('type')

    jobs = Job.objects(**query_filter)

    if request.method == 'GET':
        if format == 'summary':
            summary = {k: jobs.filter(status=k).count() for k in Job.codes}
            summary['total'] = sum(summary.values())
            return summary, HTTPStatus.OK
        return jobs, HTTPStatus.OK

    elif request.method == 'DELETE':
        jobs.delete()
        return None, HTTPStatus.OK

    elif request.method == 'POST' and multiple and 'status' in request.json:
        status = request.json['status']
        updated = {'status': status, 'updated': datetime.datetime.utcnow()}
        if status != Job.FAILURE:
            updated['message'] = None
        return jobs.update(**updated), HTTPStatus.OK

    return None, HTTPStatus.BAD_REQUEST


@api('/api/jobs/<job>', methods=['GET', 'POST', 'DELETE'], login=True)
def query_job(job, user=None):
    """
    :type job: Job
    :type user: User
    """
    job = Job.objects.with_id(job), HTTPStatus.OK
    if job is None:
        return None, HTTPStatus.NOT_FOUND

    if request.method == 'GET':
        return job, HTTPStatus.OK

    elif request.method == 'POST':
        return job.modify(**request.json), HTTPStatus.OK

    elif job and request.method == 'DELETE':
        job.delete()
        return None, HTTPStatus.OK


@api('/api/sessions/<session>/jobs', methods=['GET'], login=True)
def query_session_jobs(session, user=None):
    """
    :type session: Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    return query_jobs(query_filter={'session': session.id}, user=user)

@api('/api/sessions/<session>/jobs/<status>', methods=['GET'], login=True)
def query_session_job_status(session, status, user=None):
    """
    :type session: Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    if status not in ['success', 'started', 'dispatched', 'ready', 'failure', 'created']:
        return None, HTTPStatus.NOT_FOUND

    return query_jobs(query_filter={'session': session.id, 'status':status}, user=user)

@api('/api/sessions/<session>/automate', methods=['POST'], login=True)
def automate_session(session, user=None):
    """
    :type session: cascade.session.Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    if isinstance(request.json, dict):
        if request.json.get('analytics') is not None:
            requested_analytics = request.json['analytics']

            for requested_analytic in requested_analytics:
                analytic = Analytic.objects.with_id(requested_analytic['_id'])
                if analytic:
                    mode = requested_analytic.get('mode', analytic.mode)
                    config = AnalyticConfiguration(analytic=analytic, mode=mode)
                    session.update(add_to_set__state__analytics=config)
                    job = AnalyticJob.update_existing(analytic=analytic, user=user, session=session, mode=mode)
                    job.submit()
            return len(requested_analytics), HTTPStatus.OK

    return 0, HTTPStatus.BAD_REQUEST


@api('/api/sessions/<session>/automate/custom', methods=['POST'], login=True)
def automate_session_custom(session, user=None):
    """
    :type session: cascade.session.Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    if not isinstance(request.json, dict):
        return None, HTTPStatus.BAD_REQUEST

    query = DataModelQuery._from_son(request.json['query'])
    job = CustomQueryJob.update_existing(session=session, event_query=query, user=user)
    job.submit()
    return None, HTTPStatus.OK


@api('/api/sessions/<session>/automate/event/<event>', methods=['POST'], login=True)
def investigate_event(session, event, user=None):
    """
    :type session: cascade.session.Session
    :type user: User
    """
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    event = DataModelEvent.objects.with_id(event)
    if event is None or session.id not in {_.id for _ in event.sessions}:
        return None, HTTPStatus.NOT_FOUND

    job = InvestigateJob.update_existing(session=session, event=event, user=user)
    job.submit()
    return None, HTTPStatus.OK


@api('/api/sessions/<session>/clusters', methods=['GET'], login=True)
def get_clusters(session, user=None):
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND
    return session.get_clusters(), HTTPStatus.OK


@api('/api/sessions/<session>/clusters/hosts', methods=['GET'], login=True)
def get_clusters_host(session, user=None):
    events, _ = session_events(session)
    groups = {}

    def traverse(event, groups):
        group = []
        if groups.get(event.id) is not None:
            return group

        groups[event.id] = 'placeholder'
        group.extend([event])

        for linked_event in chain(event.links, event.reverse_links):
            if linked_event.host == event.host:
                group.extend(traverse(linked_event, groups))

        return tuple(group)

    for event in events:
        if groups.get(event.id) is None:
            group = traverse(event, groups)
            for e in group:
                groups[e.id] = group

    unique_groups = list(set(groups.values()))
    group_indices = {group: i for i, group in enumerate(unique_groups)}

    links = [
        list({
            group_indices[groups[link.id]]
            for event in group
                for link in event.links
                    if groups[link.id] != group
        })

        for group in unique_groups
    ]

    reverse_links = [
        list({
            group_indices[groups[link.id]]
            for event in group
                for link in event.reverse_links
                    if groups[link.id] != group
        })

        for group in unique_groups
    ]

    host_clusters = [{
        'host': unique_groups[i][0].host,
        'events': unique_groups[i],
        'links': links[i],
        'reverse_links': reverse_links[i]
        }
        for i in range(len(unique_groups))
    ]

    return host_clusters, HTTPStatus.OK


@api('/api/sessions/<session>/clusters/attack', methods=['GET'], login=True)
def get_clusters_with_attack(session, user=None):
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    analytics = {_.id: _ for _ in Analytic.objects()}
    clusters = session.get_clusters()

    for cluster in clusters:
        techniques = defaultdict(int)
        tactics = defaultdict(int)
        tuples = defaultdict(int)
        counts = {'tactics': 0, 'techniques': 0}

        for analytic_result in cluster['results']:
            for mapping in analytics[analytic_result.analytic.id].coverage:
                techniques[mapping.technique.id] += 1
                counts['techniques'] += 1
                for tactic in mapping.tactics:
                    tactics[tactic.id] += 1
                    counts['tactics'] += 1
                tech_tuple = mapping.technique.id, tuple(_.id for _ in mapping.tactics)
                tuples[tech_tuple] += 1

        tactic_sets = [tactic_set.id for tactic_set in TacticSet.objects()
                       if set(t.id for t in tactic_set.tactics) <= set(tactics)]

        techniques = [{'technique': technique, 'count': count} for technique, count in techniques.items()]
        tactics = [{'tactic': tactic, 'count': count} for tactic, count in tactics.items()]
        tuples = [{'technique': technique, 'tactics': _tactics, 'count': count}
                  for (technique, _tactics), count in tuples.items()]
        cluster['attack_summary'] = {'techniques': techniques,
                                     'tactics': tactics,
                                     'tuples': tuples,
                                     'tactic_sets': tactic_sets,
                                     'counts': counts}

    return clusters, HTTPStatus.OK


@api('/api/sessions/<session>/export', methods=['GET'], login=True)
def export_session(session, user=None):
    session = Session.objects.with_id(session)
    if not isinstance(session, Session):
        return None, HTTPStatus.NOT_FOUND

    events = DataModelEvent.objects(sessions=session)
    results = AnalyticResult.objects(session=session)

    dump = [
        {'collection': 'data_model_event', 'content': events},
        {'collection': 'analytic_result', 'content': results},
        {'collection': 'session', 'content': [session]}
    ]

    return dump, HTTPStatus.OK


@api('/api/events', methods=['GET'], login=True)
def query_events(user=None):
    """
    :type user: User
    """
    filter = {}
    if request.args.get('session'):
        session = Session.objects.with_id(request.args.get('session'))
        if not session:
            return None, HTTPStatus.NOT_FOUND
        filter['sessions'] = session

    return DataModelEvent.objects(**filter), HTTPStatus.OK


@api('/api/events/<event>', methods=['GET', 'DELETE'], login=True)
def query_event(event, user=None):
    """
    :type event: DataModelEvent
    :type user: users.User
    """
    if request.method == 'GET':
        event = DataModelEvent.objects.with_id(event)
        return event, HTTPStatus.OK

    elif request.method == 'DELETE':
        result = DataModelEvent.objects.with_id(event).delete()
        return None, HTTPStatus.NO_CONTENT


@api('/api/analytics', methods=['GET'], login=False)
def query_analytics(user=None):
    """ :type user: User """
    analytics = list(Analytic.objects)
    if request.args.get('format') in mappings:
        layer = mappings[request.args.get('format')]
        for analytic in analytics:
            if isinstance(analytic, CascadeAnalytic):
                optimized = layer.optimize(analytic.query)
                analytic.query = layer.parse_expression(optimized)
    return analytics, HTTPStatus.OK


@api('/api/analytics', methods=['POST'], login=True)
def submit_analytic(user=None):
    if 'update_many' in request.args:
        if isinstance(request.json, dict) and request.json.get('analytics') is not None:
            count = 0
            for content in request.json['analytics']:
                _id = content.pop('_id', None)
                analytic = Analytic.objects.with_id(_id)
                if analytic is not None:
                    count += analytic.update(**content)

            return Analytic.objects(), HTTPStatus.OK
        return {}, HTTPStatus.BAD_REQUEST

    # creating a new analytic
    else:
        if request.json.get('platform', 'CASCADE') == 'CASCADE':
            analytic = CascadeAnalytic._from_son(request.json)
        else:
            analytic = ExternalAnalytic._from_son(request.json)
        analytic.save()

    return analytic.id, HTTPStatus.OK


@api('/api/configurations/analytics', methods=['GET', 'POST'], login=True)
def query_analytic_configurations(user=None):
    if request.method == 'GET':
        return AnalyticConfigurationList.objects(), HTTPStatus.OK

    elif request.method == 'POST':
        configuration = AnalyticConfigurationList(**request.json)
        configuration.save()
        return configuration.id, HTTPStatus.OK


@api('/api/configurations/analytics/<config_id>', methods=['GET', 'PUT', 'DELETE'], login=True)
def query_analytic_configuration(config_id, user=None):
    config = AnalyticConfigurationList.objects.with_id(config_id)
    if config is None and request.method != 'PUT':
        return None, HTTPStatus.NOT_FOUND

    if request.method == 'GET':
        return config, HTTPStatus.OK

    elif request.method == 'DELETE':
        config.delete()
        return None, HTTPStatus.OK

    elif request.method == 'PUT':
        if config is None:
            config = AnalyticConfigurationList(id=config_id)
        config = config.update(**request.json)
        return config.id, HTTPStatus.OK


@api('/api/query/languages')
def get_languages():
    return list(mappings.keys()), HTTPStatus.OK


@api('/api/query/parse', methods=['POST'])
def make_query():
    try:
        query = parser.generate_query(request.json['query'])
        event_type, action = DataModelQueryLayer.get_data_model(query)
        return {'object': event_type.object_name, 'action': action, 'query': query}, HTTPStatus.OK

    except InvalidFieldError:
        return {'error': 'Invalid Data Model field in query'}, HTTPStatus.BAD_REQUEST

    except InvalidActionError:
        return {'error': 'Invalid Data Model action in query'}, HTTPStatus.BAD_REQUEST

    except InvalidObjectError:
        return {'error': 'Invalid Data Model object in query'}, HTTPStatus.BAD_REQUEST

    except parser.ParserError:
        return {'error': 'Unable to parse query'}, HTTPStatus.BAD_REQUEST


@api('/api/query/lift', methods=['POST'])
def unparse_query():
    # todo: convert from json into objects
    # query = request.json['query']
    analytic_id = request.args['analytic']
    analytic = Analytic.objects.with_id(analytic_id)
    if isinstance(analytic, ExternalAnalytic):
        return None, HTTPStatus.BAD_REQUEST
    query = parser.lift_query(analytic)
    return {'text': query}, HTTPStatus.OK


@api('/api/analytics/<analytic>/lift', methods=['GET'])
def unparse_analytic(analytic):
    # todo: convert from json into objects
    # query = request.json['query']
    analytic = Analytic.objects.with_id(analytic)
    if isinstance(analytic, ExternalAnalytic):
        return None, HTTPStatus.BAD_REQUEST
    query = parser.lift_query(analytic)
    return {'text': query}, HTTPStatus.OK


@api('/api/analytics/<analytic>', methods=['GET'], login=False)
def query_analytic(analytic, user=None):
    analytic_id = analytic
    analytic = Analytic.objects.with_id(analytic_id)

    if analytic is None:
        return None, HTTPStatus.NOT_FOUND

    return analytic, HTTPStatus.OK


@api('/api/analytics/<analytic>', methods=['PUT', 'DELETE'], login=True)
def update_analytic(analytic, user=None):
    analytic_id = analytic
    analytic = Analytic.objects.with_id(analytic_id)

    if request.method == 'PUT':
        if not analytic:
            analytic = Analytic(id=analytic_id)
        analytic.update(**request.json)
        return analytic.id, HTTPStatus.OK

    elif request.method == 'DELETE':
        if analytic is None:
            return None, HTTPStatus.NOT_FOUND

        # must delete all references of the analytic first
        AnalyticBaseline.objects(analytic=analytic).delete()
        AnalyticResult.objects(analytic=analytic).delete()
        Job.objects(analytic=analytic).delete()

        # then remove it from the session state
        for mode in Analytic.modes:
            config = AnalyticConfiguration(analytic=analytic, mode=mode)
            Session.objects(pull__state__analytics=config)
            AnalyticConfigurationList.objects(pull__analytics=config)

        analytic.delete()
        return None, HTTPStatus.OK


@api('/api/tuning', methods=['GET', 'POST'], login=True)
def query_baselines(user=None):
    if request.method == 'GET':
        return AnalyticBaseline.objects(), HTTPStatus.OK

    elif request.method == 'POST':
        if isinstance(request.json, dict):
            if request.json.get('analytics') is not None and request.json.get('time') is not None:
                requested_analytics = request.json.get('analytics', [])
                time_range = DateRange.get_range(request.json['time'])

                count = 0
                for requested_analytic in requested_analytics:
                    analytic_id = requested_analytic.pop('_id', requested_analytic.get('id'))
                    analytic = Analytic.objects.with_id(analytic_id)

                    if analytic is None:
                        continue

                    job = TuningJob.update_existing(analytic=analytic, range=time_range, user=user)
                    job.submit()
                    count += 1
                return count, HTTPStatus.OK
    return [], HTTPStatus.BAD_REQUEST


@api('/api/tuning/<analytic>', methods=['GET', 'POST', 'PUT'], login=True, endpoint='query_baseline_alternate')
@api('/api/analytics/<analytic>/tuning', methods=['GET', 'PUT', 'POST'], login=True)
def query_baseline(analytic, user=None):
    analytic = Analytic.objects.with_id(analytic)
    baseline = AnalyticBaseline.objects(analytic=analytic).first()

    if analytic is None or baseline is None:
        return {}, HTTPStatus.NOT_FOUND

    if request.method == 'GET':
        return baseline, HTTPStatus.OK

    elif request.method == 'POST':
        if 'reset' in request.args and request.method in ('GET', 'POST'):
            baseline.reset()
            baseline.save()
            return baseline, HTTPStatus.OK

        elif 'optimize' in request.args:
            baseline.optimize()
            baseline.save()
            return baseline, HTTPStatus.OK

        elif 'retrain' in request.args:
            events = baseline.recover_events()
            if request.json.get('keys'):
                baseline.keys = list(ClusterKey(name=_['name'], status=_['status']) for _ in request.json['keys'])
            baseline.cluster_events(events)
            baseline.save()
            return baseline, HTTPStatus.OK

    elif request.method == 'PUT':
        if 'root' in request.json:
            baseline.modify(root=request.json['root'])

        if 'keys' in request.json:
            baseline.cluster_events(baseline.recover_events(), keys=request.json['keys'])
            baseline.save()
        return baseline, HTTPStatus.OK

    return None, HTTPStatus.BAD_REQUEST


@api('/api/tuning/<analytic>/events', methods=['GET'], login=True,  endpoint='query_baseline_events_alternate')
@api('/api/analytics/<analytic>/tuning/events', methods=['GET'], login=True)
def query_baseline_events(analytic, user=None):
    analytic = Analytic.objects.with_id(analytic)
    baseline = AnalyticBaseline.objects(analytic=analytic).first()

    if analytic is None or baseline is None:
        return {}, HTTPStatus.NOT_FOUND

    if request.method == 'GET':
        return [{'cluster': cluster, 'size': cluster.pop('_size', 1)}
                for cluster in baseline.recover_events()], HTTPStatus.OK


@api('/api/data_model/objects', methods=['GET'])
def query_objects(user=None):
    return [
        {'name': obj.object_name,
         'actions': obj.actions,
         'fields': obj.fields,
         '_class': obj.__name__
         } for name, obj in sorted(event_lookup.items())
    ], HTTPStatus.OK


def convert_pivot(pivot_info):
    dict_info = {
        'name': pivot_info.name,
        '_title': ''.join(_.title() for _ in pivot_info.name.split('_')),
        'source': {
            '_class': pivot_info.source_class.__name__,
            'name': pivot_info.source_class.object_name,
            'actions': pivot_info.source_actions
        },
        'target': {
            '_class': pivot_info.dest_class.__name__,
            'name': pivot_info.dest_class.object_name,
            'actions': pivot_info.dest_actions
        },
        'reverse': pivot_info.reverse,
        'depends': pivot_info.depends,
        'abstract': pivot_info.abstract
    }
    if pivot_info.reverse:
        dict_info['inverse'] = pivot_info.inverse
    return dict_info


@api('/api/data_model/pivots', methods=['GET'])
def query_pivots(user=None):
    return [convert_pivot(pivot) for pivot in pivot_lookup.values()], HTTPStatus.OK


@api('/api/data_model', methods=['GET'])
def query_data_model():
    pivots, pivot_status = query_pivots()
    objects, object_status = query_objects()

    return {
        'objects': objects,
        'pivots': pivots
    }, HTTPStatus.OK


@api('/api/utils/upload', methods=['POST'], login=True)
def upload_data(user=None):
    f = request.files['file']
    bson_data = bson.json_util.loads(f.stream.read())
    utils.import_database(bson_data)
    return {'message': "Session imported successfully"}, HTTPStatus.OK


@flask_app.route('/api/sessions/<session>/stream')
def stream(session, user=None):
    # Testing for HTTP SSE
    session = Session.objects.with_id(session)
    if not session:
        return None, HTTPStatus.NOT_FOUND

    def handle_stream(handle):
        for reason, event in handle:
            yield 'event: %s\ndata: %s\n\n' % (reason, event)
    return Response(handle_stream(session.stream()), mimetype="text/event-stream")
