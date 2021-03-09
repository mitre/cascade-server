# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

import re
from enum import Enum

from mongoengine.document import EmbeddedDocument
from mongoengine.fields import EmbeddedDocumentField, StringField, DynamicField, ListField


class QueryComparators(Enum):
    (
        Or,
        And,
        Not,
    ) = range(1, 4)


class FieldComparators(Enum):
    (
        RegEx,
        WildCard,
        Equals,
        GreaterThan,
        GreaterThanOrEqual,
        LessThan,
        LessThanOrEqual,
        NotEquals,
        Contains
    ) = range(1, 10)


class QueryTerm(object):
    """ This base class makes the bitwise operators available, so that a compound query term can be
    created by a series of query terms and operators. This makes a more dynamic pythonic query language
    that will make it easier to be

        example:
            a = QueryTerm(...)
            b = QueryTerm(...)
            a & b <-> Operation(a, b, operator=Comparators.And)

    """
    def operation(self, other=None, operator=None):
        """ Perform an operation on one or more multiple QueryTerm objects. An object of the class
        Operator will be returned, or the entire operation will continue to be a data model query,
        if all input objects share the same Data Model object and action.


        :type other: QueryTerm
        :param operator: one of the valid operators defined in Operation (AND, OR, NOT)
        :rtype QueryTerm
        """
        terms = [self]
        if other is not None and operator is not EmptyQuery:
            terms.append(other)
        return Operation(terms, operator=operator)

    def __or__(self, other):
        return self.operation(other, operator=QueryComparators.Or)

    def __and__(self, other):
        return self.operation(other, operator=QueryComparators.And)

    def __invert__(self):
        return self.operation(operator=QueryComparators.Not)

    def get_fields(self):
        return set()

    # Current casuing a bug with jinja2
    # def __getitem__(self, field):
    #    return FieldQuery(field)

    def prep_value(self):
        return self

    def compare(self, event):
        raise NotImplementedError

    def __contains__(self, item):
        return self.compare(item)


class EmbeddedQueryTerm(QueryTerm, EmbeddedDocument):
    meta = {'allow_inheritance': True}


class FieldQuery(object):
    def __init__(self, field):
        """
        :type field: str
        """
        self.field = field

    def __eq__(self, other):
        if isinstance(other, WildCard):
            return self.wildcard(other)
        elif isinstance(other, RegEx):
            return self.regex(other)
        return FieldComparison(self.field, other, comparator=FieldComparators.Equals)

    def __ne__(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.NotEquals)

    def __gt__(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.GreaterThan)

    def __ge__(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.GreaterThanOrEqual)

    def __lt__(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.LessThan)

    def __le__(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.LessThanOrEqual)

    def regex(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.RegEx)

    def wildcard(self, other):
        return FieldComparison(self.field, other, comparator=FieldComparators.WildCard)

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.field)

    __str__ = __repr__


class CompareString(object):
    comparator = None

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '{}({}, {})'.format(type(self).__name__, self.comparator, repr(self.value))

    __str__ = __repr__

    def compare(self, field):
        assert isinstance(self.comparator, FieldComparators)
        return FieldComparison(field, self.value, comparator=self.comparator)


class FieldComparison(EmbeddedQueryTerm):
    field = StringField()
    value = DynamicField()
    string_comparator = StringField(db_field='comparator')

    def __init__(self, field, value, comparator=None, **kwargs):
        if comparator is not None:
            self.comparator = comparator
            kwargs['string_comparator'] = str(comparator.name)
        super(FieldComparison, self).__init__(field=field, value=value, **kwargs)
        if comparator is None:
            self.comparator = FieldComparators[self.string_comparator]

    def compare(self, event):
        event_value = event.get(self.field)
        value = self.value

        # Cast the value to have the proper type so comparisons will work
        if isinstance(value, (int, float)) and not isinstance(event_value, (int, float)):
            try:
                event_value = type(value)(event_value)
            except ValueError as e:
                return False

        elif isinstance(value, basestring) and not isinstance(event_value, basestring):
            event_value = type(value)(event_value)

        if isinstance(event_value, basestring) and isinstance(value, basestring):
            event_value = event_value.lower()
            value = value.lower()

        if self.comparator == FieldComparators.Equals:
            return event_value == value
        elif self.comparator == FieldComparators.NotEquals:
            return event_value != value
        elif self.comparator == FieldComparators.Contains:
            return event_value in value
        elif self.comparator == FieldComparators.GreaterThan:
            return event_value > value
        elif self.comparator == FieldComparators.GreaterThanOrEqual:
            return event_value >= value
        elif self.comparator == FieldComparators.LessThan:
            return event_value < value
        elif self.comparator == FieldComparators.LessThanOrEqual:
            return event_value <= value
        elif self.comparator == FieldComparators.WildCard:
            regex = re.escape(value).replace(r'\*', '.*')
            return re.match(regex, event_value) is not None
        elif self.comparator == FieldComparators.RegEx:
            return re.match(value, event_value) is not None
        else:
            raise NotImplementedError

    def get_fields(self):
        return {self.field}

    def __repr__(self):
        return '{}({}, {}, {})'.format(type(self).__name__, repr(self.field), self.comparator, repr(self.value))

    __str__ = __repr__


