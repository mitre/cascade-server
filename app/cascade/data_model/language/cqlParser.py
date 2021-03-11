# Generated from cql.g4 by ANTLR 4.9.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\32")
        buf.write("v\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7\4\b")
        buf.write("\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16\t")
        buf.write("\16\4\17\t\17\3\2\3\2\3\3\3\3\3\4\3\4\5\4%\n\4\3\5\3\5")
        buf.write("\5\5)\n\5\3\6\3\6\3\7\3\7\3\7\7\7\60\n\7\f\7\16\7\63\13")
        buf.write("\7\3\7\5\7\66\n\7\3\7\3\7\3\b\3\b\3\b\3\t\3\t\3\t\3\t")
        buf.write("\3\t\3\n\3\n\3\13\3\13\3\f\3\f\3\f\3\f\3\f\3\f\3\f\3\f")
        buf.write("\3\f\5\fO\n\f\3\r\3\r\3\16\3\16\3\17\3\17\3\17\3\17\3")
        buf.write("\17\3\17\3\17\3\17\3\17\3\17\3\17\3\17\3\17\3\17\3\17")
        buf.write("\3\17\3\17\3\17\3\17\3\17\5\17i\n\17\3\17\3\17\3\17\3")
        buf.write("\17\3\17\3\17\7\17q\n\17\f\17\16\17t\13\17\3\17\2\3\34")
        buf.write("\20\2\4\6\b\n\f\16\20\22\24\26\30\32\34\2\3\3\2\16\23")
        buf.write("\2s\2\36\3\2\2\2\4 \3\2\2\2\6$\3\2\2\2\b(\3\2\2\2\n*\3")
        buf.write("\2\2\2\f,\3\2\2\2\169\3\2\2\2\20<\3\2\2\2\22A\3\2\2\2")
        buf.write("\24C\3\2\2\2\26N\3\2\2\2\30P\3\2\2\2\32R\3\2\2\2\34h\3")
        buf.write("\2\2\2\36\37\7\26\2\2\37\3\3\2\2\2 !\7\25\2\2!\5\3\2\2")
        buf.write("\2\"%\5\2\2\2#%\5\4\3\2$\"\3\2\2\2$#\3\2\2\2%\7\3\2\2")
        buf.write("\2&)\5\32\16\2\')\5\6\4\2(&\3\2\2\2(\'\3\2\2\2)\t\3\2")
        buf.write("\2\2*+\7\27\2\2+\13\3\2\2\2,\61\5\16\b\2-.\7\3\2\2.\60")
        buf.write("\5\16\b\2/-\3\2\2\2\60\63\3\2\2\2\61/\3\2\2\2\61\62\3")
        buf.write("\2\2\2\62\65\3\2\2\2\63\61\3\2\2\2\64\66\7\3\2\2\65\64")
        buf.write("\3\2\2\2\65\66\3\2\2\2\66\67\3\2\2\2\678\7\2\2\38\r\3")
        buf.write("\2\2\29:\7\b\2\2:;\5\34\17\2;\17\3\2\2\2<=\5\22\n\2=>")
        buf.write("\5\24\13\2>?\7\t\2\2?@\5\34\17\2@\21\3\2\2\2AB\7\27\2")
        buf.write("\2B\23\3\2\2\2CD\7\27\2\2D\25\3\2\2\2EF\7\n\2\2FG\7\4")
        buf.write("\2\2GH\7\30\2\2HO\7\5\2\2IJ\7\n\2\2JK\7\4\2\2KL\5\32\16")
        buf.write("\2LM\7\5\2\2MO\3\2\2\2NE\3\2\2\2NI\3\2\2\2O\27\3\2\2\2")
        buf.write("PQ\t\2\2\2Q\31\3\2\2\2RS\7\24\2\2S\33\3\2\2\2TU\b\17\1")
        buf.write("\2UV\7\4\2\2VW\5\34\17\2WX\7\5\2\2Xi\3\2\2\2YZ\5\n\6\2")
        buf.write("Z[\5\30\r\2[\\\5\b\5\2\\i\3\2\2\2]^\7\6\2\2^_\7\4\2\2")
        buf.write("_`\5\n\6\2`a\7\7\2\2ab\5\b\5\2bc\7\5\2\2ci\3\2\2\2di\5")
        buf.write("\26\f\2ef\7\r\2\2fi\5\34\17\6gi\5\20\t\2hT\3\2\2\2hY\3")
        buf.write("\2\2\2h]\3\2\2\2hd\3\2\2\2he\3\2\2\2hg\3\2\2\2ir\3\2\2")
        buf.write("\2jk\f\5\2\2kl\7\13\2\2lq\5\34\17\6mn\f\4\2\2no\7\f\2")
        buf.write("\2oq\5\34\17\5pj\3\2\2\2pm\3\2\2\2qt\3\2\2\2rp\3\2\2\2")
        buf.write("rs\3\2\2\2s\35\3\2\2\2tr\3\2\2\2\n$(\61\65Nhpr")
        return buf.getvalue()


