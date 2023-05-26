from project.fa import iterate_transitions
from project.rfa import Nonterminal
import project.interpreter as i
from project.lang import parse
import pytest
import io


def interpret_to_str(*args, **kwargs):
    with io.StringIO() as output:
        kwargs["out"] = output

        i.interpret(*args, **kwargs)

        return output.getvalue()


def check_value(value_type: type, value_value: any, value: i.LangValue):
    assert isinstance(value, value_type)

    assert value_value == i.value_to_python_value(value)


def check_value_type(value_type: type, value: i.LangValue):
    assert isinstance(value, value_type)

    if isinstance(value, i.LangValueLambda):
        return value.value

    return i.value_to_python_value(value)


def match_pattern(pattern: str, value: i.LangValue):
    match = i.interpret(parse(pattern, "pattern"))

    result = dict()
    match(result, value)

    return result


def test_empty_program():
    assert "" == interpret_to_str(parse(""))
    assert "" == interpret_to_str(parse("/* the best program */"))
    assert "" == interpret_to_str(parse("// i hate tests"))
    assert "" == interpret_to_str(parse("// several one-line\n// comments also works"))
    assert "" == interpret_to_str(parse("// TODO rm -rf / --no-preserve-root"))
    assert "" == interpret_to_str(
        parse("/* oh, I also can write /* nested */ comments :P */")
    )


def test_non_empty_program():
    assert "'test'\n'test'\n" == interpret_to_str(
        parse(
            """
let a = "test";

// several one-line
// comments also works

>>> a;

print a;
"""
        )
    )


def test_let():
    assert "" == interpret_to_str(parse("let a = 1;"))

    assert "1\n" == interpret_to_str(parse("let a = 1; a;"))
    assert "2\n" == interpret_to_str(parse("let a = 1; let a = 2; a;"))


def test_print():
    assert "1\n" == interpret_to_str(parse("print 1;"))
    assert "1\n" == interpret_to_str(parse(">>> 1;"))
    assert "1\n" == interpret_to_str(parse("1;"))

    assert "1\n" == interpret_to_str(parse(">>> /* this is constant -> */ 1;"))


def test_parens():
    check_value(i.LangValueInt, 1, i.interpret(parse("(1)", "expr")))
    check_value(
        i.LangValueString,
        "ha_ha_funny",
        i.interpret(parse('((("ha_ha_funny")));', "expr")),
    )


def test_with():
    assert {1} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with only start states { 1 })', "expr")),
    ).start_states
    assert {0} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with only final states { 0 })', "expr")),
    ).final_states
    assert {0, 1} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with additional start states { 1 })', "expr")),
    ).start_states
    assert {0, 1} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with additional final states { 0 })', "expr")),
    ).final_states
    assert {0, 1} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with start states { 1 })', "expr")),
    ).start_states
    assert {0, 1} == check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a" with final states { 0 })', "expr")),
    ).final_states


def test_of():
    check_value(i.LangValueSet, {0}, i.interpret(parse('start states of "a"', "expr")))
    check_value(i.LangValueSet, {1}, i.interpret(parse('final states of "a"', "expr")))
    check_value(
        i.LangValueSet,
        {(0, 1)},
        i.interpret(parse('reachable states of "a"', "expr")),
    )
    check_value(i.LangValueSet, {0, 1}, i.interpret(parse('nodes of "a"', "expr")))
    check_value(
        i.LangValueSet,
        {(0, "a", 1)},
        i.interpret(parse('edges of "a"', "expr")),
    )
    check_value(i.LangValueSet, {"a"}, i.interpret(parse('labels of "a"', "expr")))


def test_map_filter():
    check_value(
        i.LangValueSet,
        {1, 2},
        i.interpret(parse(r"({0, 1} mapped with \x -> x + 1)", "expr")),
    )
    check_value(
        i.LangValueSet,
        {2, 4},
        i.interpret(
            parse(r"({0, 1} mapped with (\x -> x + 1) mapped with \x -> x * 2)", "expr")
        ),
    )

    check_value(
        i.LangValueSet,
        {0, 2},
        i.interpret(parse(r"(0..3 filtered with \x -> x != 1)", "expr")),
    )
    check_value(
        i.LangValueSet,
        {0},
        i.interpret(
            parse(
                r"(0..3 filtered with (\x -> x != 1) filtered with \x -> x == 0)",
                "expr",
            )
        ),
    )

    check_value(
        i.LangValueSet,
        {2, 3},
        i.interpret(
            parse(
                r"(0..3 mapped with (\x -> x + 1) filtered with \x -> x != 1)", "expr"
            )
        ),
    )
    check_value(
        i.LangValueSet,
        {1, 3},
        i.interpret(
            parse(
                r"(0..3 filtered with (\x -> x != 1) mapped with \x -> x + 1)", "expr"
            )
        ),
    )


