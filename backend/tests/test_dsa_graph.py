"""
Unit tests for UndirectedGraph encapsulation and operations.
"""

import pytest
from app.dsa.graph import UndirectedGraph


def test_graph_add_and_remove_vertex():
    graph = UndirectedGraph()
    assert graph.add_vertex("u1") is True
    assert graph.add_vertex("u1") is False  # Idempotent
    assert graph.has_vertex("u1") is True
    assert graph.vertex_count() == 1

    assert graph.remove_vertex("u1") is True
    assert graph.remove_vertex("u1") is False
    assert graph.has_vertex("u1") is False
    assert graph.vertex_count() == 0


def test_graph_add_and_remove_edge():
    graph = UndirectedGraph()
    assert graph.add_edge("u1", "u2") is True
    assert graph.add_edge("u1", "u2") is False  # Already present
    assert graph.add_edge("u2", "u1") is False  # Undirected symmetry
    assert graph.has_edge("u1", "u2") is True
    assert graph.has_edge("u2", "u1") is True
    assert graph.edge_count() == 1

    assert graph.remove_edge("u1", "u2") is True
    assert graph.remove_edge("u1", "u2") is False
    assert graph.has_edge("u1", "u2") is False
    assert graph.has_edge("u2", "u1") is False
    assert graph.edge_count() == 0


def test_graph_self_connection_prohibited():
    graph = UndirectedGraph()
    with pytest.raises(ValueError, match="Self-connections are prohibited"):
        graph.add_edge("u1", "u1")


def test_graph_vertex_removal_cleans_edges():
    graph = UndirectedGraph()
    graph.add_edge("u1", "u2")
    graph.add_edge("u1", "u3")
    assert graph.edge_count() == 2

    # Removing u1 must remove edges (u1, u2) and (u1, u3)
    assert graph.remove_vertex("u1") is True
    assert graph.edge_count() == 0
    assert graph.get_neighbors("u2") == set()
    assert graph.get_neighbors("u3") == set()


def test_graph_degree():
    graph = UndirectedGraph()
    graph.add_vertex("isolated")
    assert graph.degree("isolated") == 0

    graph.add_edge("hub", "spoke1")
    graph.add_edge("hub", "spoke2")
    graph.add_edge("hub", "spoke3")
    assert graph.degree("hub") == 3
    assert graph.degree("spoke1") == 1

    with pytest.raises(KeyError):
        graph.degree("nonexistent")


def test_graph_mutual_connections():
    graph = UndirectedGraph()
    # u1 and u2 both connect to m1, m2
    graph.add_edge("u1", "m1")
    graph.add_edge("u1", "m2")
    graph.add_edge("u2", "m1")
    graph.add_edge("u2", "m2")
    # u1 also connects to x1, u2 connects to x2
    graph.add_edge("u1", "x1")
    graph.add_edge("u2", "x2")

    mutuals = graph.mutual_connections("u1", "u2")
    assert mutuals == ["m1", "m2"]

    # Same user or non-existent user returns empty list
    assert graph.mutual_connections("u1", "u1") == []
    assert graph.mutual_connections("u1", "missing") == []


def test_graph_encapsulation_prevents_external_mutation():
    """Verify callers cannot mutate internal graph adjacency sets via returned copies."""
    graph = UndirectedGraph()
    graph.add_edge("u1", "u2")

    # 1. Mutate neighbor set copy
    neighbors = graph.get_neighbors("u1")
    neighbors.add("rogue_node")
    assert "rogue_node" not in graph.get_neighbors("u1")
    assert graph.has_edge("u1", "rogue_node") is False

    # 2. Mutate all_vertices set copy
    vertices = graph.all_vertices()
    vertices.add("phantom_vertex")
    assert "phantom_vertex" not in graph.all_vertices()
    assert graph.has_vertex("phantom_vertex") is False
