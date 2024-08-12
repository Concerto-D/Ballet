from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

# -----------------------------------------------------------------------
#  SETUP CONSIDERED LOADED FROM .yaml FILES IN BALLET
# -----------------------------------------------------------------------

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='ID of user')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()

n = args.n
id = args.i
sat = False if args.unsat else True
inventory_file = args.inventory

node_name = f"node_provider{id-1}"
devops = f"DevOpsProvider{id-1}"

ADDRESS = 'localhost'
USER_PORT = 3000
PORT = USER_PORT + id

# instances
provider = Provider()
provider.set_name(f"provider{id-1}")

# inventory
inventory = {}
if inventory_file != None:
    with open(inventory_file, 'r') as file:
        inventory = json.load(file)
else:
    inventory[f'user'] =  {'address': ADDRESS, 'port_planner': USER_PORT}
    for i in range(n):
      inventory[f'provider{i}'] = {'address': ADDRESS, 'port_planner': USER_PORT + i + 1}

## Connections
connections = []
connect_config = (f'provider{id-1}','config','user',f'config{id}')
connections.append(connect_config)
connect_service = (f'provider{id-1}','service','user',f'service{id}')
connections.append(connect_service)

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
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)