from typing import TypeVar

A = TypeVar('A')


class OrientedUnweightenedGraph:

    def __init__(self, vertices: list[A], edges: list[(A, A)]):
        self._vertices = vertices
        self._out_edges = {v: [] for v in vertices}
        self._in_edges = {v: [] for v in vertices}
        for (src, trg) in edges:
            self._out_edges[src].append(trg)
            self._in_edges[trg].append(src)

    def is_transition(self, src: A, trg: A):
        if src in self._out_edges.keys():
            if trg in self._out_edges[src].keys():
                return True
        return False

    def graph(self) -> dict[A, list[A]]:
        return self._out_edges

    def add_edge(self, src: A, trg: A):
        assert src in self._vertices and trg in self._vertices
        self._out_edges[src].append(trg)
        self._in_edges[trg].append(src)

    def add_vertex(self, vertex: A):
        assert vertex not in self._vertices
        self._out_edges[vertex] = []

    def rm_edge(self, src: A, trg: A):
        assert src in self._vertices and trg in self._vertices
        if trg in self._out_edges[src]:
            self._out_edges[src].remove(trg)
            self._in_edges[trg].remove(src)

    def in_edges(self) -> dict[A, list[A]]:
        return self._in_edges