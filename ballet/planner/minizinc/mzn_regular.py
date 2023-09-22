from abc import ABC, abstractmethod
from typing import Optional

from ballet.assembly.simplified.assembly import CInstance
from ballet.planner.automata import matrix_from_component
from ballet.planner.minizinc.mzn_app import MiniZincApp
from ballet.utils.list_utils import add_if_no_exist, intersection, difference, map_index
from ballet.utils.mzn_utils import add_mzn_ext, mzn_max_int


class MiniZincRegularConstraint(ABC):

    def isWaitConstraint(self) -> bool:
        return False

    def isBehaviorConstraint(self) -> bool:
        return False

    def isPortConstraint(self) -> bool:
        return False

    def isStateConstraint(self) -> bool:
        return False

    @abstractmethod
    def copy(self):
        pass


class MiniZincWaitRegularConstraint(MiniZincRegularConstraint):

    def __init__(self, comp: str, bhv: str, port: str, status: str) -> None:
        if status in ["e", "enable", "enabled", "true", "True", "T", "t"]:
            mystatus = MiniZincPortRegularConstraint.enabled
        else:
            mystatus = MiniZincPortRegularConstraint.disabled
        self._comp = comp
        self._bhv = bhv
        self._port = port
        self._status = mystatus

    def copy(self):
        return MiniZincWaitRegularConstraint(self._comp, self._bhv, self._port, self._status)

    def component(self) -> str:
        return self._comp

    def behavior(self) -> str:
        return self._bhv

    def isWaitConstraint(self) -> bool:
        return True

    def wait_instruction(self) -> str:
        pre = "e" if self._status == "enabled" else "d"
        return f"{pre}wait_{self._comp}_{self._bhv}"

    def port(self) -> str:
        return self._port

    def status(self) -> str:
        return self._status

    def isDisabled(self) -> bool:
        return self._status == "disabled"

    def isEnabled(self) -> bool:
        return self._status == "enabled"

    def __eq__(self, other):
        if isinstance(other, MiniZincWaitRegularConstraint):
            return self._comp == other.component() and self._bhv == other.behavior() and self._port == other.port() \
                   and self._status == other.status()
        else:
            return False

    def __hash__(self):
        return hash(self._comp) + hash(self._bhv) + hash(self._port) + hash(self._status)


class MiniZincStateRegularConstraint(MiniZincRegularConstraint):

    def __init__(self, state: str, final: bool = False) -> None:
        self._final = final
        self._state = state

    def copy(self):
        return MiniZincStateRegularConstraint(self._state, final=self._final)

    def isStateConstraint(self) -> bool:
        return True

    def state(self) -> str:
        return self._state

    def final(self) -> bool:
        return self._final

    def __eq__(self, other):
        if isinstance(other, MiniZincStateRegularConstraint):
            return self._state == other.state() and self._final == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._state) + hash(self._final)


class MiniZincPortRegularConstraint(MiniZincRegularConstraint):
    enabled = "enabled"
    disabled = "disabled"

    def __init__(self, port: str, status: str, final: bool = False) -> None:
        if status in ["e", "enable", self.enabled, "true", "True", "T", "t"]:
            mystatus = self.enabled
        else:
            mystatus = self.disabled
        self._port = port
        self._status = mystatus
        self._final = final

    def copy(self):
        return MiniZincPortRegularConstraint(self._port, self._status, self._final)

    def isPortConstraint(self) -> bool:
        return True

    def port(self) -> str:
        return self._port

    def status(self) -> str:
        return self._status

    def final(self) -> bool:
        return self._final

    def __eq__(self, other):
        if isinstance(other, MiniZincPortRegularConstraint):
            return self._port == other.port() and self._status == other.status() and self._final == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._port) + hash(self._status) + hash(self._final)


class MiniZincBehaviorRegularConstraint(MiniZincRegularConstraint):

    def __init__(self, behavior: str, final: bool = False) -> None:
        self._behavior = behavior
        self._final = final

    def copy(self):
        return MiniZincBehaviorRegularConstraint(self._behavior, self._final)

    def isBehaviorConstraint(self) -> bool:
        return True

    def behavior(self) -> str:
        return self._behavior

    def final(self) -> bool:
        return self._final

    def __eq__(self, other):
        if isinstance(other, MiniZincBehaviorRegularConstraint):
            return self._behavior == other.behavior() and self._final == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._behavior) + hash(self._final)


