from pyformlang.regular_expression import Regex
from pyformlang.cfg import CFG
from project.ecfg import ECFG


def test_ecfg_from_text():
    e = ECFG.from_text(
        """
S -> num | \\( S \\) | S \\+ S | S - S | S \\* S | S / S
"""
    )

    assert e.start_symbol == "S"
    assert e.rules.keys() == {"S"}

    assert (
        e.rules["S"].get_tree_str()
        == Regex("num | \\( S \\) | S \\+ S | S - S | S \\* S | S / S").get_tree_str()
    )


def non_strict_eq(s1, s2):
    s1 = [l.strip() for l in s1.split("\n") if l.strip() != ""]
    s2 = [l.strip() for l in s2.split("\n") if l.strip() != ""]

    return set(s1) == set(s2)


def test_ecfg_from_cfg():
    c = CFG.from_text(
        """
S -> "TER:(" S "TER:)" | S "TER:+" S | S "TER:-" S | S "TER:*" S | S "TER:/" S
S -> num
"""
    )

    e = ECFG.from_cfg(c)

    assert e.start_symbol == "S"
    assert e.rules.keys() == {"S"}

    assert non_strict_eq(
        e.rules["S"].get_tree_str(),
        Regex("num | \\( S \\) | S \\+ S | S - S | S \\* S | S / S").get_tree_str(),
    )
