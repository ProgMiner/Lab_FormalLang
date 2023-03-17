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


def test_query_graph_kron_empty():
    graph = g.load_by_name("generations")
    assert fa.query_graph_kron("", graph, graph.nodes, graph.nodes) == set()


def test_query_graph_kron_some():
    graph = g.load_by_name("generations")

    assert fa.query_graph_kron("sameAs*", graph, [57], [57]) == {(57, 57)}
    assert fa.query_graph_kron("sameAs sameAs", graph, [57], [57]) == {(57, 57)}

    assert fa.query_graph_kron(
        "equivalentClass intersectionOf rest first",
        graph,
        [81],
        graph.nodes,
    ) == {(81, 34)}

    assert fa.query_graph_kron(
        "( equivalentClass | first ) type* type",
        graph,
        graph.nodes,
        [21],
    ) == {
        (81, 21),
        (6, 21),
        (4, 21),
        (70, 21),
        (92, 21),
        (125, 21),
        (17, 21),
        (127, 21),
        (105, 21),
        (74, 21),
        (118, 21),
        (96, 21),
        (1, 21),
        (63, 21),
        (87, 21),
        (120, 21),
        (109, 21),
        (45, 21),
        (100, 21),
        (47, 21),
        (69, 21),
        (124, 21),
        (51, 21),
        (16, 21),
        (49, 21),
        (79, 21),
        (82, 21),
        (106, 21),
        (97, 21),
        (55, 21),
        (88, 21),
        (121, 21),
        (68, 21),
        (90, 21),
        (123, 21),
    }


def test_regexp_reachability_self():
    graph = fa.graph_to_nfa(g.load_by_name("generations"))
    assert fa.regexp_reachability(graph, graph, graph.states, False) == graph.states


def test_regexp_reachability_empty():
    graph = fa.graph_to_nfa(g.load_by_name("generations"), [], [])
    empty = EpsilonNFA()

    assert fa.regexp_reachability(empty, graph, graph.states, False) == set()


def test_regexp_reachability_with_regex():
    graph = fa.graph_to_nfa(g.load_by_name("generations"), [], [])

    assert fa.regexp_reachability(fa.regex_to_dfa("sameAs*"), graph, [57], False) == {
        57,
        98,
    }

    assert fa.regexp_reachability(fa.regex_to_dfa("sameAs*"), graph, [57], True) == {
        57: {57, 98},
    }

    assert fa.regexp_reachability(
        fa.regex_to_dfa("equivalentClass intersectionOf rest first"),
        graph,
        [81],
        False,
    ) == {34}

    assert fa.regexp_reachability(
        fa.regex_to_dfa("equivalentClass intersectionOf rest first"),
        graph,
        [81],
        True,
    ) == {81: {34}}


def test_query_graph_bfs_empty():
    graph = g.load_by_name("generations")
    assert fa.query_graph_bfs("", graph, graph.nodes, graph.nodes, False) == set()
    assert fa.query_graph_bfs("", graph, graph.nodes, graph.nodes, True) == {
        i: set() for i in graph.nodes
    }


