from typing import TypeVar

A = TypeVar('A')
B = TypeVar('B')

def sum_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result

def reverse_dict(d: dict[A, list[B]]) -> dict[B, list[A]]:
    res = {}
    for key, value_list in d.items():
        for value in value_list:
            if value not in res:
                res[value] = []
            res[value].append(key)
    return res