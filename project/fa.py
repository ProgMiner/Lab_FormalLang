from pyformlang.finite_automaton import DeterministicFiniteAutomaton, EpsilonNFA
from networkx.classes.multidigraph import MultiDiGraph
from scipy.sparse import dok_matrix, coo_matrix, kron
from pyformlang.regular_expression import Regex
from project.graphs import summary
from typing import Iterable
import numpy as np


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


def states_mapping(fa: EpsilonNFA) -> dict[any, int]:
    """
    Returns dict with FA states names to indices.
    """

    return {s: i for i, s in enumerate(fa.states)}


def to_boolean_matrix(
    fa: EpsilonNFA,
    label: any,
    mapping: dict[any, int],
) -> coo_matrix:
    """
    Builds boolean adjacency matrix of FA for specified label.
    """

    n_states = len(fa.states)

    if n_states != len(mapping):
        raise ValueError("mapping isn't complete")

    result = dok_matrix((n_states, n_states), dtype=np.bool_)

    if fa.is_deterministic():
        for u, t in fa.to_dict().items():
            for s, v in t.items():
                if s == label:
                    result[mapping[u], mapping[v]] = 1

    else:
        for u, t in fa.to_dict().items():
            for s, vs in t.items():
                for v in vs:
                    if s == label:
                        result[mapping[u], mapping[v]] = 1

    return coo_matrix(result)


def to_boolean_matrices(
    fa: EpsilonNFA,
    mapping: dict[any, int],
) -> dict[any, coo_matrix]:
    """
    Builds set boolean adjacency matrices of FA for every label.
    """

    return {s: to_boolean_matrix(fa, s, mapping) for s in fa.symbols}


def from_boolean_matrices(boolean: dict[any, coo_matrix]) -> EpsilonNFA:
    """
    Builds FA for gives boolean adjacency matrices set.
    """

    result = EpsilonNFA()

    for label, b in boolean.items():
        for i, j, v in zip(b.row, b.col, b.data):
            if v:
                result.add_transition(i, label, j)

    return result


def intersect(a: EpsilonNFA, b: EpsilonNFA) -> EpsilonNFA:
    """
    Intersects two FAs by kronecker product.
    """

    a_mapping, b_mapping = states_mapping(a), states_mapping(b)

    a_boolean = to_boolean_matrices(a, a_mapping)
    b_boolean = to_boolean_matrices(b, b_mapping)

    same_labels = set.intersection(set(a_boolean.keys()), set(b_boolean.keys()))
    result_boolean = {l: kron(a_boolean[l], b_boolean[l]) for l in same_labels}

    result = from_boolean_matrices(result_boolean)

    for a_state in a.start_states:
        for b_state in b.start_states:
            result.add_start_state(
                a_mapping[a_state] * len(b_mapping) + b_mapping[b_state]
            )

    for a_state in a.final_states:
        for b_state in b.final_states:
            result.add_final_state(
                a_mapping[a_state] * len(b_mapping) + b_mapping[b_state]
            )

    return result.minimize()
