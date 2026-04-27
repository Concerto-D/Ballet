import concurrent.futures
import json
import subprocess
import time
from abc import abstractmethod
from collections.abc import Collection
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NewType, Sequence

from minizinc import Instance, Model as mznModel, Solver, Status

from ballet.assembly.concertod.component import Component
from ballet.planner.goal import *
from ballet.utils import string_utils
from ballet.utils.list_utils import indexOf, count
from koda.gossip import Model, Solution, Node, ComponentName

State = NewType("State", str)
Transition = NewType("Transition", str)
Automata = NewType("Automata", dict[State, dict[Transition, State]])

Port = NewType("Port", str)
Var = NewType("Var", str)

SKIP = Transition("skip")


class PortStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class BinComparator(str, Enum):
    EQ = "=="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    NE = "!="


class FindMUSException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CRSolution(Solution):
    def __init__(self, result, sat: bool = True):
        self.__result = result
        self.__is_sat = sat

    @property
    def is_sat(self) -> bool:
        return self.__is_sat

    @property
    def result(self):
        return self.__result

    def get(self, key: str):
        return getattr(self.__result, key)


class CRConstraint(ABC):
    @abstractmethod
    def isGoal(self) -> bool:
        raise NotImplementedError

    def isStateConstraint(self):
        return False

    def isValueConstraint(self):
        return False

    def isBinConstraint(self):
        return False

    def isTransitionConstraint(self):
        return False

    def isPortConstraint(self):
        return False

    def isMultiPortConstraint(self):
        return False


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class BinConstraint(CRConstraint):
    left: Var
    right: Var
    comparator: BinComparator
    transition: tuple[State, Transition] | None = None

    def isGoal(self) -> bool:
        return False

    def isBinConstraint(self) -> bool:
        return True


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class ValueConstraint(CRConstraint):
    name: Var
    value: int

    def isGoal(self) -> bool:
        return False

    def isValueConstraint(self):
        return True


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class StateConstraint(CRConstraint):
    state: State
    source: str = "NO SOURCE IS SPECIFIED"
    final: bool = False
    goal: bool = False

    def isGoal(self) -> bool:
        return self.goal

    def isStateConstraint(self):
        return True


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class PortConstraint(CRConstraint):
    port: Port
    status: PortStatus
    source: str = "NO SOURCE IS SPECIFIED"
    final: bool = False
    goal: bool = False

    def isGoal(self) -> bool:
        return self.goal

    def isPortConstraint(self):
        return True


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class MultiPortConstraint(CRConstraint):
    ports: list[Port]
    status: PortStatus
    source: str = "NO SOURCE IS SPECIFIED"
    final: bool = False
    goal: bool = False

    def isGoal(self) -> bool:
        return self.goal

    def isMultiPortConstraint(self):
        return True


@dataclass(frozen=True, unsafe_hash=True, slots=True)
class TransitionConstraint(CRConstraint):
    transition: Transition
    source: str = "NO SOURCE IS SPECIFIED"
    goal: bool = False

    def isGoal(self) -> bool:
        return self.goal

    def isTransitionConstraint(self):
        return True


