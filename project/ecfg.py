from __future__ import annotations

from pyformlang.finite_automaton import EpsilonNFA, Symbol
from pyformlang.regular_expression import Regex
from project.fa import iterate_transitions
from project.rfa import RFA, Nonterminal
from collections import defaultdict


class ECFG:
    """
    Extended Context-Free Grammar
    """

    def __init__(
        self,
        start_symbol: any,
        rules: dict[any, Regex],
    ):
        self.start_symbol = start_symbol
        self.rules = rules

    def to_rfa(self):
        fas = {}

        for nt, rx in self.rules.items():
            fa = rx.to_epsilon_nfa()

            new_fa = EpsilonNFA()

            for s in fa.start_states:
                new_fa.add_start_state(s)

            for s in fa.final_states:
                new_fa.add_final_state(s)

            for u, l, v in iterate_transitions(fa):
                if l.value in self.rules:
                    l = Symbol(Nonterminal(l.value))

                new_fa.add_transition(u, l, v)

            fas[Nonterminal(nt)] = new_fa

        return RFA(Nonterminal(self.start_symbol), fas)

    @staticmethod
    def from_text(text: str, start_symbol: str = None) -> ECFG:
        """
        Parse ECFG from text.
        Each non-empty line of ECFG must have format "N -> regex", where
        N is non-terminal and regex is regular expression in syntax of pyformlang.
        All non-terminals must have strictly one rule.
        All symbols that has no rules assumed as terminals.

        If no start symbol specified, first symbol will be start.
        """

        text = text.strip()
        text = text.split("\n")

        rules = {}
        for line in text:
            line = line.strip()

            if line == "":
                continue

            nt, rx = line.split("->", 1)
            nt, rx = nt.strip(), rx.strip()

            if nt == "":
                raise ValueError("empty non-terminal name")

            if nt in rules:
                raise ValueError("duplicated non-terminal")

            if start_symbol is None:
                start_symbol = nt

            rules[nt] = Regex(rx)

        return ECFG(start_symbol, rules)

    @staticmethod
    def from_file(file) -> ECFG:
        """
        Read ECFG from file by filename.
        """

        with open(file, "r") as f:
            return ECFG.from_text(f.read())

    @staticmethod
    def from_cfg(cfg: CFG) -> ECFG:
        """
        Convert pyformlang CFG to ECGF.
        """

        def escape_regex(s):
            result = ""

            for c in s:
                if c in " .|+*()$":
                    result += f"\\{c}"

                else:
                    result += c

            return result

        rules = defaultdict(list)

        for prod in cfg.productions:
            terms = []

            for x in prod.body:
                terms.append(f"{escape_regex(x.value)}")

            rules[prod.head].append(" ".join(terms))

        rules = {nt: Regex(" | ".join(terms)) for nt, terms in rules.items()}
        return ECFG(cfg.start_symbol, rules)
