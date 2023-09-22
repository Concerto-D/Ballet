from abc import ABC

from ballet.assembly.plan.graph import OrientedUnweightenedGraph
from ballet.assembly.simplified.assembly import CInstance
from ballet.utils import list_utils


class Instruction(ABC):

    def isWait(self):
        return False

    def isPushB(self):
        return False

    def isAdd(self):
        return False

    def isDel(self):
        return False

    def isCon(self):
        return False

    def isDiscon(self):
        return False


class Add(Instruction):

    def __init__(self, component: str, component_type: str):
        self._comp = component
        self._ctype = component_type

    def isAdd(self):
        return True

    def component(self):
        return self._comp

    def type(self):
        return self._ctype

    def triplet(self) -> (str, str, str):
        return 'add', self._comp, self._ctype

    def __str__(self):
        return f"add({self._comp}, {self._ctype})"

    def __eq__(self, other):
        if isinstance(other, Add):
            return other.component() == self.component() and other.type() == self.type()
        return False

    def __hash__(self):
        return hash('add') + hash(self._comp) + hash(self._ctype)


class Delete(Instruction):

    def __init__(self, component: str):
        self._comp = component

    def isDel(self):
        return True

    def component(self):
        return self._comp

    def duet(self) -> (str, str, str):
        return 'del', self._comp

    def __str__(self):
        return f"del({self._comp})"

    def __eq__(self, other):
        if isinstance(other, Delete):
            return other.component() == self.component()
        return False

    def __hash__(self):
        return hash('delete') + hash(self._comp)


class Connect(Instruction):

    def __init__(self, provider: str, providing_port: str, user: str, using_port: str):
        self._provider = provider
        self._providing_port = providing_port
        self._user = user
        self._using_port = using_port

    def isCon(self):
        return True

    def provider(self):
        return self._provider

    def user(self):
        return self._user

    def providing_port(self):
        return self._providing_port

    def using_port(self):
        return self._using_port

    def quintet(self):
        return 'connect', self._provider, self._providing_port, self._user, self._using_port

    def __str__(self):
        return f"connect({self._provider}, {self._providing_port}, {self._user}, {self._using_port})"

    def __eq__(self, other):
        if isinstance(other, Connect):
            return other.provider() == self.provider() and other.providing_port() == self.providing_port() \
                   and other.user() == self.user() and other.using_port() == self.using_port()
        return False

    def __hash__(self):
        return hash('connect') + hash(self._provider) + hash(self._providing_port) \
               + hash(self._using_port) + hash(self._user)


class Disconnect(Instruction):

    def __init__(self, provider: str, providing_port: str, user: str, using_port: str):
        self._provider = provider
        self._providing_port = providing_port
        self._user = user
        self._using_port = using_port

    def isDiscon(self):
        return True

    def provider(self):
        return self._provider

    def user(self):
        return self._user

    def providing_port(self):
        return self._providing_port

    def using_port(self):
        return self._using_port

    def quintet(self):
        return 'disconnect', self._provider, self._providing_port, self._user, self._using_port

    def __str__(self):
        return f"disconnect({self._provider}, {self._providing_port}, {self._user}, {self._using_port})"

    def __eq__(self, other):
        if isinstance(other, Disconnect):
            return other.provider() == self.provider() and other.providing_port() == self.providing_port() \
                   and other.user() == self.user() and other.using_port() == self.using_port()
        return False

    def __hash__(self):
        return hash('disconnect') + hash(self._provider) + hash(self._providing_port) \
               + hash(self._using_port) + hash(self._user)


class Wait(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self) -> str:
        return self._component

    def behavior(self) -> str:
        return self._behavior

    def triplet(self) -> (str, str, str):
        return 'wait', self._component, self._behavior

    def isWait(self):
        return True

    def __str__(self):
        return f"wait({self._component}, {self._behavior})"

    def __eq__(self, other):
        if isinstance(other, Wait):
            return other.behavior() == self.behavior() and other.component() == self.component()
        return False

    def __hash__(self):
        return hash('wait') + hash(self._behavior) + hash(self._component)


class PushB(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self) -> str:
        return self._component

    def behavior(self) -> str:
        return self._behavior

    def triplet(self) -> (str, str, str):
        return 'pushB', self._component, self._behavior

    def isPushB(self):
        return True

    def __str__(self):
        return f"pushB({self._component}, {self._behavior})"

    def __eq__(self, other):
        if isinstance(other, PushB):
            return other.behavior() == self.behavior() and other.component() == self.component()
        return False

    def __hash__(self):
        return hash('pushb') + hash(self._behavior) + hash(self._component)


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

    def __add__(self, other):
        if type(other) == Plan:
            sum_instructions = self.instructions() + other.instructions()
            return Plan(self._name, sum_instructions)
        else:
            return self


def build_graph(plans: list[Plan]):
    vertices: list[Instruction] = list_utils.flatmap(lambda p: p.instructions(), plans)
    waits: list[Wait] = list_utils.findAll(lambda instr: instr.isWait(), vertices)
    graph: OrientedUnweightenedGraph = OrientedUnweightenedGraph(vertices, {})
    for plan in plans:
        instructions: list[Instruction] = plan.instructions()
        for i in range(0, len(instructions)):
            instr1: Instruction = instructions[i]
            if i < len(instructions) - 1:
                instr2: Instruction = instructions[i + 1]
                graph.add_edge(instr1, instr2)
            if instr1.isPushB():
                pushb: PushB = instr1
                potential_wait = list_utils.find(lambda wait: wait.behavior() == pushb.behavior() and
                                                              wait.component() == pushb.component(), waits)
                if potential_wait is not None:
                    graph.add_edge(instr1, potential_wait)
    return graph


def find_order(graph, roots):
    def pop_a_vertex(to_explore, explored, in_edges):
        for v in to_explore:
            if list_utils.forall(lambda u: u in explored, in_edges[v]):
                to_explore.remove(v)
                return v
        return to_explore.pop(0)

    simple_graph = graph.graph()
    to_explore = []
    for root in roots:
        to_explore.append(root)
    order = []
    while to_explore:
        vertex = pop_a_vertex(to_explore, order, graph.in_edges())
        if vertex not in order:
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
