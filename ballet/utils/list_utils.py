from typing import Callable, TypeVar, Iterable, Optional

A = TypeVar('A')
B = TypeVar('B')


def map_index(f: Callable[[A, int], B], seq: list[A]) -> list[B]:
    return [f(a, i) for i, a in enumerate(seq)]


def flatmap(f: Callable[[A], Iterable[B]], seq: list[A]) -> list[B]:
    return sum([list(f(s)) for s in seq], [])


def find(p: Callable[[A], bool], seq: list[A]) -> Optional[A]:
    for a in seq:
        if p(a):
            return a
    return None


def exists(p: Callable[[A], bool], seq: list[A]) -> bool:
    for a in seq:
        if p(a):
            return True
    return False


def findAll(p: Callable[[A], bool], seq: list[A]) -> list[A]:
    return [a for a in seq if p(a)]


def indexify(seq: list[A],starter:int=0) -> list[(A,int)]:
    return list(zip(seq, range(starter, len(seq)+starter)))


def difference(l1: Iterable[A], l2: Iterable[A]):
    return [x for x in l2 if x not in set(l1)] + [x for x in l1 if x not in set(l2)]


def add_if_no_exist(l: list[A], v: A):
    return l + [v] if v not in l else l

def intersection(lst1: Iterable[A], lst2: Iterable[A]):
    return [value for value in lst1 if value in lst2]


def reverse(it: Iterable[A]) -> list[A]:
    return list(it)[::-1]


def split(p: Callable[[A], bool], lst: Iterable[A]) -> tuple[list[A], list[A]]:
    return [x for x in lst if p(x)], [x for x in lst if not p(x)]


def sum_lists(l1: list[A], l2: list[A]) -> list[A]:
    return l1 + l2


def indexOf(v: A, l: list[A], default: int = -1) -> int:
    for i in range(len(l)):
        if l[i] == v:
            return i
    return default


def forall(p: Callable[[A], bool], l: list[A]) -> bool:
    return not exists(lambda a: not p(a), l)


def count(p: Callable[[A], bool], l: list[A]) -> int:
    return sum([1 if p(a) else 0 for a in l])
            