from typing import TypeVar

A = TypeVar('A')


class OrientedUnweightenedGraph:

    def __init__(self, vertices: list[A], edges: list[(A, A)]):
        self._vertices = vertices
        self._graph = {v: [] for v in vertices}
        for (src, trg) in edges:
            self._graph[src].append(trg)

    def is_transition(self, src: A, trg: A):
        if src in self._graph.keys():
            if trg in self._graph[src].keys():
                return True
        return False

    def graph(self) -> dict[A, list[A]]:
        return self._graph

    def add_edge(self, src: A, trg: A):
        assert src in self._vertices and trg in self._vertices
        self._graph[src].append(trg)

    def add_vertex(self, vertex: A):
        assert vertex not in self._vertices
        self._graph[vertex] = []

    def rm_edge(self, src: A, trg: A):
        assert src in self._vertices and trg in self._vertices
        if trg in self._graph[src]:
            self._graph[src].remove(trg)