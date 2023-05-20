grammar lang;

fragment W: [a-zA-Z_];
fragment D: [0-9];
fragment WD: (W|D);
fragment S: [ \t\r\n\u000C];

INT_NUMBER: [1-9][0-9]*|'0';
REAL_NUMBER: ([1-9][0-9]*|'0')?'.'([0-9]*[1-9]([eE]'-'?[1-9][0-9]*)?|'0')|[1-9][0-9]*[eE]'-'?[1-9][0-9]*;
STRING: '"' ('\\'. | (~'"')+)* '"';
NAME: W WD*;

BLOCK_COMMENT: '/*' (BLOCK_COMMENT|.)*? '*/' -> skip;
COMMENT: '//' .*? ('\n'|EOF) -> skip;
WS: S+ -> skip;

// here we allow to use any number of spaces betwen 'not' and 'in'
// but we need to sanitize them in future
NOT_IN: 'not' WS 'in';

program
    : (stmts+=stmt ';')* EOF
    ;

stmt
    : 'let' name=NAME '=' value=expr    # stmt__let
    | ('print' | '>>>')? value=expr     # stmt__expr
    ;

expr
    : '(' expr_=expr ')'                                                # expr__parens
    | name=NAME                                                         # expr__name
    | value=literal                                                     # expr__literal
    | 'load' name=STRING                                                # expr__load
    | value=expr op='*'                                                 # expr__unary_op
    | op=('-'|'not') value=expr                                         # expr__unary_op
    | left=expr op=('*'|'/'|'&') right=expr                             # expr__binary_op
    | left=expr op=('+'|'-'|'|') right=expr                             # expr__binary_op
    | left=expr op=('=='|'!='|'<'|'>'|'<='|'>='|'in'|NOT_IN) right=expr # expr__binary_op
    | left=expr op='and' right=expr                                     # expr__binary_op
    | left=expr op='or' right=expr                                      # expr__binary_op
    | sm=expr 'with' what=expr_set_clause what_value=expr               # expr__set
    | what=expr_get_clause 'of' sm=expr                                 # expr__get
    | value=expr op=('mapped'|'filtered') 'with' f=expr                 # expr__map_filter
    ;

expr_set_clause
    : 'only' 'start' 'states'           # expr_set_clause__set_start_states
    | 'only' 'final' 'states'           # expr_set_clause__set_final_states
    | 'additional'? 'start' 'states'    # expr_set_clause__add_start_states
    | 'additional'? 'final' 'states'    # expr_set_clause__add_final_states
    ;

expr_get_clause
    : 'start' 'states'      # expr_get_clause__start_states
    | 'final' 'states'      # expr_get_clause__final_states
    | 'reachable' 'states'  # expr_get_clause__reachable_states
    | 'nodes'               # expr_get_clause__nodes
    | 'edges'               # expr_get_clause__edges
    | 'labels'              # expr_get_clause__labels
    ;

literal
    : value=STRING                                      # literal__string
    | value=INT_NUMBER                                  # literal__int
    | value=REAL_NUMBER                                 # literal__real
    | from=INT_NUMBER '..' to=INT_NUMBER                # literal__range
    | '{' ((elems+=expr ',')* elems+=expr ','?)? '}'    # literal__set
    | '\\' param=pattern '->' body=expr                 # literal__lambda
    ;

pattern
    : name=NAME                                         # pattern__name
    | '(' (elems+=pattern ',')+ elems+=pattern ','? ')' # pattern__tuple
    ;
