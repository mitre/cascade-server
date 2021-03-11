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

from mongoengine import Document, StringField, ReferenceField, EmbeddedDocument

from app.cascade.data_model.query import QueryTerm, Operation
from app.cascade.data_model.event import DataModelQuery
from app.cascade.analytics import CascadeAnalytic, AnalyticReference
from app.cascade.data_model.parser import lift_query

logger = logging.getLogger(__name__)


class DatabaseInfo(Document):
    database_type = "BaseDatabase"
    name = StringField(required=True, unique=True)
    meta = {'abstract': False, 'allow_inheritance': True}

    def add_user(self, **kwargs):
        raise NotImplementedError()

    @classmethod
    def get_schemas(cls):
        schemas = []
        for subcls in cls.__subclasses__():
            fields = {k: {'type': type(v).__name__, 'default': (None if hasattr(v.default, '__call__') else v.default)}
                      for k, v in subcls._fields.items()}
            fields.pop('_cls')
            fields.pop('id')
            schemas.append({'_cls': subcls._class_name, 'fields': fields, 'name': subcls.database_type})
        return schemas


class UserDatabaseInfo(EmbeddedDocument):
    meta = {'abstract': True, 'allow_inheritance': True}
    database = ReferenceField(DatabaseInfo)

    def login(self):
        """ :rtype: DataModelQueryLayer """
        raise NotImplementedError

    @classmethod
    def get_schemas(cls):
        return [{'_cls': subcls._class_name,
                 'fields': {k: {'type': type(v).__name__, 'default': v.default} for k, v in subcls._fields.items()},
                 'name': subcls.database_type} for subcls in cls.__subclasses__()]


class QueryError(Exception):
    pass


class DataModelQueryLayer(object):
    _cache_dir = 'cache'
    _missing_cache = False
    platform = 'Data Model AST'

    @classmethod
    def get_data_model(cls, expression):
        """ :return (DataModelEventMeta | DataModelEvent, str): """
        if isinstance(expression, DataModelQuery):
            return expression.object, expression.action
        elif isinstance(expression, (CascadeAnalytic, AnalyticReference)):
            return cls.get_data_model(expression.query)
        elif isinstance(expression, Operation):
            event_type = None
            event_action = None

            for term in expression.terms:
                try:
                    term_object, term_action = cls.get_data_model(term)
                except QueryError:
                    # if there is no term item, then just skip it
                    continue

                if term_object is None and term_action is None:
                    continue
                if (event_type and term_object != event_type) or (event_action and term_action != event_action):
                    raise QueryError("{} mismatch".format(type(DataModelQuery).__name))

                event_type = term_object
                event_action = term_action
            if event_type is None and event_action is None:
                raise QueryError("Unable to identify data model event")
            return event_type, event_action
        else:
            raise QueryError(expression)

    @classmethod
    def optimize(cls, expression, dereference=False):
        try:
            optimized = cls._optimize(expression, dereference=dereference)
        except QueryError:
            return expression

        try:
            event_type, event_action = cls.get_data_model(expression)
            optimized = DataModelQuery(event_type, event_action, query=optimized)
        except QueryError:
            pass
        finally:
            return optimized

    @classmethod
    def _optimize(cls, expression, dereference=False):
        if isinstance(expression, (CascadeAnalytic, AnalyticReference)) and dereference:
            return cls._optimize(expression.query, dereference=dereference)

        if isinstance(expression, DataModelQuery):
            return cls._optimize(expression.query, dereference=dereference)

        elif isinstance(expression, Operation):
            optimized_terms = []

            for term in expression.terms:
                if isinstance(term, Operation) and term.operator == expression.operator:
                    optimized_terms.extend(cls._optimize(term, dereference=dereference).terms)
                else:
                    optimized_terms.append(cls._optimize(term, dereference=dereference))

            return Operation(terms=optimized_terms, operator=expression.operator)
        else:
            return expression

    @classmethod
    def parse_expression(cls, expression, *args, **kwargs):
        return expression

    def query(self, expression, **kwargs):
        """ The query function takes an abstract query over the data model, and fetches the corresponding
        content from the database. This function returns a list of events, which are represented as dictionaries of
        fields, etc.

        :type expression: QueryTerm
        :rtype: list[dict]
        """
        raise NotImplementedError("'query' not supported for {}".format(type(self)))

    @property
    def external_analytics(self):
        """ Returns a list of the analytics provided by this database.
        """
        raise NotImplementedError("'analytics' property not supported for {}".format(type(self)))


class CascadeQueryLayer(DataModelQueryLayer):
    platform = 'Data Model Query Language'

    @classmethod
    def parse_expression(cls, expression, *args, **kwargs):
        return lift_query(expression)
