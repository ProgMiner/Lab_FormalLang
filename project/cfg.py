from pyformlang.cfg import CFG


def to_wcnf(cfg: CFG) -> CFG:
    """
    Transform given CFG to Weak Chomsky Normal Form.

    WCNF is defined as CFG with only production rules like:
        - A -> B C,
        - A -> a,
        - A -> eps,

    where A, B, C is non-terminals and "a" is a terminal symbol.

    Unlike CNF, in WCNF permitted usege of start symbol in right side of rules and
    not only start symbol could have epsilon in right side of rules.
    """

    cfg = cfg.eliminate_unit_productions().remove_useless_symbols()

    new_productions = cfg._get_productions_with_only_single_terminals()
    new_productions = cfg._decompose_productions(new_productions)

    return CFG(
        start_symbol=cfg.start_symbol,
        productions=set(new_productions),
    )


def from_file(path: str) -> CFG:
    with open(path) as f:
        return CFG.from_text(f.read())
