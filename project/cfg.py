from pyformlang.cfg import CFG, Epsilon, Terminal, Variable
from networkx import MultiDiGraph


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
    """
    Read CFG from file by path.
    Syntax of file is defined by CFG.from_text.
    """

    with open(path) as f:
        return CFG.from_text(f.read())


def hellings(graph: MultiDiGraph, cfg: CFG) -> set[tuple[int, Variable, int]]:
    """
    Hellings' algorithm got graph and context free grammar and returns a set of tuples
    (vertex, nonterminal, vertex) so that from second vertex reachable from first by nonterminal.

    In other words, it is edges of transitive closure of intersection of given graph and CFG.
    """

    cfg = to_wcnf(cfg)

    r = set()
    for p in cfg.productions:
        body = p.body

        print(body)

        if len(p.body) == 0:
            r |= {(v, name, v) for v in graph.nodes}

        if len(p.body) != 1:
            continue

        name, term = p.head, p.body[0]

        print(name, term)

        if isinstance(term, Variable):
            r |= {(v, name, u) for (v, u, l) in graph.edges(data="label") if l == term}

    m = list(r)

    while len(m) > 0:
        v, ni, u = m.pop()

        for v1, nj, u1 in r:
            if u1 != v:
                continue

            for p in cfg.productions:
                if len(p.body) != 2:
                    continue

                if p.body != [nj, ni]:
                    continue

                nk = p.head
                if (v1, nk, u) in r:
                    continue

                m.append((v1, nk, u))
                r.add((v1, nk, u))

        for u1, nj, v1 in r:
            if u1 != u:
                continue

            for p in cfg.productions:
                if len(p.body) != 2:
                    continue

                if p.body != [ni, nj]:
                    continue

                nk = p.head
                if (v, nk, v1) in r:
                    continue

                m.append((v, nk, v1))
                r.add((v, nk, v1))

    return r
