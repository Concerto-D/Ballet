from abc import ABC

from ballet.assembly.plan.graph import OrientedUnweightenedGraph
from ballet.utils import list_utils


class Instruction(ABC):

    def isWait(self):
        return False

    def isPushB(self):
        return False


class Wait(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self) -> str:
        return self._component

    def behavior(self) -> str:
        return self._behavior

    def triplet(self) -> (str, str, str):
        return ('wait', self._component, self._behavior)

    def isWait(self):
        return True

    def __str__(self):
        return f"wait({self._component}, {self._behavior})"

    def __eq__(self, other):
        if isinstance(other, Wait):
            return other.behavior() == self.behavior() and other.component() == self.component()
        return False

    def __hash__(self):
        return hash(self._behavior) + hash(self._component)


class PushB(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self) -> str:
        return self._component

    def behavior(self) -> str:
        return self._behavior

    def triplet(self) -> (str, str, str):
        return ('pushB', self._component, self._behavior)

    def isPushB(self):
        return True

    def __str__(self):
        return f"pushB({self._component}, {self._behavior})"

    def __eq__(self, other):
        if isinstance(other, PushB):
            return other.behavior() == self.behavior() and other.component() == self.component()
        return False

    def __hash__(self):
        return hash(self._behavior) + hash(self._component)


class Plan:

    def __init__(self, name: str, instructions: list[Instruction]):
        self._name = name
        self._instructions = instructions

    def name(self) -> str:
        return self._name

    def instructions(self) -> list[Instruction]:
        return self._instructions

    def __str__(self):
        res = f"==============\n{self._name}\n==============\n"
        return res + '\n'.join(map(lambda instr: str(instr), self._instructions))


def build_graph(plans: list[Plan]):
    vertices: list[Instruction] = list_utils.flatmap(lambda plan: plan.instructions(), plans)
    waits: list[Wait] = list_utils.findAll(lambda instr: instr.isWait(), vertices)
    graph: OrientedUnweightenedGraph = OrientedUnweightenedGraph(vertices, {})
    for plan in plans:
        instructions: list[Instruction] = plan.instructions()
        for i in range(0, len(instructions)):
            instr1: Instruction = instructions[i]
            if instr1.isPushB():
                pushb: PushB = instr1
                potential_wait = list_utils.find(lambda wait: wait.behavior() == pushb.behavior()
                                                              and wait.component() == pushb.component(), waits)
                if potential_wait is not None:
                    graph.add_edge(instr1, potential_wait)
            if i < len(instructions) - 1:
                instr2: Instruction = instructions[i+1]
                if not instr2.isWait():
                    graph.add_edge(instr1, instr2)
    return graph


def find_order(graph, roots):
    simple_graph = graph.graph()
    to_explore = []
    for root in roots:
        to_explore.append(root)
    order = []
    while to_explore != []:
        vertex = to_explore.pop(0)
        if not vertex in order:
            order.append(vertex)
            for neighbor in simple_graph[vertex]:
                to_explore.append(neighbor)
    return order


def find_valid_root(plans: list[Plan]) -> Instruction:
    for plan in plans:
        if type(plan.instructions()[0]) != Wait:
            return plan.instructions()[0]
    raise ValueError("The set of plans is not valid (i.e., there is no plan in the set of plans that do not start by "
                     "a wait instruction)")


def find_roots(plans: list[Plan]) -> list[Instruction]:
    res = []
    for plan in plans:
        fst_instruction = plan.instructions()[0]
        if fst_instruction.isPushB():
            res.append(fst_instruction)
    return res

def merge_plans(plans: list[Plan]) -> Plan:
    roots = find_roots(plans)
    full_graph: OrientedUnweightenedGraph = build_graph(plans)
    return Plan("merged", find_order(full_graph, roots))