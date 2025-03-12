from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.simple_user import SimpleUser
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
parser.add_argument('-port', type=int, default=-1, help='port')
parser.add_argument('-it', type=int, default=0, help='Iteration')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('--time', action='store_true', help='Indicate if the time flag is set')
parser.add_argument('--verbose', action='store_true', help='Indicate if the time debug is set')

args = parser.parse_args()

n = args.n
id = args.i
it = args.it
sat = False if args.unsat else True
ctime = True if args.time else False
verbose = True if args.verbose else False
inventory_file = args.inventory
port = args.port

ADDRESS = 'localhost'

if port == -1:
    PROVIDER_PORT = 3000
    PORT = PROVIDER_PORT + id
else:
    PROVIDER_PORT = port
    PORT = port


# instances
user = SimpleUser()
user.set_name(f"user{id-1}")

# inventory
inventory = {}
if inventory_file != None:
    with open(inventory_file, 'r') as file:
        inventory = json.load(file)
else:
    inventory['provider'] = {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
    for i in range(n):
        inventory[f'user{i}'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT + i + 1}

# node

## Connections
connections = []
connect_config = ('provider','config',f'user{id-1}','config')
connections.append(connect_config)
print(connect_config)
connect_service = ('provider','service',f'user{id-1}','service')
connections.append(connect_service)
print(connect_service)

## Active
active = {user: 'running'}

## Goal
goals = {user: [StateReconfigurationGoal("initial", final=True)]}
    
print(f"START ON {PORT}")
print(inventory)

node = CostRegularNode(id=f"node_user{id}",
  admin=f"DevOpsUser{id}", components=[user], 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

print("pinged all")

# roots
roots=['provider']

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)