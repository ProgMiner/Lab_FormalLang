from pyformlang.finite_automaton import DeterministicFiniteAutomaton, EpsilonNFA
from networkx.classes.multidigraph import MultiDiGraph
from pyformlang.regular_expression import Regex
from project.graphs import summary
from math import log2, ceil
from typing import Iterable
import scipy.sparse as sp
import numpy as np


def regex_to_dfa(regex: str) -> DeterministicFiniteAutomaton:
    """
    Builds DFA for regular expression written in format:
    https://pyformlang.readthedocs.io/en/latest/usage.html#regular-expression.
    """

    return Regex(regex).to_epsilon_nfa().minimize()


def graph_to_nfa(
    graph: MultiDiGraph,
    start_states: Iterable[any] = None,
    final_states: Iterable[any] = None,
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
) -> sp.coo_matrix:
    """
    Builds boolean adjacency matrix of FA for specified label.
    """

    n_states = len(fa.states)

    if n_states != len(mapping):
        raise ValueError("mapping isn't complete")

    result = sp.dok_matrix((n_states, n_states), dtype=np.bool_)

    for u, t in fa.to_dict().items():
        for s, vs in t.items():
            if s == label:
                try:
                    for v in vs:
                        result[mapping[u], mapping[v]] = 1
                except TypeError:
                    result[mapping[u], mapping[vs]] = 1

    return sp.coo_matrix(result)


def to_boolean_matrices(
    fa: EpsilonNFA,
    mapping: dict[any, int],
) -> dict[any, sp.coo_matrix]:
    """
    Builds set boolean adjacency matrices of FA for every label.
    """

    return {s: to_boolean_matrix(fa, s, mapping) for s in fa.symbols}