def test_query_graph_bfs_some():
    graph = g.load_by_name("generations")

    assert fa.query_graph_bfs("sameAs*", graph, [57], [57], False) == {57}
    assert fa.query_graph_bfs("sameAs*", graph, [57], [57], True) == {57: {57}}

    assert fa.query_graph_bfs("sameAs sameAs", graph, [57], [57], False) == {57}
    assert fa.query_graph_bfs("sameAs sameAs", graph, [57], [57], True) == {57: {57}}

    assert fa.query_graph_bfs(
        "equivalentClass intersectionOf rest first",
        graph,
        [81],
        graph.nodes,
        False,
    ) == {34}

    assert fa.query_graph_bfs(
        "equivalentClass intersectionOf rest first",
        graph,
        [81],
        graph.nodes,
        True,
    ) == {81: {34}}

    assert fa.query_graph_bfs(
        "( equivalentClass | first ) type* type",
        graph,
        graph.nodes,
        [21],
        False,
    ) == {21}

    assert fa.query_graph_bfs(
        "( equivalentClass | first ) type* type",
        graph,
        graph.nodes,
        [21],
        True,
    ) == {
        0: set(),
        1: {21},
        2: set(),
        3: set(),
        4: {21},
        5: set(),
        6: {21},
        7: set(),
        8: set(),
        9: set(),
        10: set(),
        11: set(),
        12: set(),
        13: set(),
        14: set(),
        15: set(),
        16: {21},
        17: {21},
        18: set(),
        19: set(),
        20: set(),
        21: set(),
        22: set(),
        23: set(),
        24: set(),
        25: set(),
        26: set(),
        27: set(),
        28: set(),
        29: set(),
        30: set(),
        31: set(),
        32: set(),
        33: set(),
        34: set(),
        35: set(),
        36: set(),
        37: set(),
        38: set(),
        39: set(),
        40: set(),
        41: set(),
        42: set(),
        43: set(),
        44: set(),
        45: {21},
        46: set(),
        47: {21},
        48: set(),
        49: {21},
        50: set(),
        51: {21},
        52: set(),
        53: set(),
        54: set(),
        55: {21},
        56: set(),
        57: set(),
        58: set(),
        59: set(),
        60: set(),
        61: set(),
        62: set(),
        63: {21},
        64: set(),
        65: set(),
        66: set(),
        67: set(),
        68: {21},
        69: {21},
        70: {21},
        71: set(),
        72: set(),
        73: set(),
        74: {21},
        75: set(),
        76: set(),
        77: set(),
        78: set(),
        79: {21},
        80: set(),
        81: {21},
        82: {21},
        83: set(),
        84: set(),
        85: set(),
        86: set(),
        87: {21},
        88: {21},
        89: set(),
        90: {21},
        91: set(),
        92: {21},
        93: set(),
        94: set(),
        95: set(),
        96: {21},
        97: {21},
        98: set(),
        99: set(),
        100: {21},
        101: set(),
        102: set(),
        103: set(),
        104: set(),
        105: {21},
        106: {21},
        107: set(),
        108: set(),
        109: {21},
        110: set(),
        111: set(),
        112: set(),
        113: set(),
        114: set(),
        115: set(),
        116: set(),
        117: set(),
        118: {21},
        119: set(),
        120: {21},
        121: {21},
        122: set(),
        123: {21},
        124: {21},
        125: {21},
        126: set(),
        127: {21},
        128: set(),
    }

    assert fa.query_graph_bfs(
        "( equivalentClass | first ) type* type",
        graph,
        graph.nodes,
        for_each=False,
    ) == {88, 9, 21}

    assert fa.query_graph_bfs(
        "( equivalentClass | first ) type* type",
        graph,
        graph.nodes,
        for_each=True,
    ) == {
        0: {9},
        1: {21},
        2: {9},
        3: {9},
        4: {21},
        5: set(),
        6: {21},
        7: {9},
        8: set(),
        9: set(),
        10: set(),
        11: set(),
        12: set(),
        13: set(),
        14: set(),
        15: set(),
        16: {21},
        17: {21},
        18: set(),
        19: {9},
        20: set(),
        21: set(),
        22: set(),
        23: set(),
        24: set(),
        25: set(),
        26: set(),
        27: set(),
        28: set(),
        29: set(),
        30: {9},
        31: set(),
        32: set(),
        33: set(),
        34: set(),
        35: {9},
        36: {9},
        37: {9},
        38: set(),
        39: set(),
        40: set(),
        41: {9},
        42: set(),
        43: {9},
        44: set(),
        45: {21},
        46: set(),
        47: {21},
        48: {9},
        49: {21},
        50: set(),
        51: {21},
        52: set(),
        53: {9},
        54: {9},
        55: {21},
        56: set(),
        57: set(),
        58: set(),
        59: set(),
        60: {9},
        61: set(),
        62: set(),
        63: {21},
        64: set(),
        65: set(),
        66: set(),
        67: set(),
        68: {21},
        69: {88, 21},
        70: {21},
        71: set(),
        72: set(),
        73: set(),
        74: {21},
        75: set(),
        76: set(),
        77: set(),
        78: set(),
        79: {21},
        80: {9},
        81: {21},
        82: {21},
        83: {9},
        84: {9},
        85: {9},
        86: set(),
        87: {21},
        88: {21},
        89: set(),
        90: {21},
        91: set(),
        92: {88, 21},
        93: set(),
        94: set(),
        95: set(),
        96: {21},
        97: {21},
        98: set(),
        99: {9},
        100: {21},
        101: set(),
        102: set(),
        103: set(),
        104: set(),
        105: {21},
        106: {21},
        107: {9},
        108: set(),
        109: {21},
        110: set(),
        111: {9},
        112: set(),
        113: {9},
        114: set(),
        115: {9},
        116: set(),
        117: set(),
        118: {21},
        119: {9},
        120: {21},
        121: {21},
        122: {9},
        123: {21},
        124: {21},
        125: {21},
        126: {9},
        127: {21},
        128: set(),
    }