class cqlParser ( Parser ):

    grammarFileName = "cql.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "';'", "'('", "')'", "'match'", "','", 
                     "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'=='", "'!='", "'<'", "'<='", 
                     "'>'", "'>='" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "SEARCH", "WHERE", "ANALYTIC", 
                      "AND", "OR", "NOT", "EQ", "NE", "LT", "LE", "GT", 
                      "GE", "STRING", "INT", "FLOAT", "ID", "ANALYTIC_ID", 
                      "COMMENT", "WS" ]

    RULE_floatValue = 0
    RULE_intValue = 1
    RULE_number = 2
    RULE_value = 3
    RULE_field = 4
    RULE_allQueries = 5
    RULE_searchQuery = 6
    RULE_dataModelQuery = 7
    RULE_eventObject = 8
    RULE_eventAction = 9
    RULE_analyticReference = 10
    RULE_valueComparator = 11
    RULE_string = 12
    RULE_query = 13

    ruleNames =  [ "floatValue", "intValue", "number", "value", "field", 
                   "allQueries", "searchQuery", "dataModelQuery", "eventObject", 
                   "eventAction", "analyticReference", "valueComparator", 
                   "string", "query" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    SEARCH=6
    WHERE=7
    ANALYTIC=8
    AND=9
    OR=10
    NOT=11
    EQ=12
    NE=13
    LT=14
    LE=15
    GT=16
    GE=17
    STRING=18
    INT=19
    FLOAT=20
    ID=21
    ANALYTIC_ID=22
    COMMENT=23
    WS=24

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.1")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class FloatValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def FLOAT(self):
            return self.getToken(cqlParser.FLOAT, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_floatValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFloatValue" ):
                listener.enterFloatValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFloatValue" ):
                listener.exitFloatValue(self)




    def floatValue(self):

        localctx = cqlParser.FloatValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_floatValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 28
            self.match(cqlParser.FLOAT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IntValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def INT(self):
            return self.getToken(cqlParser.INT, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_intValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIntValue" ):
                listener.enterIntValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIntValue" ):
                listener.exitIntValue(self)




    def intValue(self):

        localctx = cqlParser.IntValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_intValue)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 30
            self.match(cqlParser.INT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def floatValue(self):
            return self.getTypedRuleContext(cqlParser.FloatValueContext,0)


        def intValue(self):
            return self.getTypedRuleContext(cqlParser.IntValueContext,0)


        def getRuleIndex(self):
            return cqlParser.RULE_number

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumber" ):
                listener.enterNumber(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumber" ):
                listener.exitNumber(self)




    def number(self):

        localctx = cqlParser.NumberContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_number)
        try:
            self.state = 34
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [cqlParser.FLOAT]:
                self.enterOuterAlt(localctx, 1)
                self.state = 32
                self.floatValue()
                pass
            elif token in [cqlParser.INT]:
                self.enterOuterAlt(localctx, 2)
                self.state = 33
                self.intValue()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def string(self):
            return self.getTypedRuleContext(cqlParser.StringContext,0)


        def number(self):
            return self.getTypedRuleContext(cqlParser.NumberContext,0)


        def getRuleIndex(self):
            return cqlParser.RULE_value

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterValue" ):
                listener.enterValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitValue" ):
                listener.exitValue(self)




    def value(self):

        localctx = cqlParser.ValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_value)
        try:
            self.state = 38
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [cqlParser.STRING]:
                self.enterOuterAlt(localctx, 1)
                self.state = 36
                self.string()
                pass
            elif token in [cqlParser.INT, cqlParser.FLOAT]:
                self.enterOuterAlt(localctx, 2)
                self.state = 37
                self.number()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FieldContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(cqlParser.ID, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_field

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterField" ):
                listener.enterField(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitField" ):
                listener.exitField(self)




    def field(self):

        localctx = cqlParser.FieldContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_field)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 40
            self.match(cqlParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AllQueriesContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def searchQuery(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(cqlParser.SearchQueryContext)
            else:
                return self.getTypedRuleContext(cqlParser.SearchQueryContext,i)


        def EOF(self):
            return self.getToken(cqlParser.EOF, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_allQueries

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAllQueries" ):
                listener.enterAllQueries(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAllQueries" ):
                listener.exitAllQueries(self)




    def allQueries(self):

        localctx = cqlParser.AllQueriesContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_allQueries)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 42
            self.searchQuery()
            self.state = 47
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    self.state = 43
                    self.match(cqlParser.T__0)
                    self.state = 44
                    self.searchQuery() 
                self.state = 49
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

            self.state = 51
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==cqlParser.T__0:
                self.state = 50
                self.match(cqlParser.T__0)


            self.state = 53
            self.match(cqlParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SearchQueryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def SEARCH(self):
            return self.getToken(cqlParser.SEARCH, 0)

        def query(self):
            return self.getTypedRuleContext(cqlParser.QueryContext,0)


        def getRuleIndex(self):
            return cqlParser.RULE_searchQuery

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSearchQuery" ):
                listener.enterSearchQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSearchQuery" ):
                listener.exitSearchQuery(self)




    def searchQuery(self):

        localctx = cqlParser.SearchQueryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_searchQuery)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 55
            self.match(cqlParser.SEARCH)
            self.state = 56
            self.query(0)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class DataModelQueryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def eventObject(self):
            return self.getTypedRuleContext(cqlParser.EventObjectContext,0)


        def eventAction(self):
            return self.getTypedRuleContext(cqlParser.EventActionContext,0)


        def WHERE(self):
            return self.getToken(cqlParser.WHERE, 0)

        def query(self):
            return self.getTypedRuleContext(cqlParser.QueryContext,0)


        def getRuleIndex(self):
            return cqlParser.RULE_dataModelQuery

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDataModelQuery" ):
                listener.enterDataModelQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDataModelQuery" ):
                listener.exitDataModelQuery(self)




    def dataModelQuery(self):

        localctx = cqlParser.DataModelQueryContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_dataModelQuery)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 58
            self.eventObject()
            self.state = 59
            self.eventAction()
            self.state = 60
            self.match(cqlParser.WHERE)
            self.state = 61
            self.query(0)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EventObjectContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(cqlParser.ID, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_eventObject

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEventObject" ):
                listener.enterEventObject(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEventObject" ):
                listener.exitEventObject(self)




    def eventObject(self):

        localctx = cqlParser.EventObjectContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_eventObject)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 63
            self.match(cqlParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class EventActionContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(cqlParser.ID, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_eventAction

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEventAction" ):
                listener.enterEventAction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEventAction" ):
                listener.exitEventAction(self)




    def eventAction(self):

        localctx = cqlParser.EventActionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_eventAction)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 65
            self.match(cqlParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AnalyticReferenceContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return cqlParser.RULE_analyticReference

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AnalyticReferenceByIDContext(AnalyticReferenceContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.AnalyticReferenceContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ANALYTIC(self):
            return self.getToken(cqlParser.ANALYTIC, 0)
        def ANALYTIC_ID(self):
            return self.getToken(cqlParser.ANALYTIC_ID, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAnalyticReferenceByID" ):
                listener.enterAnalyticReferenceByID(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAnalyticReferenceByID" ):
                listener.exitAnalyticReferenceByID(self)


    class AnalyticReferenceByNameContext(AnalyticReferenceContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.AnalyticReferenceContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def ANALYTIC(self):
            return self.getToken(cqlParser.ANALYTIC, 0)
        def string(self):
            return self.getTypedRuleContext(cqlParser.StringContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAnalyticReferenceByName" ):
                listener.enterAnalyticReferenceByName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAnalyticReferenceByName" ):
                listener.exitAnalyticReferenceByName(self)



    def analyticReference(self):

        localctx = cqlParser.AnalyticReferenceContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_analyticReference)
        try:
            self.state = 76
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,4,self._ctx)
            if la_ == 1:
                localctx = cqlParser.AnalyticReferenceByIDContext(self, localctx)
                self.enterOuterAlt(localctx, 1)
                self.state = 67
                self.match(cqlParser.ANALYTIC)
                self.state = 68
                self.match(cqlParser.T__1)
                self.state = 69
                self.match(cqlParser.ANALYTIC_ID)
                self.state = 70
                self.match(cqlParser.T__2)
                pass

            elif la_ == 2:
                localctx = cqlParser.AnalyticReferenceByNameContext(self, localctx)
                self.enterOuterAlt(localctx, 2)
                self.state = 71
                self.match(cqlParser.ANALYTIC)
                self.state = 72
                self.match(cqlParser.T__1)
                self.state = 73
                self.string()
                self.state = 74
                self.match(cqlParser.T__2)
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ValueComparatorContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EQ(self):
            return self.getToken(cqlParser.EQ, 0)

        def NE(self):
            return self.getToken(cqlParser.NE, 0)

        def LT(self):
            return self.getToken(cqlParser.LT, 0)

        def LE(self):
            return self.getToken(cqlParser.LE, 0)

        def GT(self):
            return self.getToken(cqlParser.GT, 0)

        def GE(self):
            return self.getToken(cqlParser.GE, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_valueComparator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterValueComparator" ):
                listener.enterValueComparator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitValueComparator" ):
                listener.exitValueComparator(self)




    def valueComparator(self):

        localctx = cqlParser.ValueComparatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_valueComparator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 78
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << cqlParser.EQ) | (1 << cqlParser.NE) | (1 << cqlParser.LT) | (1 << cqlParser.LE) | (1 << cqlParser.GT) | (1 << cqlParser.GE))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StringContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def STRING(self):
            return self.getToken(cqlParser.STRING, 0)

        def getRuleIndex(self):
            return cqlParser.RULE_string

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterString" ):
                listener.enterString(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitString" ):
                listener.exitString(self)




    def string(self):

        localctx = cqlParser.StringContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_string)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 80
            self.match(cqlParser.STRING)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class QueryContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return cqlParser.RULE_query

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class AnalyticReferenceQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def analyticReference(self):
            return self.getTypedRuleContext(cqlParser.AnalyticReferenceContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAnalyticReferenceQuery" ):
                listener.enterAnalyticReferenceQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAnalyticReferenceQuery" ):
                listener.exitAnalyticReferenceQuery(self)


    class OrQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def query(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(cqlParser.QueryContext)
            else:
                return self.getTypedRuleContext(cqlParser.QueryContext,i)

        def OR(self):
            return self.getToken(cqlParser.OR, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOrQuery" ):
                listener.enterOrQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOrQuery" ):
                listener.exitOrQuery(self)


    class NestedDataModelQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def dataModelQuery(self):
            return self.getTypedRuleContext(cqlParser.DataModelQueryContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNestedDataModelQuery" ):
                listener.enterNestedDataModelQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNestedDataModelQuery" ):
                listener.exitNestedDataModelQuery(self)


    class NotQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def NOT(self):
            return self.getToken(cqlParser.NOT, 0)
        def query(self):
            return self.getTypedRuleContext(cqlParser.QueryContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNotQuery" ):
                listener.enterNotQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNotQuery" ):
                listener.exitNotQuery(self)


    class ScopedQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def query(self):
            return self.getTypedRuleContext(cqlParser.QueryContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterScopedQuery" ):
                listener.enterScopedQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitScopedQuery" ):
                listener.exitScopedQuery(self)


    class ValueComparatorQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def field(self):
            return self.getTypedRuleContext(cqlParser.FieldContext,0)

        def valueComparator(self):
            return self.getTypedRuleContext(cqlParser.ValueComparatorContext,0)

        def value(self):
            return self.getTypedRuleContext(cqlParser.ValueContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterValueComparatorQuery" ):
                listener.enterValueComparatorQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitValueComparatorQuery" ):
                listener.exitValueComparatorQuery(self)


    class AndQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def query(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(cqlParser.QueryContext)
            else:
                return self.getTypedRuleContext(cqlParser.QueryContext,i)

        def AND(self):
            return self.getToken(cqlParser.AND, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAndQuery" ):
                listener.enterAndQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAndQuery" ):
                listener.exitAndQuery(self)


    class RegExQueryContext(QueryContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a cqlParser.QueryContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def field(self):
            return self.getTypedRuleContext(cqlParser.FieldContext,0)

        def value(self):
            return self.getTypedRuleContext(cqlParser.ValueContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterRegExQuery" ):
                listener.enterRegExQuery(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitRegExQuery" ):
                listener.exitRegExQuery(self)



    def query(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = cqlParser.QueryContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 26
        self.enterRecursionRule(localctx, 26, self.RULE_query, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 102
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,5,self._ctx)
            if la_ == 1:
                localctx = cqlParser.ScopedQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 83
                self.match(cqlParser.T__1)
                self.state = 84
                self.query(0)
                self.state = 85
                self.match(cqlParser.T__2)
                pass

            elif la_ == 2:
                localctx = cqlParser.ValueComparatorQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 87
                self.field()
                self.state = 88
                self.valueComparator()
                self.state = 89
                self.value()
                pass

            elif la_ == 3:
                localctx = cqlParser.RegExQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 91
                self.match(cqlParser.T__3)
                self.state = 92
                self.match(cqlParser.T__1)
                self.state = 93
                self.field()
                self.state = 94
                self.match(cqlParser.T__4)
                self.state = 95
                self.value()
                self.state = 96
                self.match(cqlParser.T__2)
                pass

            elif la_ == 4:
                localctx = cqlParser.AnalyticReferenceQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 98
                self.analyticReference()
                pass

            elif la_ == 5:
                localctx = cqlParser.NotQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 99
                self.match(cqlParser.NOT)
                self.state = 100
                self.query(4)
                pass

            elif la_ == 6:
                localctx = cqlParser.NestedDataModelQueryContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 101
                self.dataModelQuery()
                pass


            self._ctx.stop = self._input.LT(-1)
            self.state = 112
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,7,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 110
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,6,self._ctx)
                    if la_ == 1:
                        localctx = cqlParser.AndQueryContext(self, cqlParser.QueryContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_query)
                        self.state = 104
                        if not self.precpred(self._ctx, 3):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 3)")
                        self.state = 105
                        self.match(cqlParser.AND)
                        self.state = 106
                        self.query(4)
                        pass

                    elif la_ == 2:
                        localctx = cqlParser.OrQueryContext(self, cqlParser.QueryContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_query)
                        self.state = 107
                        if not self.precpred(self._ctx, 2):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 2)")
                        self.state = 108
                        self.match(cqlParser.OR)
                        self.state = 109
                        self.query(3)
                        pass

             
                self.state = 114
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,7,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[13] = self.query_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def query_sempred(self, localctx:QueryContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 3)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 2)
         




