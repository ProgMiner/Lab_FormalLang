from project.fa import states_mapping, to_boolean_matrices
from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.cfg import Variable
import scipy.sparse as sp


class RFA:
    """
    Recursive Finite Automaton
    """

    def __init__(
        self,
        start_state: Variable,
        fas: dict[Variable, EpsilonNFA],
    ):
        self.start_state = start_state
        self.fas = fas

    def to_boolean_matrices(
        self,
    ) -> dict[Variable, tuple[dict[any, int], dict[any, sp.coo_matrix]]]:
        """
        Returns dict from non-terminal to boolean matrices of FA, where each FA is represented as
        tuple of mapping from state to number and dict of boolean matrices. See fa.py for details.
        """

        result = {}
        for var, fa in self.fas.items():
            mapping = states_mapping(fa)

            result[var] = (mapping, to_boolean_matrices(fa, mapping))

        return result

    def minimize(self):
        """
        Return minimal RFA.
        """

        return RFA(
            self.start_state,
            {var: fa.minimize() for var, fa in self.fas.items()},
        )
