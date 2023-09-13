from typing import Any, Set, Iterable, Union

from ballet.assembly.assembly import Place, CInstance
from ballet.assembly.plan import Plan, Wait, PushB
from ballet.planner.minizinc.mzn_regular import MiniZincModelComponent, MiniZincStateRegularConstraint, \
    MiniZincPortRegularConstraint, MiniZincBehaviorRegularConstraint, MiniZincWaitRegularConstraint
from ballet.utils.io_utils import makeDir
from ballet.utils.list_utils import flatmap
from ballet.planner.goal import ReconfigurationGoal, Goal, PortConstraint, StateReconfigurationGoal, \
    PortReconfigurationGoal, BehaviorReconfigurationGoal


class ComponentNode:

    def __init__(self, comp: CInstance, active_place: Union[Place, str], word_length=10):
        self._id = comp.id()
        init_place = active_place.name() if type(active_place) == Place else active_place
        self._ports = list(map(lambda p: p.name(), comp.type().ports()))
        self._regular = MiniZincModelComponent(comp, init_place, word_length)
        self._goals: dict[ReconfigurationGoal, bool] = {}
        self._rcv_messages: dict[str, list[Goal]] = {neighbor: [] for neighbor in comp.neighbors()}
        self._rcv_messages["anon"] = []
        self._ballots: dict[str, int] = {neighbor: -1 for neighbor in comp.neighbors()}
        self._round: int = 0
        self._waiting_acks: Set[str] = set()
        self._must_send_acks: Set[str] = set()

    def num_constraints(self):
        # return count(lambda c: c.isPortConstraint(), self._regular.constraints())
        return len(self._regular.constraints())

    def addInstructionContents(self, instructions, source="anon", ballot: tuple[int, str] = None):
        for instruction in instructions:
            self.addInstructionContent(instruction, source, ballot)

    def addInstructionContent(self, instruction, source="anon", round: int = None):
        if instruction.isGoal():
            if instruction.isStateGoal():
                self._addStateGoal(instruction)
            if instruction.isPortGoal():
                self._addPortGoal(instruction)
            if instruction.isBehaviorGoal():
                self._addBehaviorGoal(instruction)
        else:
            # if (source != "anon" and self._ballots[source] < round):
            if (source != "anon"):
                self._rcv_messages[source] = []
                self._ballots[source] = round
                self._rcv_messages[source].append(instruction)

    def _get_constraint_messages(self) -> list[PortConstraint]:
        return flatmap(lambda src: self._rcv_messages[src], self._rcv_messages.keys())

    def _addStateGoal(self, message: StateReconfigurationGoal):
        constraint = MiniZincStateRegularConstraint(message.state(), final=message.final())
        self._regular.add_constraint(constraint)

    def _addPortGoal(self, message: PortReconfigurationGoal):
        constraint = MiniZincPortRegularConstraint(message.port(), str(message.isEnable()), final=message.final())
        self._regular.add_constraint(constraint)

    def _addBehaviorGoal(self, message: BehaviorReconfigurationGoal):
        constraint = MiniZincBehaviorRegularConstraint(message.behavior(), final=message.final())
        self._regular.add_constraint(constraint)

    @staticmethod
    def _howAffected(port: str, mznresult: dict[str, Any]):
        ps_name = port + "_status"
        port_status = mznresult[ps_name]
        result = [(ps_name, port_status[0], '')]
        size = len(port_status)
        status_curr = port_status[0]
        for i in range(1, size):
            status_i = port_status[i]
            if status_i != status_curr:
                result.append((ps_name, status_i, mznresult["sequence"][i - 1]))
                status_curr = status_i
        return result

    def bhv_inference(self) -> list[str]:
        my_regular = self._regular.copy()
        for message in self._get_constraint_messages():
            my_regular.add_constraint(MiniZincPortRegularConstraint(message.port(), message.status()))
        dirname = "local_dec_mzn"
        makeDir(dirname)
        filename = f"{dirname}/{self._id}_decision_{self.get_round()}"
        my_regular.write(filename)
        local_decision_exec = my_regular.run().result()
        sequence = local_decision_exec["sequence"]
        affected_ports = flatmap(lambda p: self._howAffected(p, local_decision_exec), self._ports)
        return sequence, affected_ports

    @staticmethod
    def _format_plan(plan: list[str], compname: str = "") -> Plan:
        def __format_wait(inst: str) -> str:
            cw = inst.split('_')
            # return f"wait({cw[1]}, {cw[2:]})"
            return Wait('_'.join(cw[1:-1]), cw[-1])

        def __format_push(inst: str) -> str:
            return PushB(compname, inst)

        return Plan(compname, list(map(
            lambda inst: __format_wait(inst) if inst[1:5] == "wait" else __format_push(inst),
            plan
        )))

    def local_plan(self) -> Plan:
        my_regular = self._regular.copy()
        for message in self._get_constraint_messages():
            my_regular.add_constraint(MiniZincPortRegularConstraint(message.port(), message.status()))
            if message.wait():
                my_regular.add_constraint(
                    MiniZincWaitRegularConstraint(message.component(), message.behavior(), message.port(),
                                                  message.status()))
        dirname = "plan_mzn"
        makeDir(dirname)
        filename = f"{dirname}/{self._id}_plan"
        my_regular.write(filename)
        local_plan_exec = my_regular.run().result()
        sequence = local_plan_exec["sequence"]
        plan = []
        for inst in sequence:
            if inst != "skip":
                plan.append(inst)
        return self._format_plan(plan, self._id)

    def get_round(self):
        return self._round

    def inc_round(self):
        self._round = self._round + 1

    def add_waiting_acks(self, dests: Iterable[str]):
        res = []
        for dest in dests:
            if self.add_waiting_ack(dest):
                res.append(dest)
        return res

    def add_waiting_ack(self, dest: str):
        self._waiting_acks.add(dest)
        if dest in self._must_send_acks:
            self._must_send_acks.remove(dest)
            return True
        return False

        # self._waiting_acks.add(dest)
        # if dest in self._must_send_acks:
        #     self._must_send_acks.remove(dest)

    def rm_waiting_acks(self, dests: Iterable[str]):
        for dest in dests:
            self.rm_waiting_ack(dest)

    def rm_waiting_ack(self, dest: str):
        if dest in self._waiting_acks:
            print(f"{self._id} removes {dest} of its ack")
            self._waiting_acks.remove(dest)
            print(f"{self._id} waiting acks: {self.waiting_acks()}, must send acks to {self.must_send_acks()}")

    def waiting_acks(self):
        return self._waiting_acks

    def must_send_acks(self):
        return self._must_send_acks

    def add_must_send_acks(self, sources: Iterable[str]):
        for dest in sources:
            self.add_must_send_ack(dest)

    def add_must_send_ack(self, source: str):
        if source not in self._waiting_acks:
            self._must_send_acks.add(source)
        if source in self._waiting_acks:
            self._waiting_acks.remove(source)

    def rm_must_send_acks(self, sources: Iterable[str]):
        for dest in sources:
            self.rm_must_send_ack(dest)

    def rm_must_send_ack(self, source: str):
        if source in self._must_send_acks:
            self._must_send_acks.remove(source)

    def rm_all_must_send_acks(self):
        self._must_send_acks = set()

    def isDone(self):
        return len(self._must_send_acks) == 0 and len(self._waiting_acks) == 0