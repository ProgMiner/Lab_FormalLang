from pyformlang.finite_automaton import (
    EpsilonNFA,
    DeterministicFiniteAutomaton,
    State,
    Symbol,
)
import networkx.algorithms.isomorphism as iso
from hypothesis.strategies import from_regex
from scipy.sparse import coo_matrix
from hypothesis import given
import project.graphs as g
import project.fa as fa
import numpy as np
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
    assert iso.is_isomorphic(dfa1.to_networkx(), dfa2.to_networkx())


def test_graph_to_nfa_sanity():
    dfa = fa.regex_to_dfa("c* a b (a|b|c)*")
    nfa = fa.graph_to_nfa(dfa.to_networkx(), [dfa.start_state], dfa.final_states)
    assert dfa.is_equivalent_to(nfa)


def test_graph_to_nfa_real():
    graph = g.load_by_name("generations")

    nfa = fa.graph_to_nfa(graph, [57], [57])
    assert nfa.accepts(["sameAs", "sameAs"])

    nfa = fa.graph_to_nfa(graph, [81])
    assert nfa.accepts(["equivalentClass", "intersectionOf", "rest", "first"])
    assert not nfa.accepts(["intersectionOf", "rest", "first"])

    nfa = fa.graph_to_nfa(graph, final_states=[21])
    assert nfa.accepts(["equivalentClass", "type"])
    assert nfa.accepts(["first", "type", "type"])
    assert not nfa.accepts(["equivalentClass", "intersectionOf", "rest", "first"])


def test_states_mapping():
    dfa = DeterministicFiniteAutomaton(
        states={1, 2, 3, 4},
        input_symbols={"0", "1"},
        start_state=1,
        final_states={1},
    )

    dfa.add_transition(1, "1", 2)
    dfa.add_transition(2, "1", 1)
    dfa.add_transition(2, "0", 4)
    dfa.add_transition(4, "0", 2)
    dfa.add_transition(3, "1", 4)
    dfa.add_transition(4, "1", 3)
    dfa.add_transition(1, "0", 3)
    dfa.add_transition(3, "0", 1)

    mapping = fa.states_mapping(dfa)

    assert len(mapping) == 4
    assert set(mapping.keys()) == {1, 2, 3, 4}
    assert set(mapping.values()) == {0, 1, 2, 3}


def test_to_boolean_matrix():
    dfa = DeterministicFiniteAutomaton(
        states={1, 2, 3, 4},
        input_symbols={"0", "1"},
        start_state=1,
        final_states={1},
    )

    dfa.add_transition(1, "1", 2)
    dfa.add_transition(2, "1", 1)
    dfa.add_transition(2, "0", 4)
    dfa.add_transition(4, "0", 2)
    dfa.add_transition(3, "1", 4)
    dfa.add_transition(4, "1", 3)
    dfa.add_transition(1, "0", 3)
    dfa.add_transition(3, "0", 1)

    mapping = {i + 1: i for i in range(4)}

    boolean_0 = fa.to_boolean_matrix(dfa, "0", mapping)
    assert (
        boolean_0.toarray()
        == np.array(
            [
                [False, False, True, False],
                [False, False, False, True],
                [True, False, False, False],
                [False, True, False, False],
            ]
        )
    ).all()

    boolean_1 = fa.to_boolean_matrix(dfa, "1", mapping)
    assert (
        boolean_1.toarray()
        == np.array(
            [
                [False, True, False, False],
                [True, False, False, False],
                [False, False, False, True],
                [False, False, True, False],
            ]
        )
    ).all()


def test_to_boolean_matrices():
    dfa = DeterministicFiniteAutomaton(
        states={1, 2, 3, 4},
        input_symbols={"0", "1"},
        start_state=1,
        final_states={1},
    )

    dfa.add_transition(1, "1", 2)
    dfa.add_transition(2, "1", 1)
    dfa.add_transition(2, "0", 4)
    dfa.add_transition(4, "0", 2)
    dfa.add_transition(3, "1", 4)
    dfa.add_transition(4, "1", 3)
    dfa.add_transition(1, "0", 3)
    dfa.add_transition(3, "0", 1)

    mapping = {i + 1: i for i in range(4)}
    boolean = fa.to_boolean_matrices(dfa, mapping)

    assert len(boolean) == 2

    assert (
        boolean["0"].toarray()
        == np.array(
            [
                [False, False, True, False],
                [False, False, False, True],
                [True, False, False, False],
                [False, True, False, False],
            ]
        )
    ).all()

    assert (
        boolean["1"].toarray()
        == np.array(
            [
                [False, True, False, False],
                [True, False, False, False],
                [False, False, False, True],
                [False, False, True, False],
            ]
        )
    ).all()


def test_from_boolean_matrices():
    boolean = {
        "0": coo_matrix(
            [
                [False, False, True, False],
                [False, False, False, True],
                [True, False, False, False],
                [False, True, False, False],
            ]
        ),
        "1": coo_matrix(
            [
                [False, True, False, False],
                [True, False, False, False],
                [False, False, False, True],
                [False, False, True, False],
            ]
        ),
    }

    dfa1 = fa.from_boolean_matrices(boolean, [1, 2, 3, 4])
    dfa1.add_start_state(1)
    dfa1.add_final_state(1)

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
    assert iso.is_isomorphic(dfa1.to_networkx(), dfa2.to_networkx())


def test_adjacency_matrix():
    dfa = DeterministicFiniteAutomaton(
        states={1, 2, 3, 4},
        input_symbols={"0", "1"},
        start_state=1,
        final_states={1},
    )

    dfa.add_transition(1, "1", 2)
    dfa.add_transition(2, "1", 1)
    dfa.add_transition(2, "0", 4)
    dfa.add_transition(4, "0", 2)
    dfa.add_transition(3, "1", 4)
    dfa.add_transition(4, "1", 3)
    dfa.add_transition(1, "0", 3)
    dfa.add_transition(3, "0", 1)

    mapping = {i + 1: i for i in range(4)}
    matrix = fa.adjacency_matrix(dfa, mapping)

    assert (
        matrix.toarray()
        == np.array(
            [
                [False, True, True, False],
                [True, False, False, True],
                [True, False, False, True],
                [False, True, True, False],
            ]
        )
    ).all()


def test_intersect_self():
    graph = fa.graph_to_nfa(g.load_by_name("generations"))
    assert graph.is_equivalent_to(fa.intersect(graph, graph))


def test_intersect_empty():
    graph = fa.graph_to_nfa(g.load_by_name("generations"))
    empty = EpsilonNFA()

    assert empty.is_equivalent_to(fa.intersect(empty, graph))


def test_intersect_with_regex():
    graph = g.load_by_name("generations")

    nfa = fa.intersect(fa.graph_to_nfa(graph, [57], [57]), fa.regex_to_dfa("sameAs*"))
    assert nfa.accepts(["sameAs", "sameAs"])

    nfa = fa.intersect(
        fa.graph_to_nfa(graph, [81]),
        fa.regex_to_dfa("equivalentClass intersectionOf rest first"),
    )
    assert nfa.accepts(["equivalentClass", "intersectionOf", "rest", "first"])
    assert not nfa.accepts(["intersectionOf", "rest", "first"])

    nfa = fa.intersect(
        fa.graph_to_nfa(graph, final_states=[21]),
        fa.regex_to_dfa("( equivalentClass | first ) type* type"),
    )
    assert nfa.accepts(["equivalentClass", "type"])
    assert nfa.accepts(["first", "type", "type"])
    assert not nfa.accepts(["type", "type"])
    assert not nfa.accepts(["equivalentClass", "intersectionOf", "rest", "first"])
