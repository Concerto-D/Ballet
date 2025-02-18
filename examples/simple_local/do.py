import sys

from ballet import choerography

assembly_file = "assembly.yaml"
goal_file = "goal.yaml"
inventory_file = "inventory.yaml"

_, _, inventory, _, _, _, _, _, _ = choerography.parse(assembly_file, assembly_file, inventory_file, goal_file)

if len(sys.argv) != 2:
    print(f"Need composent name, one of {", ".join(inventory.keys())}")
    sys.exit(1)

name = sys.argv[1]
if name not in inventory:
    print(f"Need composent name, one of {", ".join(inventory.keys())}")
    sys.exit(1)

print(f"Running {name}")
addr = inventory[name]
choerography.choerography(addr["address"], (addr["port_front"], addr["port_planner"], addr["port_executor"]), assembly_file, "", inventory_file, goal_file)
