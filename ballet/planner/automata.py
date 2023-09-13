from typing import Tuple
from ballet.assembly.assembly import ComponentInstance
from ballet.utils.list_utils import findAll, difference, add_if_no_exist


def automata_from_component(comp: ComponentInstance) -> \
        Tuple[dict[str, dict[str, list[str]]], dict[str, list[str]], dict[str, list[str]], dict[tuple[str, str], int]]:
    """
    return automata, bhv_in, bhv_out, cost
    such as
        * automata[src][bhv] -> target
        * bhv_in[pl] -> input behaviors of a place
        * bhv_out[pl] -> output behaviors of a place
        * cost[(pl_in, bhv)] -> int, the cost of applying bhv in pl_in
    """
    automata, bhv_in, bhv_out, cost = {}, {}, {}, {}
    comp_type = comp.type()
    comp_places, comp_bhvs = comp_type.places(), comp_type.behaviors()
    # Init structures with places as keys
    for place in comp_places:
        pl = place.name()
        automata[pl] = {}
        bhv_in[pl], bhv_out[pl] = [], []
    # Iterate on each behavior to fill the transition automata
    for behavior in comp_bhvs:
        bhv = behavior.name()
        for pl in comp_places:
            automata[pl.name()][bhv] = []
        for transition in behavior.transitions():
            src, trg = transition.source().name(), transition.destination()[0].name()
            automata[src][bhv].append(trg)
            if (src, bhv) not in cost.keys():
                cost[(src, bhv)] = 0
            prev = cost[(src, bhv)]
            cost[(src, bhv)] = max(prev, transition.cost())
            bhv_in[trg].append(bhv)
            bhv_out[src].append(bhv)
    return (automata, bhv_in, bhv_out, cost)


def reduce_automata(automata: dict[str, dict[str, list[str]]], label_in: dict[str, list[str]],
                    label_out: dict[str, list[str]], cost: dict[tuple[str, str], int]) -> \
        tuple[list[str], list[str], dict[str, dict[str, str]], dict[tuple[str, str], int]]:
    """
    Reduce an automata using path along arcs defined with the same input

    automata: a graph which can have multiple targets
    bhv_in: behaviors which go in for a given vertex
    bhv_out: behaviors which go out a given vertex
    cost: the cost to apply a behavior to a place
    """
    result_transit = {}
    result_cost = {}
    result_vertices: list[str] = []
    result_input: list[str] = []
    starting_vertices = findAll(
        lambda v: (label_in[v] == []) or (difference(label_out[v], label_in[v]) != []),
        automata.keys()
    )
    # Initialize the roots of the automata
    roots = []
    for vertex in starting_vertices:
        result_vertices.append(vertex)
        result_transit[vertex] = {}
        for label in label_out[vertex]:
            roots.append((vertex, label))
    # while there are vertices to treat
    for (vertex, label) in roots:
        acc = 0
        result_input = add_if_no_exist(result_input, label)
        curr = vertex
        # while a vertex can be reach with this label
        while automata[curr][label]:
            acc = acc + cost[(curr, label)]
            curr = automata[curr][label][0]
            if curr in roots:
                result_transit[vertex][label] = curr
                result_cost[(vertex, label)] = acc
        result_transit[vertex][label] = curr
        result_cost[(vertex, label)] = acc
        result_transit[curr][label] = curr  # Add a self transition
        result_vertices = add_if_no_exist(result_vertices, curr)
    return result_vertices, result_input, result_transit, result_cost


def fill_automata(states: list[str], input: list[str], transitions: dict[str, dict[str, str]],
                  cost: dict[tuple[str, str], int], skip: str) \
        -> tuple[list[str], list[str], dict[str, dict[str, str]], dict[tuple[str, str], int]]:
    result_states = states
    result_input = input + [skip]
    result_cost = {}
    result_transit = {place: {input: "<>" for input in result_input} for place in result_states}
    for state in transitions.keys():
        for input in transitions[state]:
            result_transit[state][input] = transitions[state][input]
            if transitions[state][input] not in ["<>", state]:
                result_cost[(state, input)] = cost[(state, input)]
    for state in result_states:
        result_transit[state][skip] = state
        result_cost[(state, skip)] = 0
    return result_states, result_input, result_transit, result_cost


def matrix_from_component(comp: ComponentInstance, skip: str = "pass") \
        -> tuple[list[str], list[str], dict[str, dict[str, str]], dict[tuple[str, str], int]]:
    (automata, bhv_in, bhv_out, cost) = automata_from_component(comp)
    (result_vertices, result_input, result_transit, result_cost) = reduce_automata(automata, bhv_in, bhv_out, cost)
    return fill_automata(result_vertices, result_input, result_transit, result_cost, skip)