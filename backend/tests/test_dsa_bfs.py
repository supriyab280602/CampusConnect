"""
Unit tests for BFS shortest path algorithm.
"""

from app.dsa.graph import UndirectedGraph
from app.dsa.bfs import bfs_shortest_path


def test_bfs_source_equals_target():
    graph = UndirectedGraph()
    graph.add_vertex("u1")
    path, dist = bfs_shortest_path(graph, "u1", "u1")
    assert path == ["u1"]
    assert dist == 0


def test_bfs_direct_connection():
    graph = UndirectedGraph()
    graph.add_edge("u1", "u2")
    path, dist = bfs_shortest_path(graph, "u1", "u2")
    assert path == ["u1", "u2"]
    assert dist == 1


def test_bfs_multi_hop_path():
    graph = UndirectedGraph()
    # Chain: A - B - C - D - E
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "D")
    graph.add_edge("D", "E")

    path, dist = bfs_shortest_path(graph, "A", "E")
    assert path == ["A", "B", "C", "D", "E"]
    assert dist == 4


def test_bfs_finds_shortest_in_cyclic_graph():
    graph = UndirectedGraph()
    # Path 1: A - B - C - D (length 3)
    # Path 2: A - X - D     (length 2)
    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_edge("C", "D")
    graph.add_edge("A", "X")
    graph.add_edge("X", "D")

    path, dist = bfs_shortest_path(graph, "A", "D")
    assert path == ["A", "X", "D"]
    assert dist == 2


def test_bfs_disconnected_components():
    graph = UndirectedGraph()
    graph.add_edge("A", "B")
    graph.add_edge("C", "D")

    path, dist = bfs_shortest_path(graph, "A", "D")
    assert path is None
    assert dist == -1


def test_bfs_missing_vertex():
    graph = UndirectedGraph()
    graph.add_edge("A", "B")

    path, dist = bfs_shortest_path(graph, "A", "Z")
    assert path is None
    assert dist == -1

    path, dist = bfs_shortest_path(graph, "Y", "Z")
    assert path is None
    assert dist == -1
