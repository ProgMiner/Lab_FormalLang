from pyformlang.finite_automaton import DeterministicFiniteAutomaton, EpsilonNFA
from networkx.classes.multidigraph import MultiDiGraph
from pyformlang.regular_expression import Regex
from project.graphs import summary
from typing import Iterable


def regex_to_dfa(regex: str) -> DeterministicFiniteAutomaton:
    """
    Builds DFA for regular expression written in format:
    https://pyformlang.readthedocs.io/en/latest/usage.html#regular-expression.
    """

    return Regex(regex).to_epsilon_nfa().minimize()


def graph_to_nfa(
    graph: MultiDiGraph,
    start_states: Iterable[str] = None,
    final_states: Iterable[str] = None,
) -> EpsilonNFA:
    """
    Builds NFA from multi-digraph.
    If start states and/or final states aren't specified, all states will be start/final.
    """

    states = set(graph.nodes())
    labels = summary(graph).labels

    start_states = set(start_states) if start_states is not None else set(states)
    final_states = set(final_states) if final_states is not None else set(states)

    nfa = EpsilonNFA(
        states=states,
        input_symbols=labels,
        start_state=start_states,
        final_states=final_states,
    )

    nfa.add_transitions([(f, l, t) for f, t, l in graph.edges(data="label")])
    return nfa
