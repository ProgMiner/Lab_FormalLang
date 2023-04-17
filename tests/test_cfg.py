from pyformlang.cfg import CFG, Variable
import project.graphs as graphs
import project.cfg as cfg
import tempfile
import re


def test_to_wcnf():
    grammar = CFG.from_text(
        """\
S -> "TER:(" S "TER:)" | S "TER:+" S | S "TER:-" S | S "TER:*" S | S "TER:/" S
S -> num
"""
    )

    wcnf_grammar = cfg.to_wcnf(grammar)
    actual = wcnf_grammar.to_text()

    expected = """\
S -> "VAR:(#CNF#" C#CNF#1
C#CNF#1 -> S "VAR:)#CNF#"

S -> S C#CNF#2
C#CNF#2 -> "VAR:+#CNF#" S

S -> S C#CNF#3
C#CNF#3 -> "VAR:/#CNF#" S

S -> S C#CNF#4
C#CNF#4 -> "VAR:*#CNF#" S

S -> S C#CNF#5
C#CNF#5 -> "VAR:-#CNF#" S

S -> num

(#CNF# -> (
)#CNF# -> )
+#CNF# -> +
-#CNF# -> -
*#CNF# -> *
/#CNF# -> /
"""

    actual_lines = set([re.sub(r"\d", "", l) for l in actual.split("\n") if l != ""])
    expected_lines = set(
        [re.sub(r"\d", "", l) for l in expected.split("\n") if l != ""]
    )

    assert expected_lines == actual_lines


def test_from_file():
    with tempfile.NamedTemporaryFile(mode="w+") as f:
        f.write(
            """\
S -> "TER:(" S "TER:)" | S "TER:+" S | S "TER:-" S | S "TER:*" S | S "TER:/" S
S -> num
"""
        )

        f.seek(0)
        grammar = cfg.from_file(f.name)

    actual = grammar.to_text()

    expected = """\
S -> ( S )
S -> S + S
S -> S - S
S -> S * S
S -> S / S
S -> num
"""

    actual_lines = set([l for l in actual.split("\n") if l != ""])
    expected_lines = set([l for l in expected.split("\n") if l != ""])

    assert actual_lines == expected_lines


def test_hellings():
    graph = graphs.build_two_cycles(1, 2, ("a", "b"))

    grammar = CFG.from_text("S -> a S | epsilon")

    assert cfg.hellings(graph, grammar) == {
        (0, Variable("S"), 0),
        (1, Variable("S"), 1),
        (2, Variable("S"), 2),
        (3, Variable("S"), 3),
        (0, Variable("S"), 1),
        (1, Variable("S"), 0),
        (1, Variable("a#CNF#"), 0),
        (0, Variable("a#CNF#"), 1),
    }

    grammar = CFG.from_text("S -> S b | epsilon")

    assert cfg.hellings(graph, grammar) == {
        (0, Variable("S"), 0),
        (0, Variable("S"), 2),
        (0, Variable("S"), 3),
        (1, Variable("S"), 1),
        (2, Variable("S"), 0),
        (2, Variable("S"), 2),
        (2, Variable("S"), 3),
        (3, Variable("S"), 0),
        (3, Variable("S"), 2),
        (3, Variable("S"), 3),
        (0, Variable("b#CNF#"), 2),
        (2, Variable("b#CNF#"), 3),
        (3, Variable("b#CNF#"), 0),
    }

    grammar = CFG.from_text("S -> a S b | epsilon")

    assert cfg.hellings(graph, grammar) == {
        (0, Variable("S"), 0),
        (0, Variable("S"), 2),
        (0, Variable("S"), 3),
        (1, Variable("S"), 0),
        (1, Variable("S"), 1),
        (1, Variable("S"), 2),
        (1, Variable("S"), 3),
        (2, Variable("S"), 2),
        (3, Variable("S"), 3),
        (0, Variable("a#CNF#"), 1),
        (1, Variable("a#CNF#"), 0),
        (0, Variable("b#CNF#"), 2),
        (2, Variable("b#CNF#"), 3),
        (3, Variable("b#CNF#"), 0),
        (0, Variable("C#CNF#1"), 0),
        (0, Variable("C#CNF#1"), 2),
        (0, Variable("C#CNF#1"), 3),
        (1, Variable("C#CNF#1"), 0),
        (1, Variable("C#CNF#1"), 2),
        (1, Variable("C#CNF#1"), 3),
        (2, Variable("C#CNF#1"), 3),
        (3, Variable("C#CNF#1"), 0),
    }


def test_cfpq_hellings():
    graph = graphs.build_two_cycles(1, 2, ("a", "b"))

    grammar = CFG.from_text("S -> a S | epsilon")

    assert cfg.cfpq_hellings(graph, grammar, [0]) == ({(0, 0), (0, 1)})

    grammar = CFG.from_text("S -> S b | epsilon")

    assert cfg.cfpq_hellings(graph, grammar, None, [0]) == {(0, 0), (3, 0), (2, 0)}

    grammar = CFG.from_text("S -> a S b | epsilon")

    assert cfg.cfpq_hellings(graph, grammar, [0, 1], [2, 3]) == {
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
    }
