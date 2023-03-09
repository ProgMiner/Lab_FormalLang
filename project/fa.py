from pyformlang.finite_automaton import DeterministicFiniteAutomaton, EpsilonNFA
from scipy.sparse import dok_matrix, coo_matrix, csr_matrix, kron
from networkx.classes.multidigraph import MultiDiGraph
from pyformlang.regular_expression import Regex
from project.graphs import summary
from math import log2, ceil
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

    for u, t in fa.to_dict().items():
        for s, vs in t.items():
            if s == label:
                try:
                    for v in vs:
                        result[mapping[u], mapping[v]] = 1
                except TypeError:
                    result[mapping[u], mapping[vs]] = 1

    return coo_matrix(result)


def to_boolean_matrices(
    fa: EpsilonNFA,
    mapping: dict[any, int],
) -> dict[any, coo_matrix]:
    """
    Builds set boolean adjacency matrices of FA for every label.
    """

    return {s: to_boolean_matrix(fa, s, mapping) for s in fa.symbols}


def from_boolean_matrices(
    boolean: dict[any, coo_matrix],
    states: list[any] = None,
) -> EpsilonNFA:
    """
    Builds FA for gives boolean adjacency matrices set.
    If states not set, indices will be used.
    """

    result = EpsilonNFA()

    for label, b in boolean.items():
        for i, j, v in zip(b.row, b.col, b.data):
            if v:
                si, sj = (states[i], states[j]) if states is not None else (i, j)
                result.add_transition(si, label, sj)

    return result


def adjacency_matrix(fa: EpsilonNFA, mapping: dict[any, int]) -> coo_matrix:
    """
    Builds adjacency matrix of FA for all labels.
    """

    n_states = len(fa.states)

    if n_states != len(mapping):
        raise ValueError("mapping isn't complete")

    result = dok_matrix((n_states, n_states), dtype=np.bool_)

    for u, t in fa.to_dict().items():
        for s, vs in t.items():
            try:
                for v in vs:
                    result[mapping[u], mapping[v]] = 1
            except TypeError:
                result[mapping[u], mapping[vs]] = 1

    return coo_matrix(result)


def intersect(a: EpsilonNFA, b: EpsilonNFA) -> EpsilonNFA:
    """
    Intersects two FAs by kronecker product.
    States of result FA is pairs of states of specified FAs.
    """

    a_mapping, b_mapping = states_mapping(a), states_mapping(b)

    a_boolean = to_boolean_matrices(a, a_mapping)
    b_boolean = to_boolean_matrices(b, b_mapping)

    same_labels = set.intersection(set(a_boolean.keys()), set(b_boolean.keys()))
    result_boolean = {
        l: coo_matrix(kron(a_boolean[l], b_boolean[l])) for l in same_labels
    }

    result_states = [None for i in range(len(a_mapping) * len(b_mapping))]
    for a_st, i in a_mapping.items():
        for b_st, j in b_mapping.items():
            result_states[i * len(b_mapping) + j] = (a_st, b_st)

    result = from_boolean_matrices(result_boolean, result_states)

    for a_state in a.start_states:
        for b_state in b.start_states:
            result.add_start_state(
                result_states[a_mapping[a_state] * len(b_mapping) + b_mapping[b_state]]
            )

    for a_state in a.final_states:
        for b_state in b.final_states:
            result.add_final_state(
                result_states[a_mapping[a_state] * len(b_mapping) + b_mapping[b_state]]
            )

    return result


def query_graph(
    regex: str,
    graph: MultiDiGraph,
    start_states: Iterable[str] = None,
    final_states: Iterable[str] = None,
) -> Iterable[tuple[str, str]]:
    """
    Finds all pairs of start and final states such that final state reachable from start state
    with constraints specified by the regex.
    """

    start_states = set(start_states)
    final_states = set(final_states)

    a = regex_to_dfa(regex)
    b = graph_to_nfa(graph, start_states, final_states)
    c = intersect(a, b)

    c_mapping = states_mapping(c)
    c_matrix = adjacency_matrix(c, c_mapping)

    c_closure = csr_matrix(c_matrix)
    for _ in range(ceil(log2(len(c_mapping)))):
        c_closure += c_closure @ c_closure

    start_states = {
        i: s.value for s, i in c_mapping.items() if s.value[1] in start_states
    }
    final_states = {
        i: s.value for s, i in c_mapping.items() if s.value[1] in final_states
    }
    c_closure = coo_matrix(c_closure)

    result = set()
    for i, j, v in zip(c_closure.row, c_closure.col, c_closure.data):
        if v and i in start_states and j in final_states:
            result.add((start_states[i][1], final_states[j][1]))

    return result