class CostRegular(Model):
    def __init__(
        self,
        states: list[State],
        transitions: list[Transition],
        automata: Automata,
        costs: dict[State, dict[Transition, int]],
        init_state: State,
        ports: dict[Port, list[State]],
        constraints: set[CRConstraint],
    ):
        self.__assert_conform_automata(states, transitions, automata)
        self.__assert_conform_costs(states, transitions, costs, automata)
        self.__assert_conform_ports(states, ports)
        self.__assert_conform_constraints(states, transitions, ports, constraints)
        if init_state not in states:
            raise AssertionError(
                f"Initial state {init_state} is not a valid state ({list(states)}). Hint for the error component:\n{ports}"
            )
        self.__states = set(states)
        self.__transitions = set(transitions)
        added_skip = False
        if SKIP not in self.__transitions:
            added_skip = True
            self.__transitions.add(SKIP)
        self.__automata = automata
        self.__init_state = init_state
        if added_skip:
            for state in self.__states:
                self.__automata[state][SKIP] = state
        self.__costs = costs
        if added_skip:
            for state in self.__states:
                self.__costs[state][SKIP] = 0
        self.__constraints = constraints
        self.__ports = ports
        n_wait = count(lambda b: b.startswith("wait"), transitions)
        n_bhv = len(transitions) - n_wait
        self.__seq_length = len(self.__states) * n_bhv

    def get_conf_names(self) -> set[Var]:
        res: set[Var] = set()
        for constraint in self.constraints:
            if isinstance(constraint, BinConstraint):
                res.add(constraint.left)
                res.add(constraint.right)
            elif isinstance(constraint, ValueConstraint):
                res.add(constraint.name)
        return res

    @staticmethod
    def __assert_conform_automata(
        states: list[State], transitions: list[str], automata: Automata
    ):
        for source in automata.keys():
            assert source in states  # assert source is declared
            for label in automata[source].keys():
                assert (
                    label in transitions
                )  # assert the label of transition is declared
                assert (
                    automata[source][label] in states
                    or automata[source][label] == "<>"
                    or automata[source][label] == "error"
                )
                # assert target is declared, or the transition does not exist

    @staticmethod
    def __assert_conform_costs(
        states: list[State],
        transitions: list[str],
        costs: dict[State, dict[Transition, int]],
        automata: Automata,
    ):
        for source in costs.keys():
            assert source in states  # assert source is declared
            for label in costs[source].keys():
                assert (
                    label in transitions
                )  # assert the label of transition is declared
                assert automata[source][
                    label
                ]  # assert the transition exists in the automata

    @staticmethod
    def __assert_conform_ports(states: list[State], ports: dict[Port, list[State]]):
        for _, places in ports.items():
            for place in places:
                assert place in states

    @staticmethod
    def __assert_conform_constraints(
        states: list[State],
        transitions: list[Transition],
        ports: dict[Port, list[State]],
        constraints: set[CRConstraint],
    ):
        for constraint in constraints:
            if isinstance(constraint, PortConstraint):
                assert constraint.port in ports.keys()
            elif isinstance(constraint, MultiPortConstraint):
                for port in constraint.ports:
                    assert port in ports.keys()
            elif isinstance(constraint, TransitionConstraint):
                assert constraint.transition in transitions
            elif isinstance(constraint, StateConstraint):
                if constraint.state not in states:
                    print(
                        f"{constraint.state} is not in {states} (component = {ports})",
                        flush=True,
                    )
                assert constraint.state in states

    @staticmethod
    def constraint_from_goal(
        goal: Goal, cause: str, component: Component = None, active: State | None = None
    ):
        if isinstance(goal, BehaviorReconfigurationGoal):
            return TransitionConstraint(
                transition=Transition(goal.behavior()), source=cause, goal=True
            )
        elif isinstance(goal, PlaceReconfigurationGoal):
            return StateConstraint(
                state=State(goal.place()), source=cause, final=goal.final(), goal=True
            )
        elif isinstance(goal, PortReconfigurationGoal):
            return PortConstraint(
                port=Port(goal.port()),
                status=PortStatus.ENABLED if goal.isEnable() else PortStatus.DISABLED,
                source=cause,
                final=goal.final(),
                goal=True,
            )
        elif isinstance(goal, StateReconfigurationGoal):
            if goal.state() == "deployed" or goal.state() == "running":
                to_reach = State(component.running_place)
            elif goal.state() == "destroyed":
                to_reach = State(component.initial_place_place)
            elif (
                goal.state() == "current" or goal.state() == "initial"
            ) and active is not None:
                to_reach = active
            else:
                to_reach = State(goal.state())
            return StateConstraint(
                state=to_reach, source=cause, final=goal.final(), goal=True
            )

        else:
            raise ValueError

    @property
    def states(self) -> set[State]:
        return self.__states

    @property
    def init_state(self) -> State:
        return self.__init_state

    @property
    def transitions(self) -> set[Transition]:
        return self.__transitions

    @property
    def automata(self) -> Automata:
        return self.__automata

    @property
    def costs(self) -> dict[State, dict[Transition, int]]:
        return self.__costs

    @property
    def constraints(self) -> frozenset[CRConstraint]:
        return self.get_constraints()

    def get_constraints(self) -> frozenset[CRConstraint]:
        return frozenset(self.__constraints)

    def add_constraint(self, constraint: CRConstraint):
        self.__constraints.add(constraint)

    def add_transition(
        self, label: Transition, source: State, target: State, cost: int = 0
    ):
        self.__transitions.add(label)
        self.__automata[source][label] = target
        self.__costs[source][label] = cost
        self.__seq_length = self.__seq_length + 1

    @property
    def ports(self):
        return self.__ports

    @property
    def port_names(self):
        return list(self.__ports.keys())

    def __make_mzn_transitions_line(self, state: State, undefined="<>"):
        targets = []
        for transition in self.__transitions:
            if (
                state in self.__automata.keys()
                and transition in self.__automata[state].keys()
            ):  # the transition exists
                targets.append(self.__automata[state][transition])
            else:
                targets.append(undefined)
        return "|" + ",".join(targets)

    def __make_choco_transitions_line(self, state: State):
        targets = []
        for transition in self.__transitions:
            if (
                state in self.__automata.keys()
                and transition in self.__automata[state].keys()
            ):  # the transition exists
                targets.append(self.__automata[state][transition])
            else:
                targets.append("any")
        return "{" + ",".join(targets) + "}"

    def __make_mzn_transitions_matrix(self):
        lines = map(
            lambda state: self.__make_mzn_transitions_line(state), self.__states
        )
        ll = "\n".join(lines)
        return "\n".join(
            f"""
[{ll}|]""".split("\n")[1:]
        )

    def __make_mzn_global_transitions_matrix(self):
        error_line = "|" + ",".join(["error" for _ in range(len(self.transitions))])
        lines = [error_line] + list(
            map(
                lambda state: self.__make_mzn_transitions_line(state, "error").replace(
                    "<>", "error"
                ),
                self.__states,
            )
        )
        ll = "\n".join(lines)
        return "\n".join(
            f"""
[{ll}|]""".split("\n")[1:]
        )

    def __make_choco_transitions_matrix(self):
        lines = map(
            lambda state: self.__make_choco_transitions_line(state), self.__states
        )
        ll = "\n".join(map(lambda l: f"\t\t{l}", lines))
        return ",\n".join(
            f"""
{ll}""".split("\n")[1:]
        )

    def __make_mzn_costs_line(self, state: State):
        targets = []
        for transition in self.__transitions:
            if (
                state in self.__costs.keys()
                and transition in self.__costs[state].keys()
            ):  # the transition has a cost
                targets.append(str(self.__costs[state][transition]))
            else:
                targets.append(str(100000))
        return "|" + ",".join(targets)

    def __make_choco_costs_line(self, state: State):
        targets = []
        for transition in self.__transitions:
            if (
                state in self.__costs.keys()
                and transition in self.__costs[state].keys()
            ):  # the transition has a cost
                targets.append(str(self.__costs[state][transition]))
            else:
                targets.append(str(100000))
        return "{" + ",".join(targets) + "}"

    def __make_mzn_costs_matrix(self):
        lines = map(lambda state: self.__make_mzn_costs_line(state), self.__states)
        ll = "\n".join(lines)
        return "\n".join(
            f"""
[{ll}|]""".split("\n")[1:]
        )

    def __make_mzn_global_costs_matrix(self):
        error_line = "|" + ",".join([str(100000) for i in range(len(self.transitions))])
        lines = [error_line] + list(
            map(lambda state: self.__make_mzn_costs_line(state), self.__states)
        )
        ll = "\n".join(lines)
        return "\n".join(
            f"""
[{ll}|]""".split("\n")[1:]
        )

    def __make_choco_costs_matrix(self):
        lines = map(lambda state: self.__make_choco_costs_line(state), self.__states)
        ll = ",\n".join(map(lambda l: f"\t\t{l}", lines))
        return "\n".join(
            f"""
{ll}""".split("\n")[1:]
        )

    def __make_mzn_port_line(self, port: Port, places: Collection[State]):
        decl = f"array[1..seq_length+1] of var STATUS : {port}_status;"
        disjunction = " \/ ".join(map(lambda place: f"states[i] = {place}", places))
        constr = f"constraint forall (i in 1..seq_length+1) ({port}_status[i] = enabled <-> {disjunction});"
        return [decl, constr]

    def __make_choco_port_line(self, port: Port, places: Collection[State]):
        decl = f'\t\tIntVar[] {port}_status = model.intVarArray("{port}_status", seq_length + 1, 0, 1);'
        forloop = "\t\tfor(int i = 0; i < seq_length + 1; i++) {"
        bool_b0 = (
            f'\t\t\tBoolVar b0 = model.arithm({port}_status[i], "=", enabled).reify();'
        )
        res = [decl, forloop, bool_b0]
        bool_var_names = []
        for place in places:
            bool_var_name = f"b_{port}_{place}"
            bool_var_names.append(bool_var_name)
            res.append(
                f'\t\t\tBoolVar {bool_var_name} = model.arithm(states[i], "=", {place}).reify();'
            )
        bool_clause = f"\t\t\tmodel.addClausesBoolOrArrayEqVar(new BoolVar[]{{{','.join(bool_var_names)}}}, b0);"
        endfor = "\t\t}"
        return res + [bool_clause, endfor]

    def __make_mzn_ports_status_constraints(self) -> str:
        return "\n".join(
            line
            for port in self.__ports.keys()
            for line in self.__make_mzn_port_line(port, self.__ports[port])
        )

    def __make_choco_ports_status_constraints(self) -> str:
        return "\n".join(
            line
            for port in self.__ports.keys()
            for line in self.__make_choco_port_line(port, self.__ports[port])
        )

    def __make_mzn_port_constraint_line(self, constraint: PortConstraint) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        count_name = f"count_{constraint.port}_status_{constraint.status}"
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        if constraint.final:
            res.append(
                f"constraint {constraint.port}_status[seq_length+1] = {constraint.status}; {suffix}"
            )
        res.append(f"var int: {count_name}; {suffix}")
        res.append(
            f"constraint {count_name} = sum(s in {constraint.port}_status) (s = {constraint.status}); {suffix}"
        )
        res.append(f"constraint {count_name} > 0; {suffix}")
        return res

    def __make_mzn_multiport_constraint_line(
        self, constraint: MultiPortConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        count_name = (
            f"count_multi_{''.join(constraint.ports)}_status_{constraint.status}"
        )
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        if constraint.final:
            for port in constraint.ports:
                res.append(
                    f"constraint {port}_status[seq_length+1] = {constraint.status}; {suffix}"
                )
        res.append(f"var int: {count_name}; {suffix}")
        and_condition = " /\ ".join(
            map(
                lambda port: f"{port}_status[i] = {constraint.status}", constraint.ports
            )
        )
        res.append(
            f"constraint {count_name} = sum (i in 1..seq_length+1) ({and_condition});"
        )
        res.append(f"constraint {count_name} > 0; {suffix}")
        return res

    def __make_mzn_transition_constraint_line(
        self, constraint: TransitionConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        count_name = f"count_{constraint.transition}"
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        decl1 = f"var int: {count_name}; {suffix}"
        decl2 = f"constraint {count_name} = sum(b in sequence) (b = {constraint.transition}); {suffix}"
        if constraint.transition.startswith("wait"):
            arity = "= 1"
        else:
            arity = "> 0"
        cstr = f"constraint {count_name} {arity}; {suffix}"
        return [decl1, decl2, cstr]

    def __make_mzn_state_constraint_line(
        self, constraint: StateConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        count_name = f"count_{constraint.state}"
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        res = []
        if constraint.final:
            res.append(
                f"constraint states[seq_length+1] = {constraint.state}; {suffix}"
            )
        res.append(f"var int: {count_name}; {suffix}")
        res.append(
            f"constraint {count_name} = sum(s in states) (s = {constraint.state}); {suffix}"
        )
        res.append(f"constraint {count_name} > 0; {suffix}")
        return res

    # ---------

    def __make_mzn_port_global_constraint_line(
        self, constraint: PortConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        count_name = f"count_{constraint.port}_status_{constraint.status}"
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        if constraint.final:
            res.append(
                f"constraint {constraint.port}_status[seq_length+1] = {constraint.status}; {suffix}"
            )
        res.append(
            f"constraint count({constraint.port}_status, {constraint.status}) > 0; {suffix}"
        )
        return res

    def __make_mzn_multiport_global_constraint_line(
        self, constraint: MultiPortConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        count_name = (
            f"count_multi_{''.join(constraint.ports)}_status_{constraint.status}"
        )
        if constraint.source:
            count_name += f"_{string_utils.clean(constraint.source)}"
        if constraint.final:
            for port in constraint.ports:
                res.append(
                    f"constraint {port}_status[seq_length+1] = {constraint.status}; {suffix}"
                )
        and_condition = " /\ ".join(
            map(
                lambda port: f"{port}_status[i] = {constraint.status}", constraint.ports
            )
        )
        res.append(
            f"constraint count([({and_condition}) | i in 1..seq_length+1], true) > 0; {suffix}"
        )
        return res

    def __make_mzn_transition_global_constraint_line(
        self, constraint: TransitionConstraint
    ) -> list[str]:
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        if constraint.transition.startswith("wait"):
            arity = "= 1"
        else:
            arity = "> 0"
        constr = (
            f"constraint count(sequence, {constraint.transition}) {arity}; {suffix}"
        )
        return [constr]

    def __make_mzn_state_global_constraint_line(self, constraint: StateConstraint):
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        count_name = f"count_{constraint.state}"
        if constraint.source:
            count_name = count_name + "_" + string_utils.clean(constraint.source)
        res = []
        if constraint.final:
            res.append(
                f"constraint states[seq_length+1] = {constraint.state}; {suffix}"
            )
        res.append(f"constraint count (states, {constraint.state}) > 0; {suffix}")
        return res

    # ---------

    def __make_choco_port_constraint_line(
        self, constraint: PortConstraint
    ) -> list[str]:
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        res = []
        if constraint.final:
            res.append(
                f'\t\tmodel.arithm({constraint.port}_status[seq_length], "=", {constraint.status}).post(); {suffix}'
            )
        res.append(
            f'\t\tIntVar count_{constraint.port}_{constraint.status} = model.intVar("count_{constraint.port}_{constraint.status}", 0, seq_length); {suffix}'
        )
        res.append(
            f'\t\tmodel.sum(Arrays.stream({constraint.port}_status).map(s -> s.eq({constraint.status}).boolVar()).toArray(BoolVar[]::new), "=", count_{constraint.port}_{constraint.status}).post(); {suffix}'
        )
        res.append(
            f'\t\tmodel.arithm(count_{constraint.port}_{constraint.status}, ">", 0).post(); {suffix}'
        )
        res.append("\n")
        return res

    def __make_choco_multiport_constraint_line(
        self, constraint: MultiPortConstraint
    ) -> list[str]:
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        res = []
        if constraint.final:
            for port in constraint.ports:
                res.append(
                    f'\t\tmodel.arithm({port}_status[seq_length], "=", {constraint.status}).post(); {suffix}'
                )

        for port in constraint.ports:
            res.append(
                f'\t\tIntVar count_{port}_{constraint.status} = model.intVar("count_{port}_{constraint.status}", 0, seq_length); {suffix}'
            )
            res.append(
                f'\t\tmodel.sum(Arrays.stream({port}_status).map(s -> s.eq({constraint.status}).boolVar()).toArray(BoolVar[]::new), "=", count_{port}_{constraint.status}).post(); {suffix}'
            )
            res.append(
                f'\t\tmodel.arithm(count_{port}_{constraint.status}, ">", 0).post(); {suffix}'
            )

        res.append("\n")
        return res

    def __make_choco_transition_constraint_line(
        self, constraint: TransitionConstraint
    ) -> list[str]:
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        decl = f'\t\tIntVar count_{constraint.transition} = model.intVar("count_{constraint.transition}", 0, seq_length); {suffix}'
        model_sum = f'\t\tmodel.sum(Arrays.stream(sequence).map(s -> s.eq({constraint.transition}).boolVar()).toArray(BoolVar[]::new), "=", count_{constraint.transition}).post(); {suffix}'
        model_arith = (
            f'\t\tmodel.arithm(count_{constraint.transition}, ">", 0).post(); {suffix}'
        )
        return [decl, model_sum, model_arith, "\n"]

    def __make_choco_state_constraint_line(
        self, constraint: StateConstraint
    ) -> list[str]:
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        res = []
        if constraint.final:
            res.append(
                f'\t\tmodel.arithm(states[seq_length], "=", {constraint.state}).post(); {suffix}'
            )
        res.append(
            f'\t\tIntVar count_{constraint.state} = model.intVar("count_{constraint.state}", 0, seq_length); {suffix}'
        )
        res.append(
            f'\t\tmodel.sum(Arrays.stream(states).map(s -> s.eq({constraint.state}).boolVar()).toArray(BoolVar[]::new), "=", count_{constraint.state}).post(); {suffix}'
        )
        res.append(
            f'\t\tmodel.arithm(count_{constraint.state}, ">", 0).post(); {suffix}'
        )
        res.append("\n")
        return res

    def __make_mzn_constraint_line(self, constraint: CRConstraint) -> list[str]:
        if isinstance(constraint, PortConstraint):
            return self.__make_mzn_port_constraint_line(constraint)
        elif isinstance(constraint, StateConstraint):
            return self.__make_mzn_state_constraint_line(constraint)
        elif isinstance(constraint, TransitionConstraint):
            return self.__make_mzn_transition_constraint_line(constraint)
        elif isinstance(constraint, MultiPortConstraint):
            return self.__make_mzn_multiport_constraint_line(constraint)
        else:
            return []

    def __make_mzn_values_constraints_lines(
        self, constraints: Collection[CRConstraint]
    ) -> list[str]:
        mzn_lines = []
        var_names = set()
        # First, collect all var names (we support only int for this POC)
        # Then we declare all of them
        for c in constraints:
            if isinstance(c, ValueConstraint):
                var_names.add(c.name)
            elif isinstance(c, BinConstraint):
                var_names.add(c.left)
                var_names.add(c.right)
        for var in var_names:
            mzn_lines.append(f"var int: {var};")

        for c in constraints:
            if isinstance(c, ValueConstraint):
                mzn_lines.append(f"constraint {c.name} == {c.value};")
            elif isinstance(c, BinConstraint):
                if c.transition is not None:
                    # If a transition is associated, constraint applies when the transition is adopted
                    # We iterate over the sequence length and imply the constraint if states[i] and sequence[i] matches
                    mzn_lines.append(
                        f"constraint forall(i in 1..seq_length) ("
                        f"(states[i] == {c.transition[0]} /\\ sequence[i] == {c.transition[1]}) -> ({c.left} {c.comparator} {c.right})"
                        f");"
                    )
        return mzn_lines

    def __make_mzn_global_constraint_line(self, constraint: CRConstraint) -> list[str]:
        if isinstance(constraint, PortConstraint):
            return self.__make_mzn_port_global_constraint_line(constraint)
        elif isinstance(constraint, StateConstraint):
            return self.__make_mzn_state_global_constraint_line(constraint)
        elif isinstance(constraint, TransitionConstraint):
            return self.__make_mzn_transition_global_constraint_line(constraint)
        elif isinstance(constraint, MultiPortConstraint):
            return self.__make_mzn_multiport_global_constraint_line(constraint)
        else:
            return []

    def __make_choco_constraint_line(self, constraint: CRConstraint) -> list[str]:
        if isinstance(constraint, PortConstraint):
            return self.__make_choco_port_constraint_line(constraint)
        elif isinstance(constraint, StateConstraint):
            return self.__make_choco_state_constraint_line(constraint)
        elif isinstance(constraint, TransitionConstraint):
            return self.__make_choco_transition_constraint_line(constraint)
        elif isinstance(constraint, MultiPortConstraint):
            return self.__make_choco_multiport_constraint_line(constraint)
        else:
            return []

    def __make_mzn_goal_constraints(self):
        set_of_constraints = set(self.__constraints)
        state_and_transition_constraints = filter(
            lambda c: c.isStateConstraint() or c.isTransitionConstraint(),
            set_of_constraints,
        )
        lines = [
            line
            for constraint in state_and_transition_constraints
            for line in self.__make_mzn_constraint_line(constraint)
        ]
        val_and_bin_constraints = {
            constraint
            for constraint in set_of_constraints
            if constraint.isValueConstraint() or constraint.isBinConstraint()
        }
        lines = lines + self.__make_mzn_values_constraints_lines(
            val_and_bin_constraints
        )
        self.make_json_model(print_model=True)
        # TODO remove above line
        return "\n".join(lines)

    def __make_mzn_goal_global_constraints(self):
        set_of_constraints = set(self.__constraints)
        state_and_transition_constraints = filter(
            lambda c: c.isStateConstraint() or c.isTransitionConstraint(),
            set_of_constraints,
        )
        lines = [
            line
            for constraint in state_and_transition_constraints
            for line in self.__make_mzn_global_constraint_line(constraint)
        ]
        val_and_bin_constraints = {
            constraint
            for constraint in set_of_constraints
            if constraint.isValueConstraint() or constraint.isBinConstraint()
        }
        lines = lines + self.__make_mzn_values_constraints_lines(
            val_and_bin_constraints
        )
        self.make_json_model(print_model=True)
        # TODO remove above line
        return "\n".join(lines)

    def __make_choco_goal_constraints(self):
        return "\n".join(
            line
            for constraint in self.__constraints
            for line in self.__make_choco_constraint_line(constraint)
        )

    def make_json_model(
        self,
        *,
        print_model: bool = True,
        write_file: bool = True,
        filepath: Path | str = "model_component.json",
    ):
        # State constraints format
        state_constraints = filter(lambda c: c.isStateConstraint(), self.constraints)
        json_state_constraints = list(
            map(
                lambda constraint: {
                    "state": constraint.state,
                    "isFinal": int(constraint.final),
                    "goal": int(constraint.isGoal()),
                    "source": constraint.source,
                },
                state_constraints,
            )
        )
        # Port constraints format
        port_constraints = filter(lambda c: c.isPortConstraint(), self.constraints)
        json_port_constraints = list(
            map(
                lambda constraint: {
                    "port": constraint.port,
                    "status": constraint.status,
                    "isFinal": int(constraint.final),
                    "goal": int(constraint.isGoal()),
                    "source": constraint.source,
                },
                port_constraints,
            )
        )
        # Multiport constraints format
        multiport_constraints = filter(
            lambda c: c.isMultiPortConstraint(), self.constraints
        )
        json_multiport_constraints = list(
            map(
                lambda constraint: {
                    "ports": constraint.ports,
                    "status": constraint.status,
                    "isFinal": int(constraint.final),
                    "goal": int(constraint.isGoal()),
                    "source": constraint.source,
                },
                multiport_constraints,
            )
        )
        # Transition constraints format
        transition_constraints = filter(
            lambda c: c.isTransitionConstraint(), self.constraints
        )
        json_transition_constraints = list(
            map(
                lambda constraint: {
                    "transition": constraint.transition,
                    "goal": int(constraint.isGoal()),
                    "source": constraint.source,
                },
                transition_constraints,
            )
        )
        # Value constraints format
        value_constraints = filter(lambda c: c.isValueConstraint(), self.constraints)
        json_value_constraints = list(
            map(
                lambda constraint: {"name": constraint.name, "value": constraint.value},
                value_constraints,
            )
        )

        # Bin constraints format
        def __make_json_bin_constraint(constraint):
            res = {
                "left": constraint.left,
                "right": constraint.right,
                "comparator": constraint.comparator,
            }
            if constraint.transition is not None:
                res["transition_source"] = constraint.transition[0]
                res["transition_behavior"] = constraint.transition[1]
            return res

        bin_constraints = filter(lambda c: c.isBinConstraint(), self.constraints)
        json_bin_constraints = [
            __make_json_bin_constraint(constraint) for constraint in bin_constraints
        ]
        content = {
            "states": sorted(self.states),
            "transitions": sorted(self.transitions),
            "automata": self.automata,
            "costs": self.costs,
            "init_state": self.init_state,
            "ports": self.ports,
            "constraints": {
                "state_constraint": json_state_constraints,
                "port_constraint": json_port_constraints,
                "multiport_constraint": json_multiport_constraints,
                "transition_constraint": json_transition_constraints,
                "value_constraint": json_value_constraints,
                "bin_constraint": json_bin_constraints,
            },
        }
        json_content = json.dumps(content)
        if print_model:
            print(json_content)
        if write_file:
            Path(filepath).write_text(json_content)

    def __make_choco_model(self, classname: str = "TestModel"):
        # TODO safe remove
        int_states = "\n".join(
            f"        int {state} = {i} ;" for i, state in sorted(self.states)
        )
        int_behaviors = "\n".join(
            f"        int {transaction} = {i} ;"
            for i, transaction in sorted(self.transitions)
        )
        content = f"""
package gossip;        

import java.util.Arrays;
import java.util.List;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;

public class {classname} {{
    
    public static void main(String[] args) {{

        Model model = new Model();
        int seq_length = {self.__seq_length};
        // STATE
{int_states}
        int any = -1;
        // BEHAVIOR
{int_behaviors}
        // STATUS
        int enabled = 0;
        int disabled = 1;
        
        // TRANSITIONS
        int[][] transitions = {{
{self.__make_choco_transitions_matrix()}
        }};

        // COSTS
        int[][] costs =  {{
{self.__make_choco_costs_matrix()}
        }};  


        // Captured variables
        IntVar[] sequence = model.intVarArray("sequence", seq_length, 0, {len(self.__transitions) - 1});
        IntVar[] states = model.intVarArray("states", seq_length + 1, 0, {len(self.__states) - 1});
        IntVar[] cost = model.intVarArray("cost", seq_length, 0, 1000000);

        for (int i = 0; i < seq_length; i++) {{
            model.element(states[i + 1], transitions, states[i], 0, sequence[i], 0);
        }}
        for (int i = 0; i < seq_length - 1; i++) {{
            BoolVar bi = model.arithm(sequence[i], "=", skip).reify();
            BoolVar bi1 = model.arithm(sequence[i+1], "=", skip).reify();
            bi.imp(bi1).post();;
        }}
        for (int i = 0; i < seq_length; i++) {{
            model.element(cost[i], costs, states[i], 0, sequence[i], 0);
        }}
        
        // Ports' statuses
{self.__make_choco_ports_status_constraints()}
    
        // Init state
        model.arithm(states[0], "=", {self.__init_state}).post();
        
        // Reconfiguration goals as constraints
{self.__make_choco_goal_constraints()}

        // Goal
        IntVar scost = model.intVar("scost", 0, 1000000);
        model.sum(cost, "=", scost).post();

        Solver solver = model.getSolver();
        Solution best = solver.findOptimalSolution(scost, false);
        if(best != null) {{
            solver.printShortStatistics();
        }} else {{
            solver.reset();
            List<Constraint> mus = solver.findMinimumConflictingSet(Arrays.asList(model.getCstrs()));
            System.out.println(mus);
        }}
    }}
}}

"""
        return content

    def __make_mzn_model(self, globalconstraint=True):
        nstate = len(self.states)
        nwait = count(lambda b: b.startswith("wait"), self.transitions)
        nbhv = len(self.transitions) - nwait
        seq_length = nbhv * nstate + nwait
        if globalconstraint:
            goal_constraints = self.__make_mzn_goal_global_constraints()
        else:
            goal_constraints = self.__make_mzn_goal_constraints()
        content = "\n".join(
            f"""
include "count.mzn";
include "regular.mzn";
                            
int: seq_length = {seq_length};

enum STATE = {{{",".join(sorted(self.states))}}};
enum BEHAVIOR = {{{",".join(sorted(self.transitions))}}}; 
enum STATUS = {{enabled, disabled}};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
{self.__make_mzn_transitions_matrix()};

array[STATE, BEHAVIOR] of int: costs = 
{self.__make_mzn_costs_matrix()};

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
{self.__make_mzn_ports_status_constraints()}

% Init state
constraint states[1]={self.__init_state};
constraint regular(sequence, transitions, {self.__init_state}, {{{",".join(self.states)}}});

% Reconfiguration goals as constraints
{goal_constraints}


% Goal
var int: scost;
constraint scost = sum(cost);

% Side structure for exploration strategy
array[1..seq_length] of var int: reversed_cost = array1d(1..seq_length, [cost[seq_length - i + 1] | i in 1..seq_length]);


solve 
:: int_search(reversed_cost, first_fail, indomain_min)
minimize scost;

""".split("\n")[1:]
        )
        return content

    def solve_minizinc(
        self,
        findmus=False,
        write_file=False,
        file_name="model.mzn",
        print_model=False,
        solve_with="chuffed",
    ):
        wf = write_file if not findmus else True
        modelfile = file_name
        model = mznModel()
        mzn_str_model = self.__make_mzn_model()
        if print_model:
            print(mzn_str_model)
        if wf:
            with open(modelfile, "w") as f:
                f.write(mzn_str_model)
                f.close()
            model.add_file(modelfile)
        else:
            model.add_string(mzn_str_model)
        solver = Solver.lookup(solve_with)
        instance = Instance(solver, model)
        result = instance.solve(free_search=True)
        if result.status == Status.UNSATISFIABLE or findmus:
            raise FindMUSException("UNSAT model")
        else:
            r = result.solution
            return CRSolution(r, sat=True)

    def solve_choco(
        self,
        findmus=False,
        write_file=False,
        filename="model_component.json",
        print_model=False,
    ):
        # TODO modify planner-mus.jar to support new type of constraints. Also, catch result better, to get result if sat or not.
        # If sat : we get a solution (behaviors, states, and statuses of ports)
        # If unsat : we get set of MUS
        # TODO remove disjunction, we manage models mus or not.
        if findmus:
            self.make_json_model(print_model=False, write_file=True, filepath=filename)
            try:
                cmd = f"java -jar ballet-planner-mus-1.0-SNAPSHOT-shaded.jar {filename}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return CRSolution(result.stdout, sat=False)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred: {e}", flush=True)
                print("Output:\n", e.stdout)
                print("Error:\n", e.stderr)
        else:
            wf = write_file
            modelfile = "TestModel.java"
            choco_str_model = self.__make_choco_model(classname="TestModel")
            if print_model:
                print(choco_str_model, flush=True)
            if wf:
                with open(modelfile, "w") as f:
                    f.write(choco_str_model)
                    f.close()
            return None, None

    def solve(
        self,
        mode="minizinc",
        findmus=False,
        write_file=False,
        file_name="model.mzn",
        print_model=False,
        solve_with="chuffed",
    ):
        # print(f"Solve with: {mode}, findMus: {findmus}, solver: {solve_with}")
        if mode == "minizinc":
            return self.solve_minizinc(
                findmus, write_file, file_name, print_model, solve_with
            )
        if mode == "choco":
            return self.solve_choco(findmus, write_file, file_name, print_model)


class MultiCostRegular(Model):
    def __init__(self, models: dict[str, CostRegular], node: Node):
        self._models = models
        self._node = node
        self._solutions = {k: None for k in models.keys()}
        self._port_status = {k: None for k in models.keys()}
        self.__first_skip = {k: -1 for k in models.keys()}

    def solve(
        self,
        mode="minizinc",
        print_model=False,
        write_file=False,
        step="flocal",
        iteration=0,
    ):
        def process_model(key, model):
            try:
                real_mode = "minizinc" if mode == "minizinc-test" else mode
                solution = model.solve(
                    real_mode,
                    file_name=f"{key}.mzn",
                    print_model=print_model,
                    write_file=write_file,
                )

                if mode not in ["minizinc-global", "minizinc-test"]:
                    self._solutions[key] = solution
                    self._port_status[key] = {
                        port_name: solution.get(f"{port_name}_status")
                        for port_name in model.ports.keys()
                    }
                    skip_value = solution.get("sequence")[-1]
                    self.__first_skip[key] = indexOf(
                        skip_value, solution.get("sequence")
                    )
            except FindMUSException:
                print(f"{key} 's model is unsat. Qx running", flush=True)
                self._solutions[key] = model.solve(
                    mode="choco",
                    file_name=f"{key}.json",
                    findmus=True,
                    print_model=False,
                    write_file=False,
                )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_model, key, model): key
                for key, model in self._models.items()
            }
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Wait for all threads to complete
        return self._solutions

    def solve_timed(
        self,
        mode="minizinc",
        print_model=False,
        write_file=False,
        step="flocal",
        iteration=0,
    ):
        start_times = {}

        def process_model(key, model):
            try:
                real_mode = "minizinc" if mode == "minizinc-test" else mode
                start_times[key] = time.time()
                solution = model.solve(
                    real_mode,
                    file_name=f"{key}.mzn",
                    print_model=print_model,
                    write_file=write_file,
                )

                if mode not in ["minizinc-global", "minizinc-test"]:
                    self._solutions[key] = solution
                    self._port_status[key] = {
                        port_name: solution.get(f"{port_name}_status")
                        for port_name in model.ports.keys()
                    }
                    skip_value = solution.get("sequence")[-1]
                    self.__first_skip[key] = indexOf(
                        skip_value, solution.get("sequence")
                    )
                    end_time = time.time()
                    rstep = step
                else:
                    rstep = step
            except FindMUSException:
                self._solutions[key] = model.solve(
                    mode="choco",
                    file_name=f"{key}.json",
                    findmus=True,
                    print_model=False,
                    write_file=False,
                )
                rstep = "funsat"

            cmp_time = time.time() - start_times[key]
            print(f"{key}|{rstep}|{iteration}|{cmp_time}", flush=True)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_model, key, model): key
                for key, model in self._models.items()
            }
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Wait for all threads to complete

        return self._solutions

    def get_constraints(self) -> dict[ComponentName, Collection[CRConstraint]]:
        return {
            component: self.get_model(component).constraints
            for component in self.get_components()
        }

    def get_node(self):
        return self._node

    def get_components(self) -> list[ComponentName]:
        return [ComponentName(key) for key in self._solutions.keys()]

    def get_solution(self, key: ComponentName):
        return self._solutions[key]

    def get_port_status(
        self, component: ComponentName, port: Port
    ) -> Sequence[PortStatus]:
        return self._port_status[component][port][: self.__first_skip[component] + 1]

    def get_port_statuses(
        self, component: ComponentName
    ) -> dict[Port, Sequence[PortStatus]]:
        return {
            port: self.get_port_status(component, port)
            for port in self._port_status[component].keys()
        }

    def get_sequence(self, component: ComponentName) -> Sequence[Transition]:
        try:
            return self._solutions[component].get("sequence")[
                : self.__first_skip[component]
            ]
        except:
            return []

    def get_conf_values(self, component: ComponentName):
        try:
            res = {}
            for conf_name in self.get_model(component).get_conf_names():
                res[conf_name] = self._solutions[component].get(conf_name)
            return res
        except:
            return {}

    def get_states(self, component: ComponentName) -> Sequence[State]:
        return self._solutions[component].get("states")[
            : self.__first_skip[component] + 1
        ]

    def add_transition(
        self, component: ComponentName, label: Transition, _from: State, _to: State
    ) -> None:
        self._models[component].add_transition(label, _from, _to)

    def add_constraint(
        self, component: ComponentName, constraint: CRConstraint
    ) -> None:
        print(f"{component}: ADD CONSTRAINT {constraint}", flush=True)
        self._models[component].add_constraint(constraint)

    def get_model(self, key: ComponentName) -> CostRegular:
        return self._models[key]
