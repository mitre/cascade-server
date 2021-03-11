# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import logging
import datetime

import dateutil.tz
import dateutil.parser
from mongoengine import StringField, ListField, IntField, BooleanField
from elasticsearch import Elasticsearch

from app.cascade.query_layers.base import DataModelQueryLayer, DatabaseInfo, UserDatabaseInfo
from app.cascade.data_model.query import Operation, Sequence, FieldComparators, FieldComparison, QueryComparators, FieldQuery
from app.cascade.data_model.event import DataModelQuery
from app.cascade.analytics import AnalyticReference, CascadeAnalytic, ExternalAnalytic
from app.cascade.database import EncryptedStringField


logger = logging.getLogger(__name__)


class ElasticSearchInfo(DatabaseInfo):
    database_type = "ElasticSearch"
    hosts = ListField(StringField())
    port = IntField(default=9200)
    use_ssl = BooleanField(default=False)
    verify_certs = BooleanField(default=True)

    def add_user(self, *args, **kwargs):
        return ElasticSearchLogin(database=self, *args, **kwargs)


class ElasticSearchLogin(UserDatabaseInfo):
    username = StringField()
    password = EncryptedStringField()

    def __init__(self, *args, **kwargs):
        super(ElasticSearchLogin, self).__init__(*args, **kwargs)
        self.layer = None
        """:type: ElasticAbstraction"""

    def login(self):
        self.layer = ElasticAbstraction(
            username=self.username,
            password=self.password,
            hosts=self.database.hosts,
            port=self.database.port,
            use_ssl=self.database.use_ssl,
            verify_certs=self.database.verify_certs
          )
        return self.layer


