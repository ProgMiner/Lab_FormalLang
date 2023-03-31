from pyformlang.cfg import CFG, Variable, Production
from itertools import permutations
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
