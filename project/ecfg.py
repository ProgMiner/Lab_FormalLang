from __future__ import annotations

from pyformlang.regular_expression import Regex
from pyformlang.cfg import Variable
from collections import defaultdict
from project.rfa import RFA


class ECFG:
    """
    Extended Context-Free Grammar
    """

    def __init__(
        self,
        start_symbol: str,
        rules: dict[str, Regex],
    ):
        self.start_symbol = start_symbol
        self.rules = rules

    def to_rfa(self):
        fas = {}

        for nt, rx in self.rules.items():
            fas[Variable(nt)] = rx.to_epsilon_nfa()

        return RFA(Variable(self.start_symbol), fas)

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

        for nt, terms in rules.items():
            print(nt, " | ".join(terms))

        rules = {nt: Regex(" | ".join(terms)) for nt, terms in rules.items()}
        return ECFG(cfg.start_symbol, rules)
