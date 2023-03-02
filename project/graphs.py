from networkx.drawing import nx_pydot
from collections import namedtuple
from networkx import MultiDiGraph
from typing import Tuple
import cfpq_data as cfpq


GraphSummary = namedtuple("GraphSummary", ["nodes_amount", "edges_amount", "labels"])


def load_by_name(name: str) -> MultiDiGraph:
    return cfpq.graph_from_csv(cfpq.download(name))


def summary(graph: MultiDiGraph) -> GraphSummary:
    return GraphSummary(
        nodes_amount=graph.number_of_nodes(),
        edges_amount=graph.number_of_edges(),
        labels=set([x for _, _, x in graph.edges(data="label")]),
    )


def load_summary_by_name(name: str) -> GraphSummary:
    return summary(load_by_name(name))


def build_two_cycles(n: int, m: int, labels: Tuple[str, str]) -> MultiDiGraph:
    return cfpq.labeled_two_cycles_graph(n, m, labels=labels)


def write_dot(graph: MultiDiGraph, path):
    nx_pydot.write_dot(graph, path)


def build_two_cycles_and_write_dot(n: int, m: int, labels: Tuple[str, str], path):
    write_dot(build_two_cycles(n, m, labels), path)
