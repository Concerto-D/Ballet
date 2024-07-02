from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse

# -----------------------------------------------------------------------
#  SETUP CONSIDERED LOADED FROM .yaml FILES IN BALLET
# -----------------------------------------------------------------------

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='ID of user')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()

n = args.n
id = args.i
sat = False if args.unsat else True

node_name = f"node_provider{id-1}"
devops = f"DevOpsProvider{id-1}"
print(f"WELCOME TO {node_name} MANAGED BY {devops}")


ADDRESS = 'localhost'
USER_PORT = 3000
PORT = USER_PORT + id

# instances
provider = Provider()
provider.set_name(f"provider{id-1}")

# inventory
inventory = {}
inventory[f'user'] =  {'address': ADDRESS, 'port_planner': USER_PORT}
for i in range(n):
  inventory[f'provider{i}'] = {'address': ADDRESS, 'port_planner': USER_PORT + i + 1}
print("Inventory:")
for (comp, con) in inventory.items():
      print(f"{comp} @ {con['address']}:{con['port_planner']}")

print(f"n={n}")
## Connections
connections = []
connect_config = (f'provider{id-1}','config','user',f'config{id}')
connections.append(connect_config)
connect_service = (f'provider{id-1}','service','user',f'service{id}')
connections.append(connect_service)
print(connect_config)
print(connect_service)

## Active
active = {provider: 'running'}

## Goal
if sat:
    goals = {provider: [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("initial", final=True)]}
else:
    goals = {provider: [StateReconfigurationGoal("uninstalled", final=True)]}
    
node = CostRegularNode(id=node_name,
  admin=devops, components=[provider], 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

# roots
roots=[f'provider{i}' for i in range(n)]

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)