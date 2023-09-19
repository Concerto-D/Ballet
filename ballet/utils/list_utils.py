from typing import Callable, TypeVar, Iterable, Optional

A = TypeVar('A')
B = TypeVar('B')


def map_index(f: Callable[[A, int], B], seq: list[A]) -> list[B]:
    i = 0
    res = []
    for a in seq:
        res.append(f(a, i))
        i = i + 1
    return res


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
    res = []
    for a in seq:
        if p(a):
            res.append(a)
    return res


def difference(l1: Iterable[A], l2: Iterable[A]):
    s1 = set(l1)
    s2 = set(l2)
    return [x for x in l2 if x not in s1] + [x for x in l1 if x not in s2]


def add_if_no_exist(l: list[A], v: A):
    if not v in l:
        l.append(v)
    return l


def intersection(lst1: Iterable[A], lst2: Iterable[A]):
    return [value for value in lst1 if value in lst2]


def reverse(it: Iterable[A]):
    res = []
    for a in it:
        res.insert(0, a)
    return res


def count(p: Callable[[A], bool], lst: Iterable[A]) -> int:
    res = 0
    for a in lst:
        if p(a):
            res = res + 1
    return res


def split(p: Callable[[A], bool], lst: Iterable[A]) -> tuple[list[A], list[A]]:
    l1: list[A] = []
    l2: list[A] = []
    for a in lst:
        if p(a):
            l1.append(a)
        else:
            l2.append(a)
    return (l1, l2)


def sum_lists(l1: list[A], l2: list[A]) -> list[A]:
    return l1 + l2


def indexOf(v: A, l: list[A], default: int = -1) -> int:
    for i in range(len(l)):
        if l[i] == v:
            return i
    return default
