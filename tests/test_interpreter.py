from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.regular_expression import Regex
from project.fa import iterate_transitions
from project.rfa import Nonterminal
import project.interpreter as i
import project.graphs as graphs
from project.lang import parse
import project.fa as fa
import tempfile
import pytest
import math
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

    assert {1} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with only start states { 1 })", "expr")),
    ).start_states
    assert {0} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with only final states { 0 })", "expr")),
    ).final_states
    assert {0, 1} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with additional start states { 1 })", "expr")),
    ).start_states
    assert {0, 1} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with additional final states { 0 })", "expr")),
    ).final_states
    assert {0, 1} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with start states { 1 })", "expr")),
    ).start_states
    assert {0, 1} == check_value_type(
        i.LangValueRSM,
        i.interpret(parse("(rec a with final states { 0 })", "expr")),
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

    check_value(
        i.LangValueSet,
        {0},
        i.interpret(parse("start states of rec a", "expr")),
    )
    check_value(
        i.LangValueSet,
        {1},
        i.interpret(parse("final states of rec a", "expr")),
    )
    check_value(
        i.LangValueSet,
        {(0, 1)},
        i.interpret(parse("reachable states of rec a", "expr")),
    )
    check_value(i.LangValueSet, {0, 1}, i.interpret(parse("nodes of rec a", "expr")))
    check_value(
        i.LangValueSet,
        {(0, "Nonterminal(a)", 1)},
        i.interpret(parse("edges of rec a", "expr")),
    )
    check_value(
        i.LangValueSet,
        {"Nonterminal(a)"},
        i.interpret(parse("labels of rec a", "expr")),
    )


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


def test_binary_op_boolean():
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) == (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) == (1 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) != (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) != (1 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) < (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) < (1 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 2) < (2 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) <= (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) <= (1 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 2) <= (2 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 1) > (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) > (1 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 2) > (2 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) >= (2 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("((1 == 1) >= (1 == 2))", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("((1 == 2) >= (2 == 2))", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("(1 == 1 or 2 == 2)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("(1 == 1 or 1 == 2)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("(1 == 2 or 2 == 1)", "expr")),
    )

    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("(1 == 1 and 2 == 2)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("(1 == 1 and 1 == 2)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("(1 == 2 and 2 == 1)", "expr")),
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 or 2 == 2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 1 created on 1:2 is of type int while (one of) boolean is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 == 1 or 2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 2 created on 1:12 is of type int while (one of) boolean is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 and 2 == 2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 1 created on 1:2 is of type int while (one of) boolean is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 == 1 and 2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 2 created on 1:13 is of type int while (one of) boolean is expected"
    )


def test_binary_op_int():
    check_value(i.LangValueBoolean, False, i.interpret(parse("(1 == 2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(2 == 2)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(1 != 2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(2 != 2)", "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse("(2 < 2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(1 < 2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(3 < 1)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(2 <= 2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(1 <= 2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(3 <= 1)", "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse("(2 > 2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(1 > 2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(3 > 1)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(2 >= 2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(1 >= 2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(3 >= 1)", "expr")))

    check_value(i.LangValueInt, 3, i.interpret(parse("(1 + 2)", "expr")))
    check_value(i.LangValueInt, -1, i.interpret(parse("(1 - 2)", "expr")))
    check_value(i.LangValueInt, 2, i.interpret(parse("(1 * 2)", "expr")))
    check_value(i.LangValueInt, 2, i.interpret(parse("(6 / 3)", "expr")))
    check_value(i.LangValueReal, 0.5, i.interpret(parse("(1 / 2)", "expr")))
    check_value(i.LangValueInt, 3, i.interpret(parse("(1 | 2)", "expr")))
    check_value(i.LangValueInt, 2, i.interpret(parse("(7 & 2)", "expr")))

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 | .2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 0.2 created on 1:6 is of type real while (one of) int is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(1 & .2)", "expr"))

    assert (
        str(e.value)
        == "1:2: 0.2 created on 1:6 is of type real while (one of) int is expected"
    )


def test_binary_op_real():
    check_value(i.LangValueBoolean, True, i.interpret(parse("(1.0 == 1)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(.1 == .2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(.2 == .2)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(.1 != .2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(2 != 2.0)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(.2 != .2)", "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse("(.2 < .2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(.1 < .2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(1 < .1)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(.2 <= .2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(.1 <= .2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(1 <= .1)", "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse("(.2 > .2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(.1 > .2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(1 > .1)", "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse("(.2 >= .2)", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("(.1 >= .2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("(1 >= .1)", "expr")))

    check_value(i.LangValueReal, 3.2, i.interpret(parse("(1 + 2.2)", "expr")))
    assert math.isclose(
        -0.6,
        check_value_type(i.LangValueReal, i.interpret(parse("(1.4 - 2)", "expr"))),
    )
    check_value(i.LangValueReal, 2.4, i.interpret(parse("(1.2 * 2)", "expr")))
    check_value(i.LangValueInt, 4, i.interpret(parse("(3.6 / 0.9)", "expr")))
    check_value(i.LangValueReal, 0.65, i.interpret(parse("(1.3 / 2)", "expr")))


def test_binary_op_string():
    check_value(i.LangValueBoolean, False, i.interpret(parse('("a" == "b")', "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse('("b" == "b")', "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse('("a" != "b")', "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse('("b" != "b")', "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse('("b" < "b")', "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse('("a" < "b")', "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse('("c" < "a")', "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse('("b" <= "b")', "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse('("a" <= "b")', "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse('("c" <= "a")', "expr")))

    check_value(i.LangValueBoolean, False, i.interpret(parse('("b" > "b")', "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse('("a" > "b")', "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse('("c" > "a")', "expr")))

    check_value(i.LangValueBoolean, True, i.interpret(parse('("b" >= "b")', "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse('("a" >= "b")', "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse('("c" >= "a")', "expr")))

    check_value(i.LangValueString, "ab", i.interpret(parse('("a" + "b")', "expr")))
    check_value(i.LangValueString, "a3", i.interpret(parse('("a" + 3)', "expr")))
    check_value(i.LangValueString, "aaa", i.interpret(parse('("a" * 3)', "expr")))
    check_value(i.LangValueString, "bbb", i.interpret(parse('(3 * "b")', "expr")))

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse('(3.5 * "b")', "expr"))

    assert (
        str(e.value)
        == "1:2: 'b' created on 1:8 is of type string while (one of) ['int', 'real'] is expected"
    )

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse('("a" * "b")', "expr"))

    assert (
        str(e.value)
        == "1:2: 'b' created on 1:8 is of type string while (one of) int is expected"
    )


def test_binary_op_fa():
    check_value(
        i.LangValueFA,
        Regex("a b").to_epsilon_nfa(),
        i.interpret(parse('(("a" | "a") + "b")', "expr")),
    )

    check_value(
        i.LangValueFA,
        Regex("a | b").to_epsilon_nfa(),
        i.interpret(parse('("a" | "b")', "expr")),
    )

    result = check_value_type(i.LangValueFA, i.interpret(parse('("a" & "b")', "expr")))

    assert result.states == {(0, 0), (1, 1)}
    assert result.start_states == {(0, 0)}
    assert result.final_states == {(1, 1)}
    assert result.symbols == set()
    assert list(iterate_transitions(result)) == []

    result = check_value_type(
        i.LangValueFA,
        i.interpret(parse('("a"* + "b") & ("a" + "b"*)', "expr")),
    )

    assert len(result.states) == 3
    assert len(result.start_states) == 1
    assert len(result.final_states) == 1
    assert result.symbols == {"a", "b"}
    assert len(list(iterate_transitions(result))) == 2

    assert result.accepts("ab")
    assert not result.accepts("a")
    assert not result.accepts("b")
    assert not result.accepts("aaab")
    assert not result.accepts("abbb")


def test_binary_op_rsm():
    value = EpsilonNFA()

    value.add_transition(0, Nonterminal("a"), 1)
    value.add_transition(1, "b", 2)
    value.add_start_state(0)
    value.add_final_state(2)

    check_value(i.LangValueRSM, value, i.interpret(parse('(rec a + "b")', "expr")))

    value = EpsilonNFA()
    value.add_transition(0, "a", 1)
    value.add_transition(1, Nonterminal("b"), 2)
    value.add_start_state(0)
    value.add_final_state(2)

    check_value(i.LangValueRSM, value, i.interpret(parse('("a" + rec b)', "expr")))

    value = EpsilonNFA()
    value.add_transition(0, Nonterminal("a"), 1)
    value.add_transition(0, "b", 1)
    value.add_start_state(0)
    value.add_final_state(1)

    check_value(i.LangValueRSM, value, i.interpret(parse('(rec a | "b")', "expr")))

    value = EpsilonNFA()
    value.add_transition(0, "a", 1)
    value.add_transition(0, Nonterminal("b"), 1)
    value.add_start_state(0)
    value.add_final_state(1)

    check_value(i.LangValueRSM, value, i.interpret(parse('("a" | rec b)', "expr")))

    with pytest.raises(i.InterpretError) as e:
        i.interpret(parse("(rec a & rec b)", "expr"))

    assert (
        str(e.value)
        == "1:2: RSM ($.(Nonterminal.value='b')) created on 1:10 is of type RSM while (one of) FA is expected"
    )


def test_binary_op_set():
    check_value(i.LangValueBoolean, True, i.interpret(parse("({} == {})", "expr")))
    check_value(i.LangValueBoolean, False, i.interpret(parse("({} == 1..2)", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("({ 1 } == 1..2)", "expr")))
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(parse("({ 1, 2 } == { 2, 1 })", "expr")),
    )

    check_value(i.LangValueBoolean, False, i.interpret(parse("({} != {})", "expr")))
    check_value(i.LangValueBoolean, True, i.interpret(parse("({} != 1..2)", "expr")))
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("({ 1 } != 1..2)", "expr")),
    )
    check_value(
        i.LangValueBoolean,
        False,
        i.interpret(parse("({ 1, 2 } != { 2, 1 })", "expr")),
    )

    check_value(i.LangValueSet, set(), i.interpret(parse("({} | {})", "expr")))
    check_value(i.LangValueSet, {1}, i.interpret(parse("({} | 1..2)", "expr")))
    check_value(i.LangValueSet, {1}, i.interpret(parse("({ 1 } | 1..2)", "expr")))
    check_value(i.LangValueSet, {1, 2}, i.interpret(parse("({ 1 } | { 2 })", "expr")))
    check_value(i.LangValueSet, {1, 5, 6}, i.interpret(parse("(5..7 | 1..2)", "expr")))

    check_value(i.LangValueSet, set(), i.interpret(parse("({} & {})", "expr")))
    check_value(i.LangValueSet, set(), i.interpret(parse("({} & 1..2)", "expr")))
    check_value(i.LangValueSet, {1}, i.interpret(parse("({ 1 } & 1..2)", "expr")))
    check_value(i.LangValueSet, set(), i.interpret(parse("({ 1 } & { 2 })", "expr")))
    check_value(i.LangValueSet, {5, 6}, i.interpret(parse("(5..7 & 1..10)", "expr")))


def test_binary_op():
    check_value(
        i.LangValueBoolean,
        True,
        i.interpret(
            parse(
                "(1 * 2 + 4 / 2 - 1 & 3 | 1 == 2 or 1 < 3 and 2 in 2..3 or 3 not in 1..3 | 4..5)",
                "expr",
            )
        ),
    )


def test_load():
    check_value(
        i.LangValueFA,
        fa.graph_to_nfa(graphs.load_by_name("bzip")),
        i.interpret(parse('load "bzip"', "expr")),
    )

    check_value(
        i.LangValueFA,
        fa.graph_to_nfa(graphs.load_by_name("generations")),
        i.interpret(parse('load "generations"', "expr")),
    )

    with tempfile.NamedTemporaryFile(mode="w+") as f:
        f.write(
            """\
0 1 a
1 2 a
2 0 a
2 3 b
3 2 b
"""
        )

        f.seek(0)

        value = EpsilonNFA()
        value.add_transition(0, "a", 1)
        value.add_transition(1, "a", 2)
        value.add_transition(2, "a", 0)
        value.add_transition(2, "b", 3)
        value.add_transition(3, "b", 2)

        for st in range(4):
            value.add_start_state(st)
            value.add_final_state(st)

        check_value(
            i.LangValueFA,
            value,
            i.interpret(parse(f'load "{f.name}"', "expr")),
        )

        value = EpsilonNFA()
        value.add_transition(0, "a", 1)
        value.add_transition(1, "a", 2)
        value.add_transition(2, "a", 0)
        value.add_transition(2, "b", 3)
        value.add_transition(3, "b", 2)

        value.add_start_state(0)
        value.add_start_state(1)
        value.add_final_state(3)

        check_value(
            i.LangValueFA,
            value,
            i.interpret(
                parse(
                    f"""(
load "{f.name}"
with only start states {{ 0, 1 }}
with only final states {{ 3 }}
)""",
                    "expr",
                )
            ),
        )


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
