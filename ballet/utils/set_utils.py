from typing import Callable, TypeVar, Set, Optional, List

A = TypeVar('A')


def find_in_set(f: Callable[[A], bool], s: Set[A]) -> Optional[A]:
    for item in list(s):
        if f(item):
            return item
    return None


def findAll_in_set(f: Callable[[A], bool], s: Set[A]) -> List[A]:
    res = []
    for item in list(s):
        if f(item):
            res.append(item)
    return res


def remove_in_set(f: Callable[[A], bool], s: Set[A]) -> Set[A]:
    elements_to_remove = set(findAll_in_set(f, s))
    s.difference_update(elements_to_remove)
    return s
