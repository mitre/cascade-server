# Generated from cql.g4 by ANTLR 4.9.1
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .cqlParser import cqlParser
else:
    from cqlParser import cqlParser

# This class defines a complete listener for a parse tree produced by cqlParser.
class cqlListener(ParseTreeListener):

    # Enter a parse tree produced by cqlParser#floatValue.
    def enterFloatValue(self, ctx:cqlParser.FloatValueContext):
        pass

    # Exit a parse tree produced by cqlParser#floatValue.
    def exitFloatValue(self, ctx:cqlParser.FloatValueContext):
        pass


    # Enter a parse tree produced by cqlParser#intValue.
    def enterIntValue(self, ctx:cqlParser.IntValueContext):
        pass

    # Exit a parse tree produced by cqlParser#intValue.
    def exitIntValue(self, ctx:cqlParser.IntValueContext):
        pass


    # Enter a parse tree produced by cqlParser#number.
    def enterNumber(self, ctx:cqlParser.NumberContext):
        pass

    # Exit a parse tree produced by cqlParser#number.
    def exitNumber(self, ctx:cqlParser.NumberContext):
        pass


    # Enter a parse tree produced by cqlParser#value.
    def enterValue(self, ctx:cqlParser.ValueContext):
        pass

    # Exit a parse tree produced by cqlParser#value.
    def exitValue(self, ctx:cqlParser.ValueContext):
        pass


    # Enter a parse tree produced by cqlParser#field.
    def enterField(self, ctx:cqlParser.FieldContext):
        pass

    # Exit a parse tree produced by cqlParser#field.
    def exitField(self, ctx:cqlParser.FieldContext):
        pass


    # Enter a parse tree produced by cqlParser#allQueries.
    def enterAllQueries(self, ctx:cqlParser.AllQueriesContext):
        pass

    # Exit a parse tree produced by cqlParser#allQueries.
    def exitAllQueries(self, ctx:cqlParser.AllQueriesContext):
        pass


    # Enter a parse tree produced by cqlParser#searchQuery.
    def enterSearchQuery(self, ctx:cqlParser.SearchQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#searchQuery.
    def exitSearchQuery(self, ctx:cqlParser.SearchQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#dataModelQuery.
    def enterDataModelQuery(self, ctx:cqlParser.DataModelQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#dataModelQuery.
    def exitDataModelQuery(self, ctx:cqlParser.DataModelQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#eventObject.
    def enterEventObject(self, ctx:cqlParser.EventObjectContext):
        pass

    # Exit a parse tree produced by cqlParser#eventObject.
    def exitEventObject(self, ctx:cqlParser.EventObjectContext):
        pass


    # Enter a parse tree produced by cqlParser#eventAction.
    def enterEventAction(self, ctx:cqlParser.EventActionContext):
        pass

    # Exit a parse tree produced by cqlParser#eventAction.
    def exitEventAction(self, ctx:cqlParser.EventActionContext):
        pass


    # Enter a parse tree produced by cqlParser#analyticReferenceByID.
    def enterAnalyticReferenceByID(self, ctx:cqlParser.AnalyticReferenceByIDContext):
        pass

    # Exit a parse tree produced by cqlParser#analyticReferenceByID.
    def exitAnalyticReferenceByID(self, ctx:cqlParser.AnalyticReferenceByIDContext):
        pass


    # Enter a parse tree produced by cqlParser#analyticReferenceByName.
    def enterAnalyticReferenceByName(self, ctx:cqlParser.AnalyticReferenceByNameContext):
        pass

    # Exit a parse tree produced by cqlParser#analyticReferenceByName.
    def exitAnalyticReferenceByName(self, ctx:cqlParser.AnalyticReferenceByNameContext):
        pass


    # Enter a parse tree produced by cqlParser#valueComparator.
    def enterValueComparator(self, ctx:cqlParser.ValueComparatorContext):
        pass

    # Exit a parse tree produced by cqlParser#valueComparator.
    def exitValueComparator(self, ctx:cqlParser.ValueComparatorContext):
        pass


    # Enter a parse tree produced by cqlParser#string.
    def enterString(self, ctx:cqlParser.StringContext):
        pass

    # Exit a parse tree produced by cqlParser#string.
    def exitString(self, ctx:cqlParser.StringContext):
        pass


    # Enter a parse tree produced by cqlParser#AnalyticReferenceQuery.
    def enterAnalyticReferenceQuery(self, ctx:cqlParser.AnalyticReferenceQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#AnalyticReferenceQuery.
    def exitAnalyticReferenceQuery(self, ctx:cqlParser.AnalyticReferenceQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#OrQuery.
    def enterOrQuery(self, ctx:cqlParser.OrQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#OrQuery.
    def exitOrQuery(self, ctx:cqlParser.OrQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#NestedDataModelQuery.
    def enterNestedDataModelQuery(self, ctx:cqlParser.NestedDataModelQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#NestedDataModelQuery.
    def exitNestedDataModelQuery(self, ctx:cqlParser.NestedDataModelQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#NotQuery.
    def enterNotQuery(self, ctx:cqlParser.NotQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#NotQuery.
    def exitNotQuery(self, ctx:cqlParser.NotQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#ScopedQuery.
    def enterScopedQuery(self, ctx:cqlParser.ScopedQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#ScopedQuery.
    def exitScopedQuery(self, ctx:cqlParser.ScopedQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#ValueComparatorQuery.
    def enterValueComparatorQuery(self, ctx:cqlParser.ValueComparatorQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#ValueComparatorQuery.
    def exitValueComparatorQuery(self, ctx:cqlParser.ValueComparatorQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#AndQuery.
    def enterAndQuery(self, ctx:cqlParser.AndQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#AndQuery.
    def exitAndQuery(self, ctx:cqlParser.AndQueryContext):
        pass


    # Enter a parse tree produced by cqlParser#RegExQuery.
    def enterRegExQuery(self, ctx:cqlParser.RegExQueryContext):
        pass

    # Exit a parse tree produced by cqlParser#RegExQuery.
    def exitRegExQuery(self, ctx:cqlParser.RegExQueryContext):
        pass



del cqlParser