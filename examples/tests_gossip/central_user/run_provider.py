from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json
import sys 

# -----------------------------------------------------------------------
#  SETUP CONSIDERED LOADED FROM .yaml FILES IN BALLET
# -----------------------------------------------------------------------

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='ID of user')
parser.add_argument('-it', type=int, default=0, help='Iteration')
parser.add_argument('-port', type=int, default=-1, help='port')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('--time', action='store_true', help='Indicate if the time flag is set')
parser.add_argument('--verbose', action='store_true', help='Indicate if the time debug is set')

args = parser.parse_args()

n = args.n
id = args.i
it = args.it
port = args.port
sat = False if args.unsat else True
ctime = True if args.time else False
verbose = True if args.verbose else False
inventory_file = args.inventory

node_name = f"node_provider{id-1}"
devops = f"DevOpsProvider{id-1}"

ADDRESS = 'localhost'
if port == -1:
    USER_PORT = 3000
    PORT = USER_PORT + id
else:
    USER_PORT = port
    PORT = port
    
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
connect_config = (f'provider{id-1}','config','user',f'config')
connections.append(connect_config)
connect_service = (f'provider{id-1}','service','user',f'service')
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

if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
    node.global_synchro()
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    node.global_synchro()
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)