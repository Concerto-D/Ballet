from typing import Callable, TypeVar, Set, Optional, List, Iterable

A = TypeVar('A')


def find_in_iterable(f: Callable[[A], bool], s: Iterable[A]) -> Optional[A]:
    for item in s:
        if f(item):
            return item
    return None
