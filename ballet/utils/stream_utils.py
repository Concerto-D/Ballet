from typing import TypeVar

A = TypeVar('A')


def stream_from_list(l: list[A]):
    for e in l:
        yield e