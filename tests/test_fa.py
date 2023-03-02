from pyformlang.finite_automaton import DeterministicFiniteAutomaton, State, Symbol
import networkx.algorithms.isomorphism as iso
from hypothesis.strategies import from_regex
from hypothesis import given
import project.fa as fa
import pytest


@given(from_regex("c*ab(a|b|c)*", fullmatch=True))
def test_regex_to_dfa_sanity(test):
    dfa = fa.regex_to_dfa("c* a b (a|b|c)*")

    print(f"Test: {test}")
    assert dfa.accepts(test)


def test_regex_to_dfa_minimal():
    dfa1 = fa.regex_to_dfa(
        "( 1 ( 0 0 )* ( 1 | 0 1 ( 1 ( 0 ( 0 0 )* 0 1 | 1) )* ( 0 | 1 0 ( 0 0 )* 1 ) ) | 0 ( 1 ( 0 ( 0 0 )* 0 1 | 1 ) )* ( 0 | 1 0 ( 0 0 )* 1 ) )*"
    )

    dfa2 = DeterministicFiniteAutomaton(
        states={1, 2, 3, 4},
        input_symbols={"0", "1"},
        start_state=1,
        final_states={1},
    )

    dfa2.add_transition(1, "1", 2)
    dfa2.add_transition(2, "1", 1)
    dfa2.add_transition(2, "0", 4)
    dfa2.add_transition(4, "0", 2)
    dfa2.add_transition(3, "1", 4)
    dfa2.add_transition(4, "1", 3)
    dfa2.add_transition(1, "0", 3)
    dfa2.add_transition(3, "0", 1)

    assert dfa1.is_equivalent_to(dfa2)

    dfa1_graph = dfa1.to_networkx()
    dfa2_graph = dfa2.to_networkx()

    assert iso.is_isomorphic(dfa1_graph, dfa2_graph)