class ElasticAbstraction(DataModelQueryLayer):
    platform = "ElasticSearch"

    comparator_lookup = {
        QueryComparators.And: "AND",
        QueryComparators.Not: "NOT",
        QueryComparators.Or: "OR",
        FieldComparators.GreaterThan: ":>",
        FieldComparators.GreaterThanOrEqual: ":>=",
        FieldComparators.LessThan: ":<",
        FieldComparators.LessThanOrEqual: ":<=",
        FieldComparators.Equals: ":",
        FieldComparators.NotEquals: "!=",
        FieldComparators.WildCard: ":",
        FieldComparators.Contains: ":"
    }

    def __init__(self, username=None, password=None, **kwargs):
        if username is not None and password is not None:
            kwargs['http_auth'] = username, password
        self._es = Elasticsearch(timeout=300, maxsize=4096, **kwargs)

    @staticmethod
    def wrap_results(results):
        for result in results['hits']['hits']:
            yield result['_source']

    @staticmethod
    def to_datetime(time_string, format_string="%Y-%m-%dT%H:%M:%S.%fZ"):
        # Format string assumes UTC
        return dateutil.parser.parse(time_string)

    @staticmethod
    def update_time(start, end):
        utc_now = datetime.datetime.now(tz=dateutil.tz.tzutc())

        if isinstance(start, datetime.timedelta):
            start = utc_now + start

        if isinstance(end, datetime.timedelta) and end.total_seconds() != 0:
            end = utc_now + end

        # Datetime will already be in UTC format
        if isinstance(start, datetime.datetime):
            start = start.isoformat()

        if isinstance(end, datetime.datetime):
            end = end.isoformat()
        elif start:
            end = "now"

        return start, end

    def _query(self, query_string, start=None, end=None, **kwargs):
        start, end = self.update_time(start, end)
        if start is not None:
            query_string = "@timestamp:[{} TO {}] AND ({})".format(start, end, query_string, **kwargs)

        return self._query_time(query_string, **kwargs)

    def _query_time(self, query_string, **kwargs):
        last = kwargs.pop('last', None)
        first = kwargs.pop('first', None)

        logger.info('[ELASTICSEARCH] {}'.format(query_string))
        query_dict = {"query": {"query_string": {"query": query_string}}}
        # TODO: Use scroll here instead.
        results = self._es.search(body=query_dict, size=10000, **kwargs)
        if results.get('failed') or results.get('timed_out'):
            # set a breakpoint or do something
            logger.warning('[ELASTICSEARCH] problem running query')
            pass
        hits = results['hits']['hits']
        """:type: list"""

        # Spit these out in chronological order
        hits.sort(key=lambda x: x['_source']['@timestamp'])

        if last:
            last = min(len(hits), last)
            hits = hits[-last:]

        elif first is not None:
            first = min(len(hits), first)
            hits = hits[:first]

        for hit in hits:
            result = hit['_source']
            fields = result['data_model']['fields']
            # to_datetime takes care of timezone info
            time = self.to_datetime(result['@timestamp'])
            if fields.get('HASH') or fields.get('hash'):
                for name, value in fields.get('hash', fields.get('HASH', {})).items():
                    fields['{}_hash'.format(name.lower())] = value
            yield {'time': time, 'state': fields}

    @staticmethod
    def _escape_value(value):
        if isinstance(value, str):
            return '{}'.format(value.replace('\\', '\\\\').
                               replace('\"', '\\"').
                               replace('(', '\\(').
                               replace(')', '\\)').
                               replace(':', '\\:').
                               replace('/', '\\/').
                               replace(' ', '\\ '))
        else:
            return value

    @classmethod
    def parse_expression(cls, expression):
        optimized = cls.optimize(expression)
        return cls._parse_expression(optimized)

    @classmethod
    def _parse_expression(cls, expression, prefix=''):
        if isinstance(expression, (CascadeAnalytic, AnalyticReference)):
            return cls._parse_expression(expression.query, prefix=prefix)

        if isinstance(expression, DataModelQuery):
            if len(prefix):
                return cls._parse_expression(expression.query, prefix='data_model.fields.')
            else:
                return '{} AND {} AND (\n    {}\n)'.format(
                    cls._parse_expression(FieldQuery('data_model.object') == expression.object.object_name),
                    cls._parse_expression(FieldQuery('data_model.action') == expression.action),
                    cls._parse_expression(expression.query, prefix='data_model.fields.')
                )

        elif isinstance(expression, FieldComparison):
            # Elastic search doesn't handle field != value queries, so have to negate field == value
            if expression.comparator is FieldComparators.NotEquals:
                return 'NOT {}'.format(cls._parse_expression(FieldQuery(expression.field) == expression.value), prefix=prefix)

            return '{}{}{}'.format(
                prefix + expression.field,
                cls.comparator_lookup[expression.comparator],
                cls._escape_value(expression.value)
            )

        elif isinstance(expression, Operation):
            if expression.operator is QueryComparators.Not:
                return ('{}' if isinstance(expression.terms[0], FieldComparison) else '{} ({})').format(
                                        cls.comparator_lookup[QueryComparators.Not],
                                        cls._parse_expression(expression.terms[0], prefix=prefix))
            else:
                return ' {} '.format(cls.comparator_lookup[expression.operator]).join(
                    ('({})' if isinstance(term, Operation) else '{}').format(
                        cls._parse_expression(term, prefix=prefix)
                    ) for term in expression.terms
                )

        elif isinstance(expression, Sequence):
            raise NotImplementedError()

        else:
            raise TypeError("Unknown expression type {}".format(type(expression)))

    def query(self, expression, start=None, end=None, session=None, **kwargs):
        if isinstance(expression, ExternalAnalytic):
            raise NotImplementedError

        expression = self.optimize(expression)
        lucene_query = self.parse_expression(expression)
        # The hardcoded wildcard below will cause all elasticsearch indices to be searched; specifying
        # a more specific pattern will significantly increase performance.
        results = self._query(lucene_query, index='*', start=start, end=end, **kwargs)

        for result in results:
            if isinstance(expression, DataModelQuery):
                result['state'] = {k: v for k, v in result['state'].items() if k in expression.object.fields}
            yield result

    @property
    def external_analytics(self):
        raise NotImplementedError

    @classmethod
    def optimize(cls, expression, dereference=False):
        return super(ElasticAbstraction, cls).optimize(expression, dereference=True)

