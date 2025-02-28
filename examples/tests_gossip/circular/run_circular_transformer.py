from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.circular_transformer import CircularTransformer
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import json
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='ID of user')
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

# Addressing
ADDRESS = 'localhost'
PROVIDER_PORT = 3000
USER_PORT = 3001
PORT = USER_PORT + 1 + id

# Local content
node_name = "node_transformer" + str(id)
devops = "DevOpsTransformer" + str(id)
transformer = CircularTransformer()
transformer.set_name(f"transformer{id}")

# Load or Build inventory
inventory = {}
if inventory_file != None:
    with open(inventory_file, 'r') as file: 
        inventory = json.load(file)
else:
    inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
    inventory[f'user'] =  {'address': ADDRESS, 'port_planner': USER_PORT}
    for uid in range(0, n):
        inventory[f'transformer{uid}'] = {'address': ADDRESS, 'port_planner': USER_PORT + 1 + uid}


# Connections
connections = []
if id == 0:
    # Connect to provider
    connect_inservice_provider = ("provider","serviceOut",f"transformer{id}","serviceIn")
    connections.append(connect_inservice_provider)
    connect_outconfig_provider = (f"transformer{id}","configOut","provider","configIn")
    connections.append(connect_outconfig_provider)
if n != 1:
    # Connect to next transformer if exists
    connect_outservice_next_transformer = (f"transformer{id}","serviceOut",f"transformer{id+1}","serviceIn")
    connections.append(connect_outservice_next_transformer)
    connect_inconfig_next_transformer = (f"transformer{id+1}","configOut",f"transformer{id}","configIn")
    connections.append(connect_inconfig_next_transformer)
else:
    # Connect to end user otherwise
    connect_outservice_user = (f"transformer{id}","serviceOut","user","serviceIn")
    connections.append(connect_outservice_user)
    connect_inconfig_user = (f"user","configOut",f"transformer{id}","configIn")
    connections.append(connect_inconfig_user)

# Node
active = {transformer: 'running'}
if sat:
    goals = {}
else:
    goals = {}


node = CostRegularNode(id=node_name,
admin=devops, components=[transformer], 
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

if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)