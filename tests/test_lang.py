import project.lang as l
import tempfile


def test_empty_program():
    assert l.check_syntax("")
    assert l.check_syntax("/* the best program */")
    assert l.check_syntax("// i hate tests")
    assert l.check_syntax("// several one-line\n// comments also works")
    assert l.check_syntax("// TODO rm -rf / --no-preserve-root")
    assert l.check_syntax("/* oh, I also can write /* nested */ comments :P */")

    assert not l.check_syntax(";")
    assert not l.check_syntax(";;;")


def test_non_empty_program():
    assert l.check_syntax(
        """
let a = "test";

// several one-line
// comments also works

>>> a;

print x;
"""
    )


def test_let():
    assert l.check_syntax("let a = 1;")
    assert l.check_syntax("let a = /* this is another name being shadowed -> */ a;")
    assert l.check_syntax("let a = a; // my cool variable")
    assert l.check_syntax("// my cool variable\nlet a = a;")

    assert not l.check_syntax("let a = 1")
    assert not l.check_syntax("let a = 1;;")
    assert not l.check_syntax("let 1 = a;")


def test_print():
    assert l.check_syntax("print 1;")
    assert l.check_syntax(">>> 1;")
    assert l.check_syntax("1;")

    assert l.check_syntax(">>> /* this is constant -> */ 1;")

    assert not l.check_syntax("print 1")
    assert not l.check_syntax(">>> 1")
    assert not l.check_syntax("1")

    assert not l.check_syntax("print 1;;")
    assert not l.check_syntax(">>> 1;;")
    assert not l.check_syntax("1;;")


def test_parens():
    assert l.check_syntax("(1);")
    assert l.check_syntax("(((ha_ha_funny)));")
    assert l.check_syntax(
        "(    ( \t spaces \n ) \r ) /* comment */ // and another \n ; "
    )

    assert not l.check_syntax("((wtf)));")
    assert not l.check_syntax("(((wtf));")


def test_with():
    assert l.check_syntax("graph with only start states a;")
    assert l.check_syntax("graph with only final states a;")
    assert l.check_syntax("graph with additional start states a;")
    assert l.check_syntax("graph with additional final states a;")
    assert l.check_syntax("graph with start states a;")
    assert l.check_syntax("graph with final states a;")

    assert l.check_syntax("graph with /* comment */ only /* :) */ start \n states a;")
    assert l.check_syntax("graph with /* comment */ only /* :) */ final \n states a;")
    assert l.check_syntax(
        "graph with /* comment */ additional /* :) */ start \n states a;"
    )
    assert l.check_syntax(
        "graph with /* comment */ additional /* :) */ final \n states a;"
    )
    assert l.check_syntax("graph with /* comment */ start /* :) */ states a;")
    assert l.check_syntax("graph with /* comment */ final /* :) */ states a;")

    assert not l.check_syntax("graph with additional only start states a;")
    assert not l.check_syntax("graph with additional only final states a;")
    assert not l.check_syntax("graph with only additional start states a;")
    assert not l.check_syntax("graph with only additional final states a;")


def test_of():
    assert l.check_syntax("start states of finite_automaton;")
    assert l.check_syntax("final states of finite_automaton;")
    assert l.check_syntax("reachable states of finite_automaton;")
    assert l.check_syntax("nodes of graph;")
    assert l.check_syntax("edges of graph;")
    assert l.check_syntax("labels of graph;")

    assert l.check_syntax("start /* cool */ states \n of finite_automaton;")
    assert l.check_syntax("final /* cool */ states \n of finite_automaton;")
    assert l.check_syntax("reachable /* cool */ states \n of finite_automaton;")
    assert l.check_syntax("nodes \n of graph;")
    assert l.check_syntax("edges \n of graph;")
    assert l.check_syntax("labels \n of graph;")

    assert not l.check_syntax("start final states of finite_automaton;")
    assert not l.check_syntax("final start states of finite_automaton;")
    assert not l.check_syntax("reachable final states of finite_automaton;")
    assert not l.check_syntax("reachable start states of finite_automaton;")
    assert not l.check_syntax("final reachable states of finite_automaton;")
    assert not l.check_syntax("start reachable states of finite_automaton;")
    assert not l.check_syntax("reachable nodes of graph;")
    assert not l.check_syntax("final edges of graph;")
    assert not l.check_syntax("start labels of graph;")


