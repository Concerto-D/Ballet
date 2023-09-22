from ballet.assembly.plan.plan import Instruction, Disconnect, Add, Delete, Connect
from ballet.assembly.simplified.assembly import CInstance, Place
from ballet.planner.messaging.constraint_message import PortConstraintMessage, ConstraintMessage, Messaging
from ballet.planner.component_plan_node import ComponentNode
from ballet.planner.goal import ReconfigurationGoal, PortConstraint, Goal
from ballet.utils.list_utils import findAll, difference
from typing import Set, Iterable
import string


def infer_out_messages(comp: CInstance, affected_ports: list[tuple[str, str, str]]) -> Set[
    tuple[str, PortConstraintMessage]]:
    result: Set[tuple[str, ConstraintMessage]] = set()
    # status[port] = [("enabled", b1), ("disabled", b2), ...]
    status = {p: list(
        map(lambda t: (t[1], t[2]), findAll(lambda triplet: triplet[0] == p.name() + "_status", affected_ports)))
              for p in comp.type().ports()}
    for port in status.keys():
        destinations: list[str] = list(map(lambda con: con[0], comp.connections(port))) \
            if comp.isDecentralized() \
            else list(map(lambda con: con[0].id(), comp.connections(port)))
        length = len(status[port])

        # if port.is_use_port():
        #     if length != 1:
        #         for i in range(length - 1):
        #             if status[port][i][0] == "disabled" and status[port][i + 1][0] == "enabled":
        #                 c = PortConstraintMessage(comp.id(), port.name(), "enabled")
        #                 result = result | set(map(lambda dest: (dest, c), destinations))

        if port.is_provide_port():
            if length != 1:
                if status[port][length - 2][0] == "enabled" and status[port][length - 1][0] == "disabled":
                    ##  the port is finally disconnected...
                    c = PortConstraintMessage(comp.id(), port.name(), "disabled")
                    result = result | set(map(lambda dest: (dest, c), destinations))
                for i in range(length - 2):
                    if status[port][i][0] == "enabled" and status[port][i + 1][0] == "disabled" and status[port][i + 2][
                        0] == "enabled":
                        ##  the port is disconnected then reconnected...
                        c = PortConstraintMessage(comp.id(), port.name(), "disabled", status[port][i + 1][1])
                        result = result | set(map(lambda dest: (dest, c), destinations))
                # if status[port][i]="disabled" and status[port][i+1]="enabled":
                #   pass
    return result


def infer_in_constraint(comp: CInstance, source: str, constraint: ConstraintMessage) -> Goal:
    if isinstance(constraint,PortConstraintMessage):
        const: PortConstraintMessage = constraint
        wait = True if const.behavior() is not None else False
        return PortConstraint(source, comp.external_port_connection(constraint.source(), const.port()),
                              const.behavior(), const.status(), wait)


def delta_msg(out_messages, prev_msgs):
    return difference(out_messages, prev_msgs)


def allGlobalAcked(goals: dict[string, Set[ReconfigurationGoal]], acks: Iterable[str]):
    for compId in goals:
        if len(goals[compId]) != 0 and not compId in acks:
            return False
    return True


def resolve(components: Iterable[CInstance], active: dict[CInstance, Place], goals: dict[string, Set[ReconfigurationGoal]],
            goals_states: dict[CInstance, Set[ReconfigurationGoal]], messaging: Messaging):

    # --------------------------------
    #  SETUP
    # --------------------------------
    nodes = {comp: ComponentNode(comp, active[comp]) for comp in components}
    compsIds = {comp.id(): comp for comp in components}
    plans = {comp: None for comp in components}
    prev_sent_msgs = {comp: [] for comp in components}
    for compId in goals.keys():
        if compId in compsIds.keys():
            nodes[compsIds[compId]].addInstructionContents(goals[compId])
    for comp in goals_states.keys():
        nodes[comp].addInstructionContents(goals_states[comp])
    first = True
    # --------------------------------
    #  ITERATIVE PROCESS
    # --------------------------------
    while first or not allGlobalAcked(goals, messaging.get_global_acks()):
        for comp in nodes.keys():
            out_messages = set()
            compId = comp.id()
            node: ComponentNode = nodes[comp]
            # -----------------------
            #  Get input messages
            # -----------------------
            rcv_messages: Set[(str, int, ConstraintMessage)] = messaging.get_messages(comp)
            rcv_acks: Set[str] = messaging.get_acks(comp)
            node.rm_waiting_acks(rcv_acks)
            if len(node.waiting_acks()) != 0 or len(node.must_send_acks()) != 0:
                print(f"{compId} waiting acks: {node.waiting_acks()}, must send acks to {node.must_send_acks()}")

            if len(rcv_messages) != 0 or (first and compId in goals.keys() and len(goals[compId]) != 0):
                node.inc_round()

                # -----------------------
                #  Infer constraints from messages
                # -----------------------
                for (source, msg_round, msg) in rcv_messages:
                    constraint: PortConstraint = infer_in_constraint(comp, source, msg)
                    node.add_must_send_ack(source)
                    node.addInstructionContent(constraint, source=source, round=msg_round)

                # -----------------------
                #  Local inference of behaviors
                # -----------------------
                sequence, affected_ports = node.bhv_inference()

                # -----------------------
                #  Local inference of out messages
                # -----------------------
                out_messages = delta_msg(infer_out_messages(comp, affected_ports), prev_sent_msgs[comp])
                prev_sent_msgs[comp] = prev_sent_msgs[comp] + out_messages
                # -----------------------
                #  Send out messages
                # -----------------------
                if len(out_messages) != 0:
                    messaging.send_messages(comp, node.get_round(), out_messages)
                    to_send = node.add_waiting_acks(set(map(lambda om: om[0], out_messages)))
                    messaging.send_acks(comp, to_send)

            if not first and len(node.must_send_acks()) != 0 and len(node.waiting_acks()) == 0 and len(out_messages) == 0:
                messaging.send_acks(comp, node.must_send_acks())
                node.rm_all_must_send_acks()
            if (compId in goals.keys() and len(goals[compId]) != 0) and len(node.waiting_acks()) == 0 and len(node.must_send_acks()) == 0 :
                messaging.bcast_root_acks(comp)

        first = False

    for comp in nodes:
        plans[comp] = nodes[comp].local_plan()

    return plans


def diff_assembly(comp_in: dict[str, str], conn_in: list[(str, str, str, str)],
                  comp_out: dict[str, str], conn_out: list[(str, str, str, str)]) -> \
        (list[Instruction], list[Instruction], list[Instruction], list[Instruction]):
    to_add: list[Add] = []
    to_del: list[Delete] = []
    to_con: list[Connect] = []
    to_disc: list[Disconnect] = []
    for comp_name, comp_type in comp_in.items():
        if comp_name not in comp_out.keys():
            to_del.append(Delete(comp_name))
    for comp_name, comp_type in comp_out.items():
        if comp_name not in comp_in.keys():
            to_add.append(Add(comp_name, comp_type))
    for c1, p1, c2, p2 in conn_in:
        if (c1, p1, c2, p2) not in conn_out:
            to_disc.append(Disconnect(c1, p1, c2, p2))
    for c1, p1, c2, p2 in conn_out:
        if (c1, p1, c2, p2) not in conn_in:
            to_con.append(Connect(c1, p1, c2, p2))
    return to_add, to_del, to_con, to_disc
