# NOTICE
#
# This software was produced for the U. S. Government
# under Basic Contract No. W15P7T-13-C-A802, and is
# subject to the Rights in Noncommercial Computer Software
# and Noncommercial Computer Software Documentation
# Clause 252.227-7014 (FEB 2012)
#
# (C) 2017 The MITRE Corporation.

from antlr4 import InputStream, ParseTreeWalker, CommonTokenStream

from app.cascade.data_model.language.cqlLexer import cqlLexer
from app.cascade.data_model.language.cqlListener import cqlListener
from app.cascade.data_model.language.cqlParser import cqlParser
from app.cascade.data_model.query import (
    QueryTerm, FieldComparison, FieldComparators, QueryComparators, Operation, FieldQuery
)
from app.cascade.data_model.event import DataModelQuery, InvalidFieldError, InvalidObjectError, InvalidActionError
from app.cascade.analytics import AnalyticReference, Analytic, CascadeAnalytic


class ParserError(ValueError):
    pass


class cqlQueryBuilder(cqlListener):
    field_comparators = {
        '>': FieldComparators.GreaterThan,
        '>=': FieldComparators.GreaterThanOrEqual,
        '<': FieldComparators.LessThan,
        '<=': FieldComparators.LessThanOrEqual,
        '==': FieldComparators.Equals,
        '!=': FieldComparators.NotEquals
    }

    query_comparators = {
        'and': QueryComparators.And,
        'not': QueryComparators.Not,
        'or': QueryComparators.Or,
    }

    field_comp_reverse = {v: k for k, v in field_comparators.items()}
    query_comp_reverse = {v: k for k, v in query_comparators.items()}

    def __init__(self):
        self._stack = []

    def push(self, value):
        self._stack.append(value)

    def pop(self):
        return self._stack.pop()

    def exitField(self, ctx):
        self.push(ctx.getText())

    def exitString(self, ctx):
        # need to replace values and stuff
        self.push(ctx.getText()[1:-1].replace('\\"', '"').replace('\\\\', '\\'))

    def _getID(self, ctx):
        return ctx.ID().getText()

    def _pushID(self, ctx):
        self.push(self._getID(ctx))

    def exitFloatValue(self, ctx):
        self.push(float(ctx.getText()))

    def exitIntValue(self, ctx):
        self.push(int(ctx.getText()))

    def exitRegExQuery(self, ctx):
        value = self.pop()
        key = self.pop()
        self.push(FieldComparison(key, value, FieldComparators.RegEx))

    def exitAndQuery(self, ctx):
        right = self.pop()
        left = self.pop()
        self.push(left & right)

    def exitOrQuery(self, ctx):
        right = self.pop()
        left = self.pop()
        self.push(left | right)

    def exitNotQuery(self, ctx):
        term = self.pop()
        self.push(~term)

    def exitAnalyticReferenceByID(self, ctx):
        self.push(AnalyticReference(analytic=self._getID(ctx)))

    def exitAnalyticReferenceByName(self, ctx):
        analytic_name = self.pop()
        self.push(AnalyticReference.with_name(analytic_name))

    def exitValueComparator(self, ctx):
        self.push(self.field_comparators[ctx.getText()])

    exitEventObject = _pushID
    exitEventAction = _pushID

    def exitDataModelQuery(self, ctx):
        query = self.pop()
        action = self.pop()
        event_type = self.pop()
        self.push(DataModelQuery(object_name=event_type, action=action, query=query))

    def exitValueComparatorQuery(self, ctx):
        value = self.pop()
        comparator = self.pop()
        key = self.pop()
        if isinstance(value, str) and '*' in value:
            wildcard_comparison = FieldComparison(key, value, FieldComparators.WildCard)
            if comparator == FieldComparators.NotEquals:
                wildcard_comparison = ~wildcard_comparison
            self.push(wildcard_comparison)

        else:
            self.push(FieldComparison(key, value, comparator))

    def exitScopedQuery(self, ctx):
        # only exists for ordering, can preserve everything as is
        pass


def generate_query(query_string):
    try:
        lexer = cqlLexer(InputStream(query_string))
        stream = CommonTokenStream(lexer)
        parser = cqlParser(stream)
        builder = cqlQueryBuilder()
        tree = parser.allQueries()
        walker = ParseTreeWalker()
        walker.walk(builder, tree)
        query = builder.pop()
        return query

    except (InvalidFieldError, InvalidActionError, InvalidObjectError) as e:
        raise

    except Exception as e:
        raise ParserError()


def _escape_value(value):
    if isinstance(value, str):
        return '"{}"'.format(value.replace('\\', '\\\\').replace('"', '\\"'))
    else:
        return value


def lift_query(expression):
    # expression = optimize(expression)
    return 'search {}'.format(_lift_query(expression))


def _lift_query(expression):
    comparator_lookup = cqlQueryBuilder.field_comp_reverse
    comparator_lookup.update(cqlQueryBuilder.query_comp_reverse)
    comparator_lookup[FieldComparators.WildCard] = comparator_lookup[FieldComparators.Equals]

    if isinstance(expression, CascadeAnalytic):
        return _lift_query(expression.query)

    elif isinstance(expression, AnalyticReference):
        return 'analytic( "{}" )'.format(expression.analytic.name)

    elif isinstance(expression, DataModelQuery):
        return '{} {} where \n    {}'.format(expression.object.object_name,
                                             expression.action,
                                             _lift_query(expression.query))

    elif isinstance(expression, FieldComparison):
        if expression.comparator is FieldComparators.RegEx:
            return 'match({}, {})'.format(expression.field, _escape_value(expression.value))
        else:
            return '{} {} {}'.format(expression.field,
                                     comparator_lookup[expression.comparator],
                                     _escape_value(expression.value))

    elif isinstance(expression, Operation):
        if expression.operator is QueryComparators.Not:
            return '{} ({})'.format(comparator_lookup[QueryComparators.Not],
                                    _lift_query(expression.terms[0]))
        else:
            # what about wildcard or regex ?

            return ' {} '.format(comparator_lookup[expression.operator]).join(
                ('({})' if isinstance(term, Operation) else '{}').format(
                    _lift_query(term)
                ) for term in expression.terms
            )
    else:
        raise TypeError("Unknown expression type {}".format(type(expression)))

