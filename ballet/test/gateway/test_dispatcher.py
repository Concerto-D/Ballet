from ballet.gateway.dispatcher import Dispatcher
from ballet.gateway.parser import AssemblyParser, InventoryParser, GoalParser

def parse(assembly_filename: str, inventory_filename: str, goal_filename: str):
    assembly_parser = AssemblyParser()
    inventory_parser = InventoryParser()
    instances, active = assembly_parser.parse(assembly_filename)
    inventory = inventory_parser.parse(inventory_filename)
    goal_parser = GoalParser(instances, active)
    res_goals, res_goals_state = goal_parser.parse(goal_filename)
    return instances, active, inventory, res_goals, res_goals_state

def init(address: str, port: int, assembly_filename: str, inventory_filename: str, goal_filename: str):
    instances, active, inventory, goals, state_goals = parse(assembly_filename, inventory_filename, goal_filename)
    dispatcher = Dispatcher(address, port, instances, active, inventory, goals, state_goals)

    for instance in dispatcher.instances():
        print(f"- {instance.id()} (active = {dispatcher.active_places()[instance]})")
        if instance.id() in dispatcher.goals():
            for goal in dispatcher.goals()[instance.id()]:
                print(f"\t-goal: {goal}")
        if instance in dispatcher.place_goals():
            for goal in dispatcher.place_goals()[instance]:
                print(f"\t-goal: {goal}")

    return dispatcher.instances(), dispatcher.active_places(), dispatcher.goals(), dispatcher.place_goals()

if __name__ == "__main__":
    assembly = "assembly.yaml"
    goal = "goal.yaml"
    inventory = "inventory.yaml"
    nodes = [("gros-15.nancy.grid5000.fr", 5000), ("gros-16.nancy.grid5000.fr", 5006), ("gros-42.nancy.grid5000.fr", 5008)]
    for (a, p) in nodes:
        print(f"{a}:{p}")
        init(a, p, assembly, inventory, goal)
        print("------------------")