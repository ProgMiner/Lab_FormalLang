from networkx.drawing import nx_pydot
from networkx import MultiDiGraph
from typing import Tuple
import cfpq_data as cfpq


def load_by_name(name: str) -> MultiDiGraph:
    return cfpq.graph_from_csv(cfpq.download(name))


def summary(graph) -> Tuple[int, int, set]:
    labels = set([x for _, _, x in graph.edges(data="label")])

    return (graph.number_of_nodes(), graph.number_of_edges(), labels)


def build_two_cycles(n: int, m: int, labels: Tuple[str, str]) -> MultiDiGraph:
    return cfpq.labeled_two_cycles_graph(n, m, labels=labels)


def write_dot(graph, path):
    nx_pydot.write_dot(graph, path)
