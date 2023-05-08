language lang;

fragment W: [a-zA-Z_];
fragment D: [0-9];
fragment WD: (W|D);
fragment S: [ \t\r\n\u000C];

INT_NUMBER: [1-9][0-9]*|'0';
REAL_NUMBER: ([1-9][0-9]*)?'.'([0-9]*[1-9]([eE]'-'?[1-9][0-9]*)?|'0')|[1-9][0-9]*[eE]'-'?[1-9][0-9]*;
STRING: '"' ('\\'. | (~'"')+)* '"';
NAME: W WD*;

BLOCK_COMMENT: '/*' (BLOCK_COMMENT|.)*? '*/' -> skip;
COMMENT: '//' .*? '\n' -> skip;
WS: S+ -> skip;

program
    : stmts+=stmt* EOF
    ;

stmt
    : 'let' name=NAME '=' value=expr    # stmt__let
    | ('print' | '>>>')? expr           # stmt__expr
    ;

expr
    : '(' expr_=expr ')'                    # expr__parens
    | sm=expr 'with' what=expr_set_clause   # expr__set
    | what=expr_get_clause 'of' sm=expr     # expr__get
    | value=expr 'mapped' 'with' f=expr     # expr__map
    | value=expr 'filtered' 'with' f=expr   # expr__filter
    | 'load' name=value                     # expr__load
    | '-' value=expr                        # expr__unary_minus
    | left=expr '+' right=expr              # expr__plus
    | left=expr '-' right=expr              # expr__minus
    | left=expr '*' right=expr              # expr__mult
    | left=expr '/' right=expr              # expr__div
    | left=expr '|' right=expr              # expr__or
    | left=expr '&' right=expr              # expr__and
    | '(' sm=expr ')' '*'                   # expr__star
    | name=NAME                             # expr__name
    | value=literal                         # expr__literal
    ;

expr_set_clause
    : 'only' 'start' 'states' states=expr           # expr_set_clause__set_start_states
    | 'only' 'final' 'states' states=expr           # expr_set_clause__set_final_states
    | 'additional'? 'start' 'states' states=expr    # expr_set_clause__add_start_states
    | 'additional'? 'final' 'states' states=expr    # expr_set_clause__add_final_states
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
    : value=STRING                      # literal__string
    | value=INT_NUMBER                  # literal__int
    | value=REAL_NUMBER                 # literal__real
    | '\\' param=NAME '->' body=expr    # literal__lambda
    ;