def from_boolean_matrices(
    boolean: dict[any, sp.coo_matrix],
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


def adjacency_matrix(fa: EpsilonNFA, mapping: dict[any, int]) -> sp.coo_matrix:
    """
    Builds adjacency matrix of FA for all labels.
    """

    n_states = len(fa.states)

    if n_states != len(mapping):
        raise ValueError("mapping isn't complete")

    result = sp.dok_matrix((n_states, n_states), dtype=np.bool_)

    for u, t in fa.to_dict().items():
        for s, vs in t.items():
            try:
                for v in vs:
                    result[mapping[u], mapping[v]] = 1
            except TypeError:
                result[mapping[u], mapping[vs]] = 1

    return sp.coo_matrix(result)


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
        l: sp.coo_matrix(sp.kron(a_boolean[l], b_boolean[l])) for l in same_labels
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


def query_graph_kron(
    regex: str,
    graph: MultiDiGraph,
    start_states: Iterable[any] = None,
    final_states: Iterable[any] = None,
) -> Iterable[tuple[any, any]]:
    """
    Finds all pairs of start and final states such that final state reachable from start state
    with constraints specified by the regex.
    """

    a = regex_to_dfa(regex)
    b = graph_to_nfa(graph, start_states, final_states)
    c = intersect(a, b)

    c_mapping = states_mapping(c)
    c_matrix = adjacency_matrix(c, c_mapping)

    c_closure = sp.csr_matrix(c_matrix)
    for _ in range(ceil(log2(len(c_mapping)))):
        c_closure += c_closure @ c_closure

    start_states = {i: s.value for s, i in c_mapping.items() if s in c.start_states}
    final_states = {i: s.value for s, i in c_mapping.items() if s in c.final_states}
    c_closure = sp.coo_matrix(c_closure)

    result = set()
    for i, j, v in zip(c_closure.row, c_closure.col, c_closure.data):
        if v and i in start_states and j in final_states:
            result.add((start_states[i][1], final_states[j][1]))

    return result


def regexp_reachability(
    regexp: EpsilonNFA,
    graph: EpsilonNFA,
    start_nodes: Iterable[any],
    for_each: bool,
):
    """
    Find all final nodes reachable from specified start nodes with RegExp constraints.

    If `for_each` specified, return value is dict of start state to nodes, otherwise is just
    set of final nodes.

    Graph is represented as FA only for convenience, them start and final states are ignored.
    """

    regexp = regexp.minimize()

    a_mapping, b_mapping = states_mapping(regexp), states_mapping(graph)

    a_boolean = to_boolean_matrices(regexp, a_mapping)
    b_boolean = to_boolean_matrices(graph, b_mapping)

    same_labels = set.intersection(set(a_boolean.keys()), set(b_boolean.keys()))

    # NOTE: matrices are transposed
    both_boolean = {
        l: sp.block_diag((a_boolean[l], b_boolean[l])).transpose() for l in same_labels
    }

    n = len(a_mapping)  # number of regexp states
    m = len(b_mapping)  # number of graph nodes

    if for_each:
        start_nodes_sets = {frozenset({x}) for x in start_nodes}
    else:
        start_nodes_sets = {frozenset(start_nodes)}

    del start_nodes
    final_states = {a_mapping[i] for i in regexp.final_states}

    result = {}
    for start_nodes in start_nodes_sets:
        current = {
            (a_mapping[i], b_mapping[j])
            for i in regexp.start_states
            for j in start_nodes
        }

        visited = set()
        while current:
            visited |= current

            front = sp.dok_matrix((m, n), dtype=np.bool_)
            for (i, j) in current:
                front[j, i] = 1

            front = sp.vstack((sp.identity(n, dtype=np.bool_), front), format="csr")

            current = set()
            for adj_mat in both_boolean.values():
                next_front = sp.coo_matrix(adj_mat @ front)

                a_states = [[] for _ in range(n)]
                b_states = [[] for _ in range(n)]
                for i, j, v in zip(next_front.row, next_front.col, next_front.data):
                    if not v:
                        continue

                    if i < n:
                        a_states[j].append(i)
                    else:
                        b_states[j].append(i - n)

                current |= {
                    (i, j) for k in range(n) for i in a_states[k] for j in b_states[k]
                }

            current -= visited

        result[frozenset(start_nodes)] = {j for i, j in visited if i in final_states}

    b_states = [j for _, j in sorted([(idx, s) for s, idx in b_mapping.items()])]

    if for_each:
        return {x: {b_states[j] for j in js} for (x,), js in result.items()}

    else:
        (result,) = result.values()
        return {b_states[j] for j in result}


def query_graph_bfs(
    regex: str,
    graph: MultiDiGraph,
    start_states: Iterable[any] = None,
    final_states: Iterable[any] = None,
    for_each: bool = False,
):
    """
    Finds all nodes in graph reachable from start nodes with RegExp constraints.

    If `for_each` is `True`, returns dict of start state to set of reachable nodes,
    otherwise returns one set for all start nodes.

    If final states specified, it will be used to filter results.
    """

    a = regex_to_dfa(regex)
    b = graph_to_nfa(graph, [], [])
    result = regexp_reachability(a, b, start_states, for_each)

    if final_states is not None:
        if for_each:
            result = {
                i: {j for j in js if j in final_states} for i, js in result.items()
            }

        else:
            result = {i for i in result if i in final_states}

    return result


def union(a: EpsilonNFA, b: EpsilonNFA) -> EpsilonNFA:
    a_states = {st: 2 + i for i, st in enumerate(a.states)}
    b_states = {st: 2 + len(a.states) + i for i, st in enumerate(b.states)}
    s, t = 0, 1

    result = EpsilonNFA(
        states=set({s, t} | a_states.keys() | b_states.keys()),
        input_symbols=set(a.symbols | b.symbols),
        start_state={s},
        final_states={t},
    )

    result.add_transitions(
        [
            (a_states[u], l, a_states[v])
            for u, x in a.to_dict().items()
            for l, vs in x.items()
            for v in vs
        ]
    )

    result.add_transitions(
        [
            (b_states[u], l, b_states[v])
            for u, x in b.to_dict().items()
            for l, vs in x.items()
            for v in vs
        ]
    )

    result.add_transitions([(s, "epsilon", a_states[x]) for x in a.start_states])
    result.add_transitions([(s, "epsilon", b_states[x]) for x in b.start_states])

    result.add_transitions([(a_states[x], "epsilon", t) for x in a.final_states])
    result.add_transitions([(b_states[x], "epsilon", t) for x in b.final_states])

    return result


def kleene_star(fa: EpsilonNFA) -> EpsilonNFA:
    fa_states = {st: 2 + i for i, st in enumerate(fa.states)}
    s, t = 0, 1

    result = EpsilonNFA(
        states=set({0, 1} | fa.states),
        input_symbols=fa.symbols.copy(),
        start_state={s},
        final_states={t},
    )

    result.add_transitions(
        [
            (fa_states[u], l, fa_states[v])
            for u, x in fa.to_dict().items()
            for l, vs in x.items()
            for v in vs
        ]
    )

    result.add_transitions([(s, "epsilon", fa_states[x]) for x in fa.start_states])
    result.add_transitions([(fa_states[x], "epsilon", t) for x in fa.final_states])
    result.add_transitions([(s, "epsilon", t), (t, "epsilon", s)])

    return result
