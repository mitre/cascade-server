# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import math
import json
import datetime
import dateutil
import logging


from mongoengine import StringField, IntField
import splunklib.client as client
from splunklib.results import ResultsReader, Message

from app.cascade.database import EncryptedStringField
from app.cascade.query_layers.base import DataModelQueryLayer, DatabaseInfo, UserDatabaseInfo, QueryError
from app.cascade.data_model.query import Operation, Sequence, QueryComparators, FieldComparators, FieldComparison
from app.cascade.data_model.event import DataModelQuery
from app.cascade.analytics import CascadeAnalytic, AnalyticReference, ExternalAnalytic, Analytic
from app.utils import AuthenticationError

logger = logging.getLogger(__name__)


class SplunkInfo(DatabaseInfo):
    database_type = "Splunk"
    host = StringField()
    port = IntField(default=8089)
    app = StringField()

    def add_user(self, *args, **kwargs):
        login = SplunkSearchLogin(database=self, *args, **kwargs)
        return login


class SplunkSearchLogin(UserDatabaseInfo):
    username = StringField()
    password = EncryptedStringField()

    def __init__(self, *args, **kwargs):
        super(SplunkSearchLogin, self).__init__(*args, **kwargs)
        self.layer = None
        """:type: SplunkAbstraction"""
        # self.password = kwargs['password']

    def login(self):
        try:
            layer = SplunkAbstraction(
                host=self.database.host,
                port=self.database.port,
                app=self.database.app,
                username=self.username,
                password=self.password,
                # token=self.token
              )
            self.layer = layer
            return self.layer
        except client.AuthenticationError:
            raise AuthenticationError


