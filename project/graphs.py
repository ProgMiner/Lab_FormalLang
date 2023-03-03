from networkx.drawing import nx_pydot
from collections import namedtuple
from networkx import MultiDiGraph
from typing import Tuple
import cfpq_data as cfpq


GraphSummary = namedtuple("GraphSummary", ["nodes_amount", "edges_amount", "labels"])


def load_by_name(name: str) -> MultiDiGraph:
    """
    Loads graph from dataset by name.
    """

    return cfpq.graph_from_csv(cfpq.download(name))


def summary(graph: MultiDiGraph) -> GraphSummary:
    """
    Returns number of nodes and edges, and set of labels.
    """

    return GraphSummary(
        nodes_amount=graph.number_of_nodes(),
        edges_amount=graph.number_of_edges(),
        labels=set([x for _, _, x in graph.edges(data="label")]),
    )


def load_summary_by_name(name: str) -> GraphSummary:
    """
    Returns summary about graph loaded by name.
    """

    return summary(load_by_name(name))


def build_two_cycles(n: int, m: int, labels: Tuple[str, str]) -> MultiDiGraph:
    """
    Builds graph of two cycles with n and m nodes in cycle respectively.
    Edges of first cycle will have label from first element of pair, edges of second cycle -
    from second element.
    """

    return cfpq.labeled_two_cycles_graph(n, m, labels=labels)


def write_dot(graph: MultiDiGraph, path):
    """
    Writes graph in a DOT format. Path could be a path or file object.
    """

    nx_pydot.write_dot(graph, path)


def build_two_cycles_and_write_dot(n: int, m: int, labels: Tuple[str, str], path):
    """
    Builds graph of two cycles and writes in DOT format.
    """

    write_dot(build_two_cycles(n, m, labels), path)