def test_map_filter():
    assert l.check_syntax("set mapped with lambda;")
    assert l.check_syntax("set filtered with lambda;")

    assert l.check_syntax("set \n mapped /* accurately */ with lambda;")
    assert l.check_syntax("set \n filtered /* with care */ with lambda;")

    assert l.check_syntax("set \n mapped with f \n filtered with g mapped with h;")
    assert l.check_syntax("set \n filtered with f \n mapped with g filtered with h;")

    assert l.check_syntax("set \n mapped with f \n mapped with g mapped with h;")
    assert l.check_syntax("set \n filtered with f \n filtered with g filtered with h;")


def test_unary_op():
    assert l.check_syntax("set*;")
    assert l.check_syntax("set**/*wtf*/**;")
    assert l.check_syntax("not-set**/*wtf*/**;")

    assert l.check_syntax("-1;")
    assert l.check_syntax("--- - - -  \n  1;")
    assert l.check_syntax("---- /* count them */ --- 1;")
    assert l.check_syntax("1 ---- /* next section :D */ ---- 1;")

    assert l.check_syntax("not cond;")
    assert l.check_syntax("not not not cond;")
    assert l.check_syntax("not not /* not */ not not cond;")

    assert not l.check_syntax("not not not not not;")


def test_binary_op():
    assert l.check_syntax("a * b;")
    assert l.check_syntax("a / b;")
    assert l.check_syntax("a & b;")
    assert l.check_syntax("a + b;")
    assert l.check_syntax("a - b;")
    assert l.check_syntax("a | b;")
    assert l.check_syntax("a == b;")
    assert l.check_syntax("a != b;")
    assert l.check_syntax("a < b;")
    assert l.check_syntax("a > b;")
    assert l.check_syntax("a <= b;")
    assert l.check_syntax("a >= b;")
    assert l.check_syntax("a in b;")
    assert l.check_syntax("a not in b;")
    assert l.check_syntax("a and b;")
    assert l.check_syntax("a or b;")
    assert l.check_syntax("a not   \t  \n  in b;")

    assert (
        "([] ([14] ([31 14] ([4 31 14] ([4 4 31 14] ([4 4 4 31 14] ([4 4 4 4 31 14] ([4 4 4 4 4 31 14] ([4 4 4 4 4 4 31 14] ([4 4 4 4 4 4 4 31 14] a) * ([56 4 4 4 4 4 4 31 14] b)) + ([59 4 4 4 4 4 31 14] ([4 59 4 4 4 4 4 31 14] a) / ([56 59 4 4 4 4 4 31 14] b))) - ([59 4 4 4 4 31 14] ([4 59 4 4 4 4 31 14] a) & ([56 59 4 4 4 4 31 14] b))) | ([59 4 4 4 31 14] c)) == ([62 4 4 31 14] a)) or ([68 4 31 14] ([4 68 4 31 14] ([4 4 68 4 31 14] a) < ([62 4 68 4 31 14] c)) and ([65 68 4 31 14] ([4 65 68 4 31 14] a) in ([62 65 68 4 31 14] c)))) or ([68 31 14] ([4 68 31 14] a) not in ([62 68 31 14] ([4 62 68 31 14] c) | ([59 62 68 31 14] b))))) ; <EOF>)"
        == l.parse(
            "a * b + a / b - a & b | c == a or a < c and a in c or a not in c | b;"
        ).toStringTree()
    )

    assert not l.check_syntax("a iN b;")
    assert not l.check_syntax("a Not in b;")
    assert not l.check_syntax("a anD b;")
    assert not l.check_syntax("a Or b;")
    assert not l.check_syntax("a not   /*  */  \n  in b;")
    assert not l.check_syntax("a not   //  \n  in b;")


def test_load():
    assert l.check_syntax('load "";')
    assert l.check_syntax('load "test";')
    assert l.check_syntax('load /* my cool graph */ "test";')

    assert l.check_syntax(
        r"""
load "test"
with only start states { 1, 2, 3 }
with only final states { 5, 6 }
;
"""
    )

    assert not l.check_syntax("load;")
    assert not l.check_syntax("load 1;")
    assert not l.check_syntax("load test;")
    assert not l.check_syntax('load "graph1", "graph2";')


def test_name():
    assert l.check_syntax("test;")
    assert l.check_syntax("tEsT;")
    assert l.check_syntax("t_e_s_t;")
    assert l.check_syntax("test1;")
    assert l.check_syntax("test_1;")
    assert l.check_syntax("___test;")
    assert l.check_syntax("test___;")
    assert l.check_syntax("_;")

    assert l.check_syntax("rec test;")

    assert not l.check_syntax(">>> ;")
    assert not l.check_syntax("te/*eeeeee*/st;")
    assert not l.check_syntax("имя;")

    assert not l.check_syntax("rec rec;")
    assert not l.check_syntax("rec rec test;")


