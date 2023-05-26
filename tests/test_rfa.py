import project.graphs as graphs
from project.ecfg import ECFG
import project.rfa as rfa
import project.fa as fa


def test_Nonterminal():
    assert rfa.Nonterminal("A") == rfa.Nonterminal("A")

    assert "A" != rfa.Nonterminal("A")
    assert rfa.Nonterminal("A") != "A"


def test_intersect_with_fa_one_nonterminal():
    graph = fa.graph_to_nfa(graphs.build_two_cycles(1, 2, ("a", "b")))

    grammar = ECFG.from_text("S -> a S b | epsilon").to_rfa().minimize()

    result = rfa.intersect_with_fa(grammar, graph)

    assert result.states == graph.states
    assert result.start_states == graph.start_states
    assert result.final_states == graph.final_states

    assert set(fa.iterate_transitions(result)) == {
        (0, rfa.Nonterminal("S"), 0),
        (0, rfa.Nonterminal("S"), 2),
        (0, rfa.Nonterminal("S"), 3),
        (1, rfa.Nonterminal("S"), 0),
        (1, rfa.Nonterminal("S"), 1),
        (1, rfa.Nonterminal("S"), 2),
        (1, rfa.Nonterminal("S"), 3),
        (2, rfa.Nonterminal("S"), 2),
        (3, rfa.Nonterminal("S"), 3),
    }


def test_intersect_with_fa_generic_with_eps():
    graph = fa.graph_to_nfa(graphs.build_two_cycles(1, 2, ("a", "b")))

    grammar = (
        ECFG.from_text(
            """
S -> A | epsilon
A -> a S b
"""
        )
        .to_rfa()
        .minimize()
    )

    result = rfa.intersect_with_fa(grammar, graph)

    assert result.states == graph.states
    assert result.start_states == graph.start_states
    assert result.final_states == graph.final_states

    assert set(fa.iterate_transitions(result)) == {
        (0, rfa.Nonterminal("S"), 0),
        (0, rfa.Nonterminal("S"), 2),
        (0, rfa.Nonterminal("S"), 3),
        (1, rfa.Nonterminal("S"), 0),
        (1, rfa.Nonterminal("S"), 1),
        (1, rfa.Nonterminal("S"), 2),
        (1, rfa.Nonterminal("S"), 3),
        (2, rfa.Nonterminal("S"), 2),
        (3, rfa.Nonterminal("S"), 3),
    }


def test_intersect_with_fa_generic():
    graph = fa.graph_to_nfa(graphs.build_two_cycles(1, 2, ("a", "b")))

    grammar = (
        ECFG.from_text(
            """
S -> A | a b
A -> a S b
"""
        )
        .to_rfa()
        .minimize()
    )

    result = rfa.intersect_with_fa(grammar, graph)

    assert result.states == graph.states
    assert result.start_states == graph.start_states
    assert result.final_states == graph.final_states

    assert set(fa.iterate_transitions(result)) == {
        (0, rfa.Nonterminal("S"), 0),
        (0, rfa.Nonterminal("S"), 2),
        (0, rfa.Nonterminal("S"), 3),
        (1, rfa.Nonterminal("S"), 0),
        (1, rfa.Nonterminal("S"), 2),
        (1, rfa.Nonterminal("S"), 3),
    }
