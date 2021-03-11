# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import datetime
import re

from app.cascade.data_model.query import FieldQuery, FieldComparison, FieldComparators, Operation, QueryTerm, QueryComparators
from app.cascade.data_model.event import DataModelEvent, DataModelQuery
from app.cascade.query_layers.base import DataModelQueryLayer
from app.cascade.analytics import AnalyticReference, CascadeAnalytic, ExternalAnalytic


class MongoQuery(dict):
    pass


class MongoAbstraction(DataModelQueryLayer):
    platform = "Mongo"

    comparator_lookup = {
        QueryComparators.And: "$and",
        QueryComparators.Not: "$not",
        QueryComparators.Or: "$or",
        FieldComparators.GreaterThan: "$gt",
        FieldComparators.GreaterThanOrEqual: "$gte",
        FieldComparators.LessThan: "$le",
        FieldComparators.LessThanOrEqual: "$lte",
        # FieldComparators.Equals: "$eq",
        FieldComparators.NotEquals: "$ne",
        FieldComparators.WildCard: "$regex",
        FieldComparators.Contains: "$regex",
    }

    def external_analytics(self):
        raise NotImplementedError

    @classmethod
    def parse_expression(cls, expression, prefix=''):
        """ Parse through the query expression
        :param QueryTerm expression:  The semantic tree of query operations
        :rtype dict
        """
        if isinstance(expression, MongoQuery):
            return expression
        elif isinstance(expression, DataModelQuery):
            return cls.parse_expression(expression.query, prefix='state.')
        elif isinstance(expression, CascadeAnalytic):
            return cls.parse_expression(expression.query, prefix=prefix)
        elif isinstance(expression, AnalyticReference):
            return cls.parse_expression(expression.query, prefix=prefix)
        elif isinstance(expression, Operation):
            key = cls.comparator_lookup[expression.operator]
            return MongoQuery({key: [cls.parse_expression(term, prefix=prefix) for term in expression.terms]})

        elif isinstance(expression, FieldComparison):
            value = expression.value
            if expression.comparator is FieldComparators.Equals:
                return MongoQuery({prefix + expression.field: value})

            if expression.comparator is FieldComparators.WildCard:
                value = re.escape(value).replace(r'\*', '.*')
            elif expression.comparator is FieldComparators.Contains:
                value = ".*{}.*".format(re.escape(value))

            return MongoQuery({"{}{}".format(prefix, expression.field): {cls.comparator_lookup[expression.comparator]: value}})

        else:
            raise ValueError("Unable to parse expression {}".format(expression))

    def query(self, expression, start=None, end=None, session=None, **kwargs):
        if isinstance(expression, ExternalAnalytic):
            raise NotImplementedError()

        event_class, action = self.get_data_model(expression)
        field_query = self.parse_expression(expression)
        context_expression = (FieldQuery('action') == action)

        if session is not None:
            context_expression &= (FieldQuery('sessions') == session.id)

        else:
            if start is not None:
                if isinstance(start, datetime.datetime):
                    context_expression &= (FieldQuery('time') >= start)
            if end is not None:
                if isinstance(end, datetime.datetime):
                    context_expression &= (FieldQuery('time') <= end)

        context_query = self.parse_expression(context_expression)

        # mongo doesn't handle case insensitivity, so we actually have to make inefficient queries and perform
        # it client side
        # cursor = event_class.objects(__raw__={"$and": [field_query, context_query]})
        cursor = event_class.objects(__raw__=context_query)

        def wrap_cursor(input_cursor):
            for event in input_cursor:
                state = dict(event.state.to_mongo())
                if expression.compare(state):
                    yield {'id': event.id, 'uuid': event.uuid, 'state': state, 'time': event.time}
        return wrap_cursor(cursor)

    @classmethod
    def optimize(cls, expression, dereference=False):
        return super(MongoAbstraction, cls).optimize(expression, dereference=True)

