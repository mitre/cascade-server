# Generated from C:/Users/...cascade-server/app/cascade/data_model/language\cql.g4 by ANTLR 4.6
from antlr4 import *

# This class defines a complete generic visitor for a parse tree produced by cqlParser.

class cqlVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by cqlParser#floatValue.
    def visitFloatValue(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#intValue.
    def visitIntValue(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#number.
    def visitNumber(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#value.
    def visitValue(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#field.
    def visitField(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#allQueries.
    def visitAllQueries(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#searchQuery.
    def visitSearchQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#dataModelQuery.
    def visitDataModelQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#eventObject.
    def visitEventObject(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#eventAction.
    def visitEventAction(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#analyticReferenceByID.
    def visitAnalyticReferenceByID(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#analyticReferenceByName.
    def visitAnalyticReferenceByName(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#valueComparator.
    def visitValueComparator(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#string.
    def visitString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#AnalyticReferenceQuery.
    def visitAnalyticReferenceQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#OrQuery.
    def visitOrQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#NestedDataModelQuery.
    def visitNestedDataModelQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#NotQuery.
    def visitNotQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#ScopedQuery.
    def visitScopedQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#ValueComparatorQuery.
    def visitValueComparatorQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#AndQuery.
    def visitAndQuery(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by cqlParser#RegExQuery.
    def visitRegExQuery(self, ctx):
        return self.visitChildren(ctx)


