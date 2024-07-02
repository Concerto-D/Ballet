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
id = args.i
sat = False if args.unsat else True

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
PORT = PROVIDER_PORT + id

# instances
user = ParallelUser(1)
user.set_name(f"user{id-1}")

# inventory
inventory = {}
inventory['provider'] = {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
for i in range(n):
    inventory[f'user{i}'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT + i + 1}
print("Inventory:")
for (comp, con) in inventory.items():
      print(f"{comp} @ {con['address']}:{con['port_planner']}")

# node

## Connections
connections = []
connect_config = ('provider','config',f'user{id-1}','config0')
connections.append(connect_config)
connect_service = ('provider','service',f'user{id-1}','service0')
connections.append(connect_service)
print(f'ID: {id-1}')
print(connect_config)
print(connect_service)

## Active
active = {user: 'running'}

## Goal
goals = {user: [StateReconfigurationGoal("initial", final=True)]}
    

node = CostRegularNode(id=f"node_user{id}",
  admin=f"DevOpsUser{id}", components=[user], 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

# roots
roots=['provider']

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)