class MiniZincModelComponent:
    _skip: str = "skip"
    _includes = ["regular", "count"]

    def __init__(self, comp: CInstance, iplace: str, word_length: Optional[int] = None,
                 constraints: set[MiniZincRegularConstraint] = None) -> None:
        if constraints is None:
            constraints = set()
        self._filename = ""
        self._component = comp
        self._ports = {}
        self._places, self._behaviors, self._matrix_transitions, self._costs = matrix_from_component(comp, self._skip)
        if word_length is None:
            self._word_length = len(self._behaviors) * len(self._places)
        else:
            self._word_length = word_length
        for port in comp.type().ports():
            self._ports[port.name()] = intersection(list(map(lambda place: place.name(), port.bound_places())),
                                                    self._places)
        self._iplace = iplace
        self._wait_constraints = set()
        self._port_constraints = set()
        self._state_constraints = set()
        self._behavior_constraints = set()
        self.add_constraints(constraints)
        self._written = False

    def copy(self):
        self_constraints = self._wait_constraints | self._port_constraints | self._state_constraints | self._behavior_constraints
        constraints = map(lambda c: c.copy(), self_constraints)
        return MiniZincModelComponent(self._component, self._iplace, self._word_length, constraints)

    def constraints(self):
        return self._wait_constraints | self._port_constraints | self._state_constraints | self._behavior_constraints

    def comp_places(self) -> list[str]:
        return self._places

    def states(self) -> str:
        return "enum STATE = {" + ', '.join(self._places) + "};"

    def comp_behaviors(self) -> list[str]:
        return self._behaviors

    def behaviors(self) -> str:
        return "enum BEHAVIOR = {" + ', '.join(self._behaviors) + "};"

    def port_status(self) -> str:
        return "enum STATUS = {" + MiniZincPortRegularConstraint.enabled + ", " + MiniZincPortRegularConstraint.disabled + "};"

    def comp_transitions(self) -> dict[str, dict[str, str]]:
        return self._matrix_transitions

    def transitions(self) -> str:
        lines = ["|" + ",".join([self._matrix_transitions[state][bhv] for bhv in self._behaviors])
                 for state in self._matrix_transitions.keys()]
        return f"array[STATE, BEHAVIOR] of opt STATE: transitions = \n[" + "\n".join(lines) + "|];"

    def includes(self) -> str:
        return '\n'.join(map(lambda lib: f"include \"{add_mzn_ext(lib)}\";", self._includes))

    def word_states_ports(self) -> str:
        # Build Minizinc constraint for tracking ports
        list_ports_status = []
        for port in self._ports.keys():
            port_status_name = port + "_status"
            conditional = ' \/ '.join(map(lambda place: f" states[i] = {place}", self._ports[port]))
            port_status = f"""array[1..{self._word_length}+1] of var STATUS : {port_status_name};
constraint forall (i in 1..{self._word_length}+1) ({port_status_name}[i] = {MiniZincPortRegularConstraint.enabled} <-> {conditional});"""
            list_ports_status.append(port_status)
        # Produce Minizinc content
        sequence = f"array[1..{self._word_length}] of var BEHAVIOR: sequence;"
        active_place = f"array[1..{self._word_length}+1] of var STATE: states;"
        active_place = active_place + "\n" + f"constraint forall (i in 1..{self._word_length}) " \
                                             f"(states[i + 1] = transitions[states[i], sequence[i]]);"
        port_status = '\n'.join(list_ports_status)
        return '\n'.join([sequence, active_place, port_status])

    def constraint_regular(self) -> str:
        init = f"constraint states[1]={self._iplace};"
        valid_places = self._places.copy()
        # valid_places.remove("<>")
        reg = "constraint regular(sequence, transitions, " + \
              self._iplace + ", {" + ','.join(valid_places) + "});"
        suff = f"constraint forall (i in 1..{self._word_length} - 1) (sequence[i] = {self._skip} -> " + \
               f"sequence[i+1] = {self._skip});"
        return '\n'.join([init, reg, suff])

    def trace_cost(self):
        cond = '\n'.join(map_index(lambda key, i: ("if " if i == 0 else "elseif ") +
                                                  f"state = {key[0]} /\\ behavior = {key[1]} then\n{self._costs[key]}",
                                   list(self._costs.keys())))
        return f"""
array[1..{self._word_length}] of var int: cost;
constraint forall (i in 1..{self._word_length}) (cost[i] = fcost(states[i], sequence[i]));
function var int: fcost(var STATE: state, var BEHAVIOR: behavior) =
{cond}
else 
{mzn_max_int}
endif;
"""

    def solve(self) -> str:
        return "solve minimize sum(cost);"

    def add_constraint(self, constraint: MiniZincRegularConstraint):
        if constraint.isWaitConstraint():
            self.add_wait_constraint(constraint)
        if constraint.isBehaviorConstraint():
            self.add_behavior_constraint(constraint)
        if constraint.isStateConstraint():
            self.add_state_constraint(constraint)
        if constraint.isPortConstraint():
            self.add_port_constraint(constraint)

    def add_constraints(self, constraints: list[MiniZincRegularConstraint]):
        for constraint in constraints:
            self.add_constraint(constraint)

    def add_wait_constraint(self, constraint: MiniZincWaitRegularConstraint):
        self._wait_constraints.add(constraint)
        # Find all places that verify port+status
        if constraint.isDisabled():
            pl_comp_port = list(
                map(lambda pl: pl.name(), self._component.type().get_port(constraint.port()).bound_places())
            )
            places = difference(self._places, intersection(self._places, pl_comp_port))
        else:
            pl_comp_port = list(
                map(lambda pl: pl.name(), self._component.type().get_port(constraint.port()).bound_places())
            )
            places = intersection(self._places, pl_comp_port)
        for place in self._places:
            self._costs[(place, constraint.wait_instruction())] = 0
            if place in places:
                self._matrix_transitions[place][constraint.wait_instruction()] = place
            else:
                self._matrix_transitions[place][constraint.wait_instruction()] = "<>"
        # self._behaviors.append(constraint.wait_instruction())
        self._behaviors = add_if_no_exist(self._behaviors, constraint.wait_instruction())

    def add_wait_constraints(self, constraints: list[MiniZincWaitRegularConstraint]):
        for constraint in constraints:
            self.add_wait_constraint(constraint)

    def add_port_constraint(self, constraint: MiniZincPortRegularConstraint):
        self._port_constraints.add(constraint)

    def add_port_constraints(self, constraints: list[MiniZincPortRegularConstraint]):
        for constraint in constraints:
            self.add_port_constraint(constraint)

    def add_state_constraint(self, constraint: MiniZincStateRegularConstraint):
        self._state_constraints.add(constraint)

    def add_state_constraints(self, constraints: list[MiniZincStateRegularConstraint]):
        for constraint in constraints:
            self.add_state_constraint(constraint)

    def add_behavior_constraint(self, constraint: MiniZincBehaviorRegularConstraint):
        self._behavior_constraints.add(constraint)

    def add_behavior_constraints(self, constraints: list[MiniZincBehaviorRegularConstraint]):
        for constraint in constraints:
            self.add_behavior_constraint(constraint)

    def _wait_goal(self, constraint: MiniZincWaitRegularConstraint) -> str:
        return f"constraint count (bhv in sequence) (bhv = {constraint.wait_instruction()}) = 1;"

    def _state_goal(self, constraint: MiniZincStateRegularConstraint) -> str:
        res = ""
        if constraint.final():
            res = f"constraint states[{self._word_length} + 1] = {constraint.state()};\n"
        return res + f"constraint count (v in states) (v = {constraint.state()}) > 0;"

    def _port_goal(self, constraint: MiniZincPortRegularConstraint) -> str:
        if constraint.final():
            return f"constraint {constraint.port()}_status[length({constraint.port()}_status)] = {constraint.status()};"
        else:
            return f"constraint count (status in {constraint.port()}_status) (status = {constraint.status()}) > 0;"

    def _behavior_goal(self, constraint: MiniZincBehaviorRegularConstraint) -> str:
        res = f"constraint count (v in sequence) (v = {constraint.behavior()}) > 0;"
        if constraint.final():
            fin_constraint = f"""constraint (exists (i in 1..{self._word_length}-1) (sequence[i] = {constraint.behavior()} /\ sequence[i+1] = skip)) \/ (sequence[{self._word_length}] = {constraint.behavior()});"""
            res = res + "\n" + fin_constraint
        return res

    def _wait_goals(self) -> str:
        return '\n'.join(map(lambda constraint: self._wait_goal(constraint), self._wait_constraints))

    def _state_goals(self) -> str:
        return '\n'.join(map(lambda constraint: self._state_goal(constraint), self._state_constraints))

    def _port_goals(self) -> str:
        return '\n'.join(map(lambda constraint: self._port_goal(constraint), self._port_constraints))

    def _behavior_goals(self) -> str:
        return '\n'.join(map(lambda constraint: self._behavior_goal(constraint), self._behavior_constraints))

    def goals(self):
        gwait = self._wait_goals()
        gstate = self._state_goals()
        gport = self._port_goals()
        gbhv = self._behavior_goals()
        return '\n'.join([gwait, gstate, gport, gbhv])

    def content(self) -> str:
        content = [self.includes(), self.states(), self.behaviors(), self.port_status(), self.transitions(),
                   self.word_states_ports(), self.constraint_regular(), self.goals(), self.trace_cost(), self.solve()]
        return '\n'.join(content)

    def write(self, filename: str) -> None:
        self._written = True
        mzn_content = self.content()
        filename_mzn = add_mzn_ext(filename)
        self._filename = filename_mzn
        with open(filename_mzn, 'w') as f:
            f.write(mzn_content)
            f.close()

    def run(self, solver: str = "gecode"):
        assert self._written
        return MiniZincApp(self._filename).run(solver)