class SplunkAbstraction(DataModelQueryLayer):
    platform = "Splunk"
    """
    :type _client: splunklib.client.Service
    """
    _epoch = datetime.datetime(1970, 1, 1)
    _time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    comparator_lookup = {
        QueryComparators.And: "AND",
        QueryComparators.Not: "NOT",
        QueryComparators.Or: "OR",
        FieldComparators.GreaterThan: ">",
        FieldComparators.GreaterThanOrEqual: ">=",
        FieldComparators.LessThan: ">",
        FieldComparators.LessThanOrEqual: "=",
        FieldComparators.Equals: "=",
        FieldComparators.NotEquals: "!=",
        FieldComparators.WildCard: "="
    }

    def __init__(self, host, port, app=None, **kwargs):
        self._default_args = {}
        self._client = client.connect(host=host, port=port, app=app, autologin=True, **kwargs)
        # TODO: enforce this!
        self._search_limit = max(int(role.srchJobsQuota) for role in self._client.roles)
        self._active_searches = 0

    def _parse_results(self, handle):
        """ Wraps output from Splunk searches with the Splunk ResultsReader.
        Splunk typically retrieves events debug statements, errors through the same stream.
        Debug/Info messages will be displayed and actual results

        :param handle: Splunk search job generator
        """
        result_reader = ResultsReader(handle)
        for result in result_reader:

            # Diagnostic messages may be returned in the results
            if isinstance(result, Message):
                logger.debug('[{}] {}'.format(result.type, result.message))

            # Normal events are returned as dicts
            elif isinstance(result, dict):
                result = dict(result)
                if '_time' in result:
                    result['_time'] = SplunkAbstraction._to_datetime(result['_time'])
                yield {
                    'time': result['_time'] if '_time' in result else '',
                    'metadata': {k: v for k, v in result.items() if k.startswith('_')},
                    'state': {k: v for k, v in result.items() if not k.startswith('_')}
                }

            else:
                logger.warning('Unknown result type in _parse_results: {}'.format(result))

        assert result_reader.is_preview is False

    def _export(self, query, **kwargs):
        logger.info('[SPLUNK] export {} {} {} {}'.format(kwargs.get('earliest_time'), kwargs.get('latest_time'), query, '\n'))
        return self._parse_results(self._client.jobs.export(query, enable_lookups=True, **kwargs))

        # This is a big error that can't be shrugged over like this and needs to seriously be re-implemented
        # try:
        #     return self._parse_results(self._client.jobs.export(query, enable_lookups=True, **kwargs))
        # except urllib2.HTTPError as ex:
        #    logger.warning('[SPLUNK] HTTP Error in query. probably max concurrent searches.')

    def _oneshot(self, query, **kwargs):
        logger.info('[SPLUNK] oneshot {} {} {} {}'.format(kwargs.get('earliest_time'), kwargs.get('latest_time'), query, '\n'))
        return self._parse_results(self._client.jobs.oneshot(query, enable_lookups=True, **kwargs))

    @classmethod
    def parse_expression(cls, expression, scoped=False):

        if isinstance(expression, (CascadeAnalytic, AnalyticReference)):
            return cls.parse_expression(expression.query, scoped=scoped)

        if isinstance(expression, ExternalAnalytic):
            if expression.platform != 'Splunk':
                raise NotImplementedError()
            else:
                return '| savedsearch "{}"'.format(expression.query_name)

        elif isinstance(expression, DataModelQuery):
            if scoped:
                return cls.parse_expression(expression.query, scoped=True)
            else:
                search = 'tag=dm-{}'.format(expression.object.object_name)
                if expression.action:
                    search += '-{}'.format(expression.action)
                if expression.query:
                    search += ' {}'.format(cls.parse_expression(expression.query, scoped=True))
                return search

        elif isinstance(expression, FieldComparison):
            if expression.comparator is FieldComparators.RegEx:
                raise NotImplementedError("RegEx is not yet implemented in Splunk!")
            return '{}{}{}'.format(
                expression.field, cls.comparator_lookup[expression.comparator], cls._escape_value(expression.value)
            )

        elif isinstance(expression, Operation):
            if expression.operator is QueryComparators.Not:
                return 'NOT ({})'.format(cls.parse_expression(expression.terms[0], scoped=scoped))

            else:
                return '( {} )'.format(' {} '.format(cls.comparator_lookup[expression.operator]).join(
                    cls.parse_expression(term, scoped=scoped) for term in expression.terms
                ))

        elif isinstance(expression, Sequence):
            # For now, assume they can always be done as a multi search
            output = "| multisearch "

            # Rename the original fields
            for i, q in enumerate(expression.queries):
                output += '[\n search {}'.format(cls.parse_expression(q, scoped=scoped))
                output += '\n| rename ' + ', '.join('{} AS term_{}_{}'.format(f, i, f) for f in q.fields())

                output += '\n| eval term_{}_time=_time'.format(i)
                output += '\n| eval term_number={}'.format(i)
                for j, field_set in enumerate(expression.field_sets):
                    for query_term in field_set:
                        if query_term.query is q:
                            output += '\n| eval transact_{}={}'.format(j, query_term.field)
                output += '] '

            # Now transact the two on the fields that match
            output += '\n| transaction '
            output += ' '.join('transact_{}'.format(i) for i in range(len(expression.field_sets)))

            # Parse out the original args
            if expression.max_time is not None:
                output += ' maxspan={}'.format(expression.max_time)

            output += ' maxevents=true'
            output += ' startswith=(term_number=0) endswith=(term_number={})'.format(len(expression.queries)-1)

            if expression.min_time > 0:
                output += '| where duration > {}'.format(expression.min_time)

            return output
        else:
            raise TypeError("Unknown query type {}".format(type(expression)))

    @staticmethod
    def _escape_value(value):
        if isinstance(value, str):
            # json already does all the escaping for me
            escaped_value = json.dumps(value)
            return escaped_value
        else:
            return value

    @staticmethod
    def _to_datetime(splunk_date):
        """
        :param splunk_date: Splunk time string in a format like 2015-10-10 09:19:46.000 EDT
        :rtype datetime.datetime
        """
        dt = dateutil.parser.parse(splunk_date)
        return dt

    @staticmethod
    def _from_datetime(dt):
        if isinstance(dt, datetime.datetime):
            return dt.strftime(SplunkAbstraction._time_format)

        elif isinstance(dt, datetime.timedelta):
            seconds = int(math.floor(dt.total_seconds()))
            return 'now' if seconds == 0 else '{}s'.format(seconds)
        else:
            return dt

    def _splunk_args(self, search, kwargs):
        splunk_args = self._default_args.copy()
        kwargs.pop('session', None)

        if isinstance(kwargs.get('start'), (datetime.datetime, datetime.timedelta)):
            splunk_args['earliest_time'] = self._from_datetime(kwargs['start'])

        if isinstance(kwargs.get('end'), (datetime.datetime, datetime.timedelta)):
            splunk_args['latest_time'] = self._from_datetime(kwargs['end'])

        if kwargs.get('first') is not None:
            search += " | tail {}".format(kwargs['first'])

        if kwargs.get('last') is not None:
            search += " | head {}".format(kwargs['last'])

        # Force splunk time formats
        splunk_args['output_time_format'] = self._time_format
        # splunk_args['time_format'] = self._time_format

        return search, splunk_args

    def query(self, expression, **kwargs):
        search, kwargs = self._splunk_args(self.parse_expression(self.optimize(expression)), kwargs)

        # Apparently the splunk api doesn't always return all aliased/calculated fields
        # This should help
        query_function = self._export if isinstance(expression, Analytic) else self._oneshot

        try:
            event_type, action = self.get_data_model(expression)
            fields = event_type.fields
        except QueryError:
            fields = ['*']

        search = '{} | fields {}'.format(search, ' '.join(fields))
        if not isinstance(expression, ExternalAnalytic):
            search = 'search {}'.format(search)

        return query_function(search, **kwargs)

    @property
    def external_analytics(self):
        for saved_search in self._client.saved_searches:
            if saved_search.name.startswith('CAR-'):
                yield saved_search.name, saved_search.search

    @classmethod
    def optimize(cls, expression, dereference=False):
        return super(SplunkAbstraction, cls).optimize(expression, dereference=True)
