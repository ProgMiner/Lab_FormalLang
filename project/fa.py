from pyformlang.finite_automaton import (
    DeterministicFiniteAutomaton,
    EpsilonNFA,
    State,
    Symbol,
)
from networkx.classes.multidigraph import MultiDiGraph
from pyformlang.regular_expression import Regex
from project.graphs import summary
from typing import Iterable


def regex_to_dfa(regex: str) -> DeterministicFiniteAutomaton:
    return Regex(regex).to_epsilon_nfa().minimize()


def graph_to_nfa(
    graph: MultiDiGraph,
    start_states: Iterable[str] = None,
    final_states: Iterable[str] = None,
) -> EpsilonNFA:
    states = {st: State(st) for st in graph.nodes()}
    states_set = set(states.values())

    labels = {s: Symbol(s) for s in summary(graph).labels}
    labels_set = set(labels.values())

    start_states = (
        set([states[st] for st in start_states])
        if start_states is not None
        else states_set
    )

    final_states = (
        set([states[st] for st in final_states])
        if final_states is not None
        else states_set
    )

    nfa = EpsilonNFA(
        states=states_set,
        input_symbols=labels_set,
        start_state=start_states,
        final_states=final_states,
    )

    for f, t, l in graph.edges(data="label"):
        nfa.add_transition(states[f], labels[l], states[t])

    return nfa
