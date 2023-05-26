from project.fa import (
    states_mapping,
    to_boolean_matrices,
    from_boolean_matrices,
    transitive_closure,
)
from pyformlang.finite_automaton import EpsilonNFA, State, Symbol
from collections import namedtuple
import scipy.sparse as sp
import numpy as np


Nonterminal = namedtuple("Nonterminal", ["value"])


class RFA:
    """
    Recursive Finite Automaton
    """

    def __init__(
        self,
        start_state: Nonterminal,
        fas: dict[Nonterminal, EpsilonNFA],
    ):
        self.start_state = start_state
        self.fas = fas

    def to_boolean_matrices(
        self,
    ) -> dict[Nonterminal, tuple[dict[State, int], dict[Symbol, sp.coo_matrix]]]:
        """
        Returns dict from non-terminal to boolean matrices of FA, where each FA is represented as
        tuple of mapping from state to number and dict of boolean matrices. See fa.py for details.
        """

        result = {}
        for nt, fa in self.fas.items():
            mapping = states_mapping(fa)

            result[nt] = (mapping, to_boolean_matrices(fa, mapping))

        return result

    def minimize(self):
        """
        Return minimal RFA.
        """

        return RFA(
            self.start_state,
            {nt: fa.minimize() for nt, fa in self.fas.items()},
        )


def intersect_with_fa(a: RFA, b: EpsilonNFA) -> EpsilonNFA:
    """
    Intersects RFA with FA. Returns FA, that is, when used in RFA
    with boxes of input RFA, will be box of start non-terminal.
    """

    b_states = len(b.states)
    b_mapping = states_mapping(b)
    b_matrices = {l: m.tolil() for l, m in to_boolean_matrices(b, b_mapping).items()}

    for nt, fa in a.fas.items():
        if fa.accepts(""):
            mat = sp.eye(b_states, dtype=np.bool_).tolil()

        else:
            mat = sp.lil_matrix((b_states, b_states), dtype=np.bool_)

        b_matrices[Symbol(nt)] = mat

    a_matrices = a.to_boolean_matrices()

    a_start_states = {
        nt: {nt_mapping[st] for st in a.fas[nt].start_states}
        for nt, (nt_mapping, _) in a_matrices.items()
    }

    a_final_states = {
        nt: {nt_mapping[st] for st in a.fas[nt].final_states}
        for nt, (nt_mapping, _) in a_matrices.items()
    }

    changed = True
    while changed:
        changed = False

        for nt, (nt_mapping, nt_matrices) in a_matrices.items():
            n = len(nt_mapping) * len(b_mapping)

            same_labels = set.intersection(
                set(nt_matrices.keys()),
                set(b_matrices.keys()),
            )
            result = sp.csr_matrix((n, n), dtype=np.bool_)

            for l in same_labels:
                result += sp.kron(nt_matrices[l], b_matrices[l])

            result = sp.coo_matrix(transitive_closure(result))

            for i, j, v in zip(result.row, result.col, result.data):
                a_i, b_i = i // len(b_mapping), i % len(b_mapping)
                a_j, b_j = j // len(b_mapping), j % len(b_mapping)

                if v and a_i in a_start_states[nt] and a_j in a_final_states[nt]:
                    if b_matrices[nt][b_i, b_j]:
                        continue

                    b_matrices[nt][b_i, b_j] = True
                    changed = True

    # в этом месте я не очень понял, как мне получить РКА из матрицы смежности,
    # но интуитивно кажется, что если мы построим КА для нового нетерминала,
    # используя только полученные переходы по стартовому символу входного РКА,
    # то получим РКА для пересечения

    # а ещё мне не очень понятно, и честно говоря не хочется понимать, как получить
    # не конкретные состояния, а пары состояний из двух автоматов

    b_states = {i: st for st, i in b_mapping.items()}
    result = b_matrices[a.start_state].tocoo()

    result_fa = EpsilonNFA(
        states=b.states.copy(),
        start_state=b.start_states,
        final_states=b.final_states,
    )

    for i, j, v in zip(result.row, result.col, result.data):
        if not v:
            continue

        si, sj = b_states[i], b_states[j]
        result_fa.add_transition(si, a.start_state, sj)

    return result_fa
