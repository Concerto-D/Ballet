import argparse

from ballet.assembly.concertod.assembly import Assembly
from ballet.assembly.plan.plan import merge_plans, Plan, Add, Delete, Disconnect, Wait, PushB, Connect
from ballet.gateway.dispatcher import Dispatcher
from ballet.gateway.parser import AssemblyParser, InventoryParser, GoalParser
from ballet.planner.communication.constraint_message import MailboxMessaging, HybridMessaging
from ballet.planner.communication.grpc.grpc_planner import gRPCMessagingPlanner
from ballet.planner.resolve import resolve, diff_assembly


def parse(assembly_in_filename: str, assembly_out_filename: str, inventory_filename: str, goal_filename: str):
    assembly_parser = AssemblyParser()
    inventory_parser = InventoryParser()
    instances, active, components_in, connections_in = assembly_parser.parse(assembly_in_filename)
    additional_instances, _, components_out, connections_out = assembly_parser.parse(assembly_out_filename)
    for inst in additional_instances:
        active[inst] = inst.type().initial_place()
        instances.add(inst)
    comp_inventory = inventory_parser.parse(inventory_filename)
    goal_parser = GoalParser(instances, active)
    res_goals, res_goals_state = goal_parser.parse(goal_filename)
    return instances, active, comp_inventory, res_goals, res_goals_state, components_in, connections_in, components_out, connections_out


def dispatch(address, port, instances, active, inventory, goals, state_goals):
    dispatcher = Dispatcher(address, port, instances, active, inventory, goals, state_goals)
    return dispatcher.instances(), dispatcher.active_places(), dispatcher.goals(), dispatcher.place_goals()


def plan(instances, active, inventory, port, goals, goals_place, comp_in, conn_in, comp_out, conn_out):
    messaging = HybridMessaging(local_messaging=MailboxMessaging(instances),
                                remote_messaging=gRPCMessagingPlanner(instances, inventory, port, verbose=True),
                                local_comps=instances)
    plans = resolve(instances, active, goals, goals_place, messaging)
    unified_plan: Plan = merge_plans(list(plans.values()))
    to_add, to_del, to_con, to_disc = diff_assembly(comp_in, conn_in, comp_out, conn_out)
    return Plan("Final plan", to_add + to_con + unified_plan.instructions() + to_disc + to_del)


def execute(assembly: Assembly, plan: Plan, running=False):
    # TODO: remove print and concretely execute the plan
    if not running:
        print(f"{plan}\n")
    else:
        for instruction in plan.instructions():
            if instruction.isAdd():
                add: Add = instruction
                assembly.add_component(add.component(), add.type())
            elif instruction.isCon():
                connect: Connect = instruction
                assembly.connect(connect.provider(), connect.providing_port(), connect.user(), connect.using_port())
            elif instruction.isPushB():
                pushb: PushB = instruction
                assembly.push_b(pushb.component(), pushb.behavior())
            elif instruction.isWait():
                wait: Wait = instruction
                assembly.wait(wait.component())
            elif instruction.isDiscon():
                disconnect: Disconnect = instruction
                assembly.disconnect(disconnect.provider(), disconnect.providing_port(), disconnect.user(), disconnect.using_port())
            elif instruction.isDel():
                delete: Delete = instruction
                assembly.del_component(delete.component())
    # TODO: What is assembly.synchronize()? It appears in some example but never defined


def choerography(address, ports, assembly_in_filename: str, assembly_out_filename: str, inventory_filename: str, goal_filename: str):
    (port_front, port_planner, port_executor) = ports
    instances, active, inventory, goals, goals_state, components_in, connections_in, components_out, connections_out \
        = parse(assembly_in_filename, assembly_out_filename, inventory_filename, goal_filename)
    instances, active, goals, place_goals = dispatch(address, port_front, instances, active, inventory, goals, goals_state)
    my_plan = plan(instances, active, inventory, port_planner, goals, place_goals, components_in, connections_in, components_out, connections_out)
    assembly = None # TODO get concrete assembly
    execute(assembly, my_plan)