def test_unary_op():
    result = check_value_type(i.LangValueFA, i.interpret(parse('"a"*', "expr")))

    assert result.accepts("")
    assert result.accepts("a")
    assert result.accepts("aaa")

    result = check_value_type(i.LangValueRSM, i.interpret(parse("rec a*", "expr")))

    assert result.accepts([])
    assert result.accepts([Nonterminal(x) for x in "a"])
    assert result.accepts([Nonterminal(x) for x in "aaa"])

    result = check_value_type(i.LangValueFA, i.interpret(parse('"a"***', "expr")))

    assert result.accepts("")
    assert result.accepts("a")
    assert result.accepts("aaa")

    result = check_value_type(i.LangValueRSM, i.interpret(parse("rec a***", "expr")))

    assert result.accepts([])
    assert result.accepts([Nonterminal(x) for x in "a"])
    assert result.accepts([Nonterminal(x) for x in "aaa"])

    check_value(i.LangValueInt, -1, i.interpret(parse("-1", "expr")))
    check_value(i.LangValueInt, 1, i.interpret(parse("----1", "expr")))

    check_value(i.LangValueReal, -0.21, i.interpret(parse("-0.21", "expr")))
    check_value(i.LangValueReal, 0.21, i.interpret(parse("----0.21", "expr")))

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse('-"1"', "expr"))

    assert (
        str(e.value)
        == "1:1: '1' created on 1:2 is of type string while (one of) ['int', 'real'] is expected"
    )

    check_value(i.LangValueBoolean, True, i.interpret(parse("not (1 != 1)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("not (1 == 1)", "expr")))

    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("not not not not (1 == 1)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("not not not not (1 != 1)", "expr")),
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("not 1", "expr"))

    assert (
        str(e.value)
        == "1:1: 1 created on 1:5 is of type int while (one of) boolean is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse('not "a"', "expr"))

    assert (
        str(e.value)
        == "1:1: 'a' created on 1:5 is of type string while (one of) boolean is expected"
    )


# def test_binary_op():
#     assert l.check_syntax("a * b;")
#     assert l.check_syntax("a / b;")
#     assert l.check_syntax("a & b;")
#     assert l.check_syntax("a + b;")
#     assert l.check_syntax("a - b;")
#     assert l.check_syntax("a | b;")
#     assert l.check_syntax("a == b;")
#     assert l.check_syntax("a != b;")
#     assert l.check_syntax("a < b;")
#     assert l.check_syntax("a > b;")
#     assert l.check_syntax("a <= b;")
#     assert l.check_syntax("a >= b;")
#     assert l.check_syntax("a in b;")
#     assert l.check_syntax("a not in b;")
#     assert l.check_syntax("a and b;")
#     assert l.check_syntax("a or b;")
#     assert l.check_syntax("a not   \t  \n  in b;")
#
#     assert (
#         "([] ([14] ([31 14] ([4 31 14] ([4 4 31 14] ([4 4 4 31 14] ([4 4 4 4 31 14] ([4 4 4 4 4 31 14] ([4 4 4 4 4 4 31 14] ([4 4 4 4 4 4 4 31 14] a) * ([56 4 4 4 4 4 4 31 14] b)) + ([59 4 4 4 4 4 31 14] ([4 59 4 4 4 4 4 31 14] a) / ([56 59 4 4 4 4 4 31 14] b))) - ([59 4 4 4 4 31 14] ([4 59 4 4 4 4 31 14] a) & ([56 59 4 4 4 4 31 14] b))) | ([59 4 4 4 31 14] c)) == ([62 4 4 31 14] a)) or ([68 4 31 14] ([4 68 4 31 14] ([4 4 68 4 31 14] a) < ([62 4 68 4 31 14] c)) and ([65 68 4 31 14] ([4 65 68 4 31 14] a) in ([62 65 68 4 31 14] c)))) or ([68 31 14] ([4 68 31 14] a) not in ([62 68 31 14] ([4 62 68 31 14] c) | ([59 62 68 31 14] b))))) ; <EOF>)"
#         == l.parse(
#             "a * b + a / b - a & b | c == a or a < c and a in c or a not in c | b;"
#         ).toStringTree()
#     )


# def test_load():
#     assert l.check_syntax('load "";')
#     assert l.check_syntax('load "test";')
#     assert l.check_syntax('load /* my cool graph */ "test";')
#
#     assert l.check_syntax(
#         r"""
# load "test"
# with only start states { 1, 2, 3 }
# with only final states { 5, 6 }
# ;
# """
#     )


def test_name():
    assert "1\n" == interpret_to_str(parse("let test = 1; test;"))
    assert "2\n" == interpret_to_str(parse("let tEsT = 2; tEsT;"))
    assert "3\n" == interpret_to_str(parse("let t_e_s_t = 3; t_e_s_t;"))
    assert "4\n" == interpret_to_str(parse("let test1 = 4; test1;"))
    assert "5\n" == interpret_to_str(parse("let test_1 = 5; test_1;"))
    assert "6\n" == interpret_to_str(parse("let ___test = 6; ___test;"))
    assert "7\n" == interpret_to_str(parse("let test___ = 7; test___;"))
    assert "8\n" == interpret_to_str(parse("let _ = 8; _;"))

    with pytest.raises(i.InterpretError) as e:
        assert interpret_to_str(parse("let test = 9; tEsT;"))

    assert str(e.value) == '1:15: name "tEsT" is not in scope'

    result = check_value_type(i.LangValueRSM, i.interpret(parse("rec test", "expr")))

    assert result.accepts([Nonterminal("test")])
    assert {(0, Nonterminal("test"), 1)} == set(iterate_transitions(result))


def test_string():
    check_value(i.LangValueString, "", i.interpret(parse('""', "literal")))
    check_value(
        i.LangValueString,
        "Hello, World!",
        i.interpret(parse('"Hello, World!"', "literal")),
    )
    check_value(
        i.LangValueString,
        'Hello, my "friend"',
        i.interpret(parse('"Hello, my \\"friend\\""', "literal")),
    )


def test_int():
    check_value(i.LangValueInt, 0, i.interpret(parse("0", "literal")))
    check_value(i.LangValueInt, 1, i.interpret(parse("1", "literal")))
    check_value(i.LangValueInt, -1, i.interpret(parse("-1", "expr")))
    check_value(
        i.LangValueInt,
        10000000000000000000,
        i.interpret(parse("10000000000000000000", "literal")),
    )


def test_real():
    check_value(i.LangValueReal, 0, i.interpret(parse(".0", "literal")))
    check_value(i.LangValueReal, 0, i.interpret(parse("0.0", "literal")))
    check_value(i.LangValueReal, 0.12313, i.interpret(parse("0.12313", "literal")))
    check_value(i.LangValueReal, 0.234234, i.interpret(parse(".234234", "literal")))
    check_value(i.LangValueReal, 0.1e1231, i.interpret(parse(".1e1231", "literal")))
    check_value(i.LangValueReal, 0.2e1, i.interpret(parse(".2E1", "literal")))
    check_value(i.LangValueReal, 0.3e-1, i.interpret(parse(".3E-1", "literal")))
    check_value(i.LangValueReal, 0.1e-131, i.interpret(parse(".1e-131", "literal")))
    check_value(i.LangValueReal, 1e131, i.interpret(parse("1e131", "literal")))
    check_value(i.LangValueReal, 1e-11, i.interpret(parse("1E-11", "literal")))


def test_range():
    check_value(i.LangValueSet, {1}, i.interpret(parse("1..2", "literal")))
    check_value(i.LangValueSet, {1}, i.interpret(parse("1 .. 2", "literal")))

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(-1..2)", "expr"))

    assert (
        str(e.value)
        == "1:2: {1} created on 1:3 is of type set while (one of) ['int', 'real'] is expected"
    )


def test_set():
    check_value(i.LangValueSet, set(), i.interpret(parse("{}", "literal")))
    check_value(i.LangValueSet, {1}, i.interpret(parse("{1}", "literal")))
    check_value(i.LangValueSet, {1, 2}, i.interpret(parse("{ 1, 2 }", "literal")))
    check_value(i.LangValueSet, {1, 2}, i.interpret(parse("{ 1, 2, }", "literal")))
    check_value(i.LangValueSet, {1, "2"}, i.interpret(parse('{ 1, "2", }', "literal")))
    check_value(
        i.LangValueSet,
        {1, frozenset({"2"})},
        i.interpret(parse('{ 1, {"2"}, }', "literal")),
    )
    check_value(
        i.LangValueSet,
        {1, frozenset({frozenset({1})})},
        i.interpret(parse("{ 1, { 1..2 }, }", "literal")),
    )

    assert interpret_to_str(parse('let a = "a"; let b = 2; { a, (1 + b), };')) in [
        "{'a', 3}\n",
        "{3, 'a'}\n",
    ]


def test_lambda():
    value1 = i.interpret(parse("123", "literal"))
    value2 = i.interpret(parse('"123"', "literal"))

    result = check_value_type(
        i.LangValueLambda,
        i.interpret(parse(r"\x -> x", "literal")),
    )
    assert result(value1) is value1
    assert result(value2) is value2

    result = check_value_type(
        i.LangValueLambda,
        i.interpret(parse(r"\x -> x * 2", "literal")),
    )
    check_value(i.LangValueInt, 123 * 2, result(value1))
    check_value(i.LangValueString, "123" * 2, result(value2))

    result = check_value_type(
        i.LangValueLambda,
        i.interpret(parse(r"\x -> x + y & x", "literal")),
    )

    with pytest.raises(ValueError) as e:
        result(value1)

    assert str(e.value) == 'name "y" is not in scope'


def test_name_pattern():
    value = i.interpret(parse('"123"', "literal"))

    result = match_pattern("xyz", value)
    assert result == {"xyz": value}
    assert result["xyz"] is value

    result = match_pattern("x123", value)
    assert result == {"x123": value}
    assert result["x123"] is value

    result = match_pattern("___123", value)
    assert result == {"___123": value}
    assert result["___123"] is value

    assert match_pattern("_", value) == dict()


def test_tuple_pattern():
    ctx = parse("")

    assert match_pattern("(x, y)", i.python_value_to_value(("test", 123), ctx)) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
    }

    assert match_pattern(
        "(x, y, z)",
        i.python_value_to_value(("test", 123, 0.321), ctx),
    ) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
        "z": i.LangValueReal(value=0.321, ctx=ctx),
    }

    assert match_pattern(
        "(x, (y, z), w)",
        i.python_value_to_value(("test", (123, 0.321), True), ctx),
    ) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
        "z": i.LangValueReal(value=0.321, ctx=ctx),
        "w": i.LangValueBoolean(value=True, ctx=ctx),
    }

    assert match_pattern(
        "(x, y, (z, w))",
        i.python_value_to_value(("test", 123, (0.321, True)), ctx),
    ) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
        "z": i.LangValueReal(value=0.321, ctx=ctx),
        "w": i.LangValueBoolean(value=True, ctx=ctx),
    }

    assert match_pattern(
        "((x, y), z)",
        i.python_value_to_value((("test", 123), 0.321), ctx),
    ) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
        "z": i.LangValueReal(value=0.321, ctx=ctx),
    }

    assert match_pattern("(x, y, )", i.python_value_to_value(("test", 123), ctx)) == {
        "x": i.LangValueString(value="test", ctx=ctx),
        "y": i.LangValueInt(value=123, ctx=ctx),
    }

    with pytest.raises(ValueError) as e:
        match_pattern("(x, y)", i.python_value_to_value("test", ctx))

    assert (
        str(e.value)
        == "'test' created on 1:1 is of type string while (one of) tuple is expected"
    )

    with pytest.raises(ValueError) as e:
        match_pattern("(x, y)", i.python_value_to_value(("test", 123, 0.321), ctx))

    assert str(e.value) == "wrong number of elements in tuple 3 vs expected 2"

    with pytest.raises(ValueError) as e:
        match_pattern("(x, (y, z))", i.python_value_to_value(("test", 123), ctx))

    assert (
        str(e.value)
        == "123 created on 1:1 is of type int while (one of) tuple is expected"
    )
