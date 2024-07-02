from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.parallel_user import ParallelUser
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
sat = False if args.unsat else True

ADDRESS = 'localhost'
USER_PORT = 3000
PORT = USER_PORT

node_name = "node_user"
devops = "DevOpsUser"
print(f"WELCOME TO {node_name} MANAGED BY {devops}")

# instances
user = ParallelUser(n) 
user.set_name(f"user")

# inventory
inventory = {}
inventory[f'user'] =  {'address': ADDRESS, 'port_planner': USER_PORT}
for i in range(n):
  inventory[f'provider{i}'] = {'address': ADDRESS, 'port_planner': USER_PORT + i + 1}
print("Inventory:")
for (comp, con) in inventory.items():
      print(f"{comp} @ {con['address']}:{con['port_planner']}")

connections = []
for i in range(n):
    connect_config = (f'provider{i}','config',f'user',f'config{i}')
    connections.append(connect_config)
    connect_service = (f'provider{i}','service',f'user',f'service{i}')
    connections.append(connect_service)
    print(connect_config)
    print(connect_service)

## Active
active = {user: 'running'}

## Goal
goals = {user: [StateReconfigurationGoal("initial", final=True)]}
    

node = CostRegularNode(id=node_name,
  admin=devops, components=[user], 
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