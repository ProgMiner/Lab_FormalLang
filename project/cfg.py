from pyformlang.cfg import CFG, Epsilon, Terminal, Variable
from networkx import MultiDiGraph
from typing import Iterable
from math import log2, ceil
from project import graphs
import scipy.sparse as sp
import numpy as np


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


def hellings(
    graph: MultiDiGraph | str,
    cfg: CFG | str,
) -> set[tuple[int, Variable, int]]:
    """
    Hellings' algorithm got graph and context free grammar and returns a set of tuples
    (vertex, nonterminal, vertex) so that from second vertex reachable from first by nonterminal.

    In other words, it is edges of transitive closure of intersection of given graph and CFG.

    If graph specified by string, it loaded from dataset by name using project.graphs.load_by_name.
    If CFG specified by string, it loaded from text using CFG.from_text.
    """

    if isinstance(graph, str):
        graph = graphs.load_by_name(graph)

    if isinstance(cfg, str):
        cfg = CFG.from_text(cfg)

    cfg = to_wcnf(cfg)

    r = set()
    for p in cfg.productions:
        name = p.head

        if len(p.body) == 0:
            r |= {(v, name, v) for v in graph.nodes}

        if len(p.body) != 1:
            continue

        term = p.body[0]
        if isinstance(term, Terminal):
            term = term.value

            r |= {(v, name, u) for (v, u, l) in graph.edges(data="label") if l == term}

    m = list(r)

    while len(m) > 0:
        v, ni, u = m.pop()

        new_r = set()
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
                new_r.add((v1, nk, u))

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
                new_r.add((v, nk, v1))

        r |= new_r

    return r


def cfpq_hellings(
    graph: MultiDiGraph | str,
    cfg: CFG | str,
    start_nodes: Iterable[any] = None,
    final_nodes: Iterable[any] = None,
    nonterminal: Variable = None,
) -> set[tuple[int, int]]:
    """
    Context free path querying graph use Hellings' algorithm.

    If graph specified by string, it loaded from dataset by name using project.graphs.load_by_name.
    If CFG specified by string, it loaded from text using CFG.from_text.
    """

    if isinstance(graph, str):
        graph = graphs.load_by_name(graph)

    if isinstance(cfg, str):
        cfg = CFG.from_text(cfg)

    if start_nodes is None:
        start_nodes = set(graph.nodes)

    if final_nodes is None:
        final_nodes = set(graph.nodes)

    if nonterminal is None:
        nonterminal = cfg.start_symbol

    result = set()
    for v, n, u in hellings(graph, cfg):
        if n == nonterminal and v in start_nodes and u in final_nodes:
            result.add((v, u))

    return result


def matrix_algorithm(
    graph: MultiDiGraph | str,
    cfg: CFG | str,
) -> set[tuple[int, Variable, int]]:
    """
    Matrix algorithm got graph and context free grammar and returns a set of tuples
    (vertex, nonterminal, vertex) so that from second vertex reachable from first by nonterminal.

    In other words, it is edges of transitive closure of intersection of given graph and CFG.

    If graph specified by string, it loaded from dataset by name using project.graphs.load_by_name.
    If CFG specified by string, it loaded from text using CFG.from_text.
    """

    if isinstance(graph, str):
        graph = graphs.load_by_name(graph)

    if isinstance(cfg, str):
        cfg = CFG.from_text(cfg)

    cfg = to_wcnf(cfg)

    n = graph.number_of_nodes()
    matrices = {nt: sp.dok_matrix((n, n), dtype=np.bool_) for nt in cfg.variables}

    for p in cfg.productions:
        matrix = matrices[p.head]

        if len(p.body) == 0:
            for i in range(n):
                matrix[i, i] = 1

        if len(p.body) != 1:
            continue

        term = p.body[0]
        if isinstance(term, Terminal):
            term = term.value

            for (v, u, l) in graph.edges(data="label"):
                if l == term:
                    matrix[v, u] = 1

    matrices = {nt: m.tocsr() for nt, m in matrices.items()}

    while True:
        new_matrices = {
            nt: sp.csr_matrix((n, n), dtype=np.bool_) for nt in cfg.variables
        }

        for p in cfg.productions:
            if len(p.body) != 2:
                continue

            new_matrices[p.head] += matrices[p.body[0]] @ matrices[p.body[1]]

        old_nonzeroes = {nt: m.count_nonzero() for nt, m in matrices.items()}

        for nt, m in new_matrices.items():
            matrices[nt] += m

        new_nonzeroes = {nt: m.count_nonzero() for nt, m in matrices.items()}

        if old_nonzeroes == new_nonzeroes:
            break

    result = set()
    for nt, m in matrices.items():
        m = m.tocoo()

        for i, j, v in zip(m.row, m.col, m.data):
            if v:
                result.add((i, nt, j))

    return result
