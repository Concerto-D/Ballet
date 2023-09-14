import argparse

from ballet.assembly.assembly import CInstance
from ballet.assembly.plan import Plan
from ballet.gateway.dispatcher import Dispatcher
from ballet.gateway.parser import AssemblyParser, InventoryParser, GoalParser
from ballet.messaging.constraint_message import MailboxMessaging, HybridMessaging
from ballet.messaging.grpc.grpc_planner import gRPCMessaging
from ballet.planner.resolve import resolve


def parse(assembly_filename: str, inventory_filename: str, goal_filename: str):
    assembly_parser = AssemblyParser()
    inventory_parser = InventoryParser()
    instances, active = assembly_parser.parse(assembly_filename)
    inventory = inventory_parser.parse(inventory_filename)
    goal_parser = GoalParser(instances, active)
    res_goals, res_goals_state = goal_parser.parse(goal_filename)
    return instances, active, inventory, res_goals, res_goals_state


def dispatch(address, port, instances, active, inventory, goals, state_goals):
    dispatcher = Dispatcher(address, port, instances, active, inventory, goals, state_goals)
    return dispatcher.instances(), dispatcher.active_places(), dispatcher.goals(), dispatcher.place_goals()


def plan(instances, active, goals, goals_place, messaging):
    plans = resolve(instances, active, goals, goals_place, messaging)
    return plans


def execute(plans: dict[CInstance, Plan]):
    # TODO call Concerto-D (i.e., executor)
    for cinstance, plan in plans.items():
        print(f"{plan}\n")


def main(address, port, assembly_filename: str, inventory_filename: str, goal_filename: str):
    instances, active, inventory, goals, goals_state = parse(assembly_filename, inventory_filename, goal_filename)
    instances, active, goals, place_goals = dispatch(address, port, instances, active, inventory, goals, goals_state)
    messaging = HybridMessaging(local_messaging=MailboxMessaging(instances),
                                remote_messaging=gRPCMessaging(instances, inventory, port, verbose=True),
                                local_comps=instances)
    plans = plan(instances, active, goals, place_goals, messaging)

    execute(plans)

if __name__ == "__main__":
    # Setup arguments
    parser = argparse.ArgumentParser(prog='Ballet',
                                     description='',
                                     epilog='')
    parser.add_argument('-hs', '--host', default="localhost")
    parser.add_argument('-p', '--port', type=int, default=5000)
    parser.add_argument('-a', '--assembly', default="assembly.yaml")
    parser.add_argument('-i', '--inventory', default="inventory.yaml")
    parser.add_argument('-g', '--goal', default="goal.yaml")

    args = parser.parse_args()
    host = args.host
    port = args.port
    assembly = args.assembly
    inventory = args.inventory
    goal = args.goal

    main(host, port, assembly, inventory, goal)