def test_string():
    assert l.check_syntax('"";')
    assert l.check_syntax('"Hello, World!";')
    assert l.check_syntax('"Hello, my \\"friend\\"";')

    assert not l.check_syntax('";')
    assert not l.check_syntax("'test';")


def test_int():
    assert l.check_syntax("0;")
    assert l.check_syntax("1;")
    assert l.check_syntax("-1;")
    assert l.check_syntax("10000000000000000000;")

    assert not l.check_syntax("00;")
    assert not l.check_syntax("01;")


def test_real():
    assert l.check_syntax(".0;")
    assert l.check_syntax("0.0;")
    assert l.check_syntax("0.12313;")
    assert l.check_syntax(".234234;")
    assert l.check_syntax(".1e1231;")
    assert l.check_syntax(".2E1;")
    assert l.check_syntax(".3E-1;")
    assert l.check_syntax(".1e-131;")
    assert l.check_syntax("1e131;")
    assert l.check_syntax("1E-11;")

    assert not l.check_syntax("0.;")
    assert not l.check_syntax("01.;")
    assert not l.check_syntax(".0e21;")
    assert not l.check_syntax("0e21;")
    assert not l.check_syntax("1e21e2;")
    assert not l.check_syntax("1e0;")
    assert not l.check_syntax("1E0;")


def test_range():
    assert l.check_syntax("1..2;")
    assert l.check_syntax("1 .. 2;")
    assert l.check_syntax("1 /* left */ .. /* right */ 2;")
    assert l.check_syntax("-1..2; // this is not that you think...")

    assert not l.check_syntax("(-1)..2; // this is limitation")
    assert not l.check_syntax("a..2; // this is limitation")
    assert not l.check_syntax('"x".."y";')
    assert not l.check_syntax("1.2 .. 2e1;")


def test_set():
    assert l.check_syntax("{};")
    assert l.check_syntax("{1};")
    assert l.check_syntax("{ 1 };")
    assert l.check_syntax("{ 1 , };")
    assert l.check_syntax("{ 1, 2 };")
    assert l.check_syntax("{ 1, 2, };")
    assert l.check_syntax('{ 1, "2", };')
    assert l.check_syntax('{ 1, {"2"}, };')
    assert l.check_syntax("{ 1, { 1..2 }, };")
    assert l.check_syntax("{ a, (1 + b), };")

    assert not l.check_syntax("{ , };")
    assert not l.check_syntax("{ 1,, };")
    assert not l.check_syntax("{ , 1 };")


def test_lambda():
    assert l.check_syntax("\\x->x;")
    assert l.check_syntax("\\ x -> x ;")
    assert l.check_syntax("\\ x -> x + y & x ;")
    assert l.check_syntax("\\ /* wtf */ x /* wtf */ -> /* wtf */ x in y & x ;")

    # lambda consumes all expression
    assert (
        "([] ([14] ([31 14] ([43 31 14] \\ ([137 43 31 14] x) -> ([139 43 31 14] ([4 139 43 31 14] x) + ([59 139 43 31 14] ([4 59 139 43 31 14] y) & ([56 59 139 43 31 14] x)))))) ; <EOF>)"
        == l.parse("\\ x -> x + y & x ;").toStringTree()
    )

    assert not l.check_syntax("\\ -> x;")
    assert not l.check_syntax("\\ x - > x;")
    assert not l.check_syntax("\\ x y -> x;")


def test_name_pattern():
    assert l.check_syntax("\\ xyz -> x;")
    assert l.check_syntax("\\ x123 -> x;")
    assert l.check_syntax("\\ x___123 -> x;")
    assert l.check_syntax("\\ _ -> x;")

    assert not l.check_syntax("\\ 1 -> x;")


def test_tuple_pattern():
    assert l.check_syntax("\\ (x, y) -> x;")
    assert l.check_syntax("\\ (x, y, z) -> x;")
    assert l.check_syntax("\\ (x, y, z, w) -> x;")
    assert l.check_syntax("\\ (x, (y, z), w) -> x;")
    assert l.check_syntax("\\ (x, y, (z, w)) -> x;")
    assert l.check_syntax("\\ ((x, y), z) -> x;")
    assert l.check_syntax("\\ ((x,y),z) -> x;")
    assert l.check_syntax("\\ ((x, /* wtf */ y) /* lol */ ,z) -> x;")
    assert l.check_syntax("\\ (x, y, ) -> x;")

    assert not l.check_syntax("\\ () -> x;")
    assert not l.check_syntax("\\ (,) -> x;")
    assert not l.check_syntax("\\ (x,) -> x;")
    assert not l.check_syntax("\\ (,x) -> x;")
    assert not l.check_syntax("\\ (x,,y) -> x;")