class RegEx(CompareString):
    comparator = FieldComparators.RegEx


class WildCard(CompareString):
    comparator = FieldComparators.WildCard


class NotEquals(CompareString):
    comparator = FieldComparators.NotEquals


# @serializes("EmptyQuery")
class EmptyQueryClass(EmbeddedQueryTerm):
    @staticmethod
    def get_value(value):
        return value

    def compare(self, event):
        return True

    __or__ = get_value
    __and__ = get_value


EmptyQuery = EmptyQueryClass()


# @serializes("operation")
class Operation(EmbeddedQueryTerm):
    """ An Operation performs some type of operation (so far only boolean: AND, OR, NOT) on multiple query terms to
    build a compound query. There is no implementation yet for more sophisticated mappings, such as SQL join,
    Splunk transaction, map, etc.

    :param QueryComparators operator: The abstract operation to be performed on the input expression(s)
    :param List[QueryTerm] terms: A list of all of the terms joined by the operator
    """
    string_operator = StringField(db_field='operator')
    terms = ListField(EmbeddedDocumentField(EmbeddedQueryTerm))

    def __init__(self, terms, operator=None, **kwargs):
        """
        :type terms: List[QueryTerm]
        :type operator: QueryComparators
        """
        kwargs["terms"] = list(term.prep_value() for term in terms)

        if operator is not None:
            kwargs['string_operator'] = operator.name
            self.operator = operator

        super(Operation, self).__init__(**kwargs)
        if operator is None:
            self.operator = QueryComparators[self.string_operator]

    def compare(self, event):
        if self.operator == QueryComparators.And:
            return all(term.compare(event) for term in self.terms)
        elif self.operator == QueryComparators.Or:
            return any(term.compare(event) for term in self.terms)
        elif self.operator == QueryComparators.Not:
            return not(self.terms[0].compare(event))

    def get_fields(self):
        return {f for term in self.terms for f in term.get_fields()}

    def operation(self, other=None, operator=None):
        # if the operation is with something null ignore it
        if other is None or other is EmptyQuery:
            if operator is self.operator:
                return self
            # but not if the operation is inversion
            else:
                return Operation(terms=[self], operator=operator)

        # if the operators match, then create a new operation and merge them together if possible
        elif operator is self.operator:
            terms = list(self.terms)
            if isinstance(other, Operation) and other.operator is operator:
                terms.extend(other.terms)
            else:
                terms.append(other)
            return Operation(terms=terms, operator=operator)

        else:
            return Operation(terms=[self, other], operator=operator)

    def __repr__(self):
        return '{}(operator={}, terms={})'.format(type(self).__name__, self.string_operator, self.terms)

    __str__ = __repr__


class Sequence(QueryTerm):
    """ A Sequence specifies that a set of events must happen in a certain order.
    A sequence is defined as an ordered list of QueryTerms, and the timing thresholds between
    each event.
    """
    def __init__(self, queries, intervals=None, min_time=0, max_time=None, where=None, field_sets=None):
        """
        :type queries: list[QueryTerm]
        :type intervals: list[int]
        :param min_time: Minimum of number of time in seconds
        :param max_time: Maximum of number of time in seconds
        :type where: QueryTerm
        :type field_sets: list[list[FieldQuery]]
        """
        assert len(queries) > 1

        # If any intervals are defined, then all must be defined. For n events, there are n-1 intervals
        if intervals is not None and (len(queries) != (len(intervals) - 1)):
            raise ValueError("Mismatched timing information. {} events and {}".format(len(queries), len(intervals)))

        self.queries = queries
        self.intervals = intervals
        self.min_time = min_time
        self.max_time = max_time
        self.where = where
        self.field_sets = field_sets

    def __or__(self, other):
        raise NotImplementedError()

    def __and__(self, other):
        raise NotImplementedError()

    def __not__(self):
        raise NotImplementedError()

    def __repr__(self):
        return '{}({}, min_time={}, max_time={}, where={})'.format(
            type(self).__name__,
            self.queries,
            self.min_time, self.max_time,
            self.where
        )

    __str__ = __repr__

