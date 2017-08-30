/* NOTICE

This software was produced for the U. S. Government
under Basic Contract No. W15P7T-13-C-A802, and is
subject to the Rights in Noncommercial Computer Software
and Noncommercial Computer Software Documentation
Clause 252.227-7014 (FEB 2012)

(C) 2017 The MITRE Corporation.
*/

grammar cql;

SEARCH: 'search' | 'SEARCH';
WHERE: 'where' | 'WHERE';
ANALYTIC: 'analytic' | 'ANALYTIC';

AND: 'and' | 'AND';
OR: 'or' | 'OR';
NOT: 'not' | 'NOT';

floatValue: FLOAT;
intValue: INT;

number: floatValue | intValue;
value: string | number;
field: ID;


allQueries:
    searchQuery (';' searchQuery)* ';'? EOF;

searchQuery: SEARCH query;

dataModelQuery:
	eventObject eventAction WHERE query ;

eventObject: ID;
eventAction: ID;

EQ: '==';
NE: '!=';
LT: '<';
LE: '<=';
GT: '>';
GE: '>=';

analyticReference:
  ANALYTIC '(' ANALYTIC_ID ')' # analyticReferenceByID
| ANALYTIC '(' string ')' # analyticReferenceByName;

valueComparator:
	EQ | NE | LT | LE | GT | GE;

string:
    STRING;


query:
 '(' query ')' # ScopedQuery
|  field valueComparator value # ValueComparatorQuery
|  'match' '(' field ',' value ')' # RegExQuery
| analyticReference # AnalyticReferenceQuery
| NOT query # NotQuery
| query AND query # AndQuery
| query OR query # OrQuery
| dataModelQuery # NestedDataModelQuery;


// Lexer rules
STRING : '"' ( '\\"' | '\\\\' | ~[\\"\r\n] )* '"';
INT: [0-9]+;
FLOAT : [0-9]+.[0-9]+;
ID : [a-zA-Z_][a-zA-Z_0-9]* ;  // match identifiers
ANALYTIC_ID : [a-zA-Z_0-9]+ ;  // match identifiers
COMMENT : '#' ~[\r\n]* -> skip ; // skip comment lines
WS : [ \t\r\n]+ -> skip ; // skip spaces, tabs, newlines
