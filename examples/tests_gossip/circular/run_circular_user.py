from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.circular_user import CircularUser
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import json
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-it', type=int, default=0, help='Iteration')
parser.add_argument('-port', type=int, default=-1, help='port')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('--time', action='store_true', help='Indicate if the time flag is set')
parser.add_argument('--verbose', action='store_true', help='Indicate if the time debug is set')
args = parser.parse_args()

n = args.n
it = args.it
sat = False if args.unsat else True
ctime = True if args.time else False
verbose = True if args.verbose else False
inventory_file = args.inventory
port = args.port

# Addressing
ADDRESS = 'localhost'


if port == -1:
    PROVIDER_PORT = 3000
    USER_PORT = 3001
    PORT = USER_PORT
else:
    PROVIDER_PORT = port
    USER_PORT = port
    PORT = port



# Local content
node_name = "node_provider"
devops = "DevOpsProvider"
user = CircularUser()
user.set_name("user")

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
if n != 0:
    # connect to last transformer
    connect_inservice_last_transformer = (f"transformer{n-1}", "serviceOut", f"user", f"serviceIn")
    connections.append(connect_inservice_last_transformer)
    connect_outconfig_last_transformer = (f"user", "configOut", f"transformer{n-1}", f"configIn")
    connections.append(connect_outconfig_last_transformer)
else:
    # connect to provider
    connect_inservice_provider = (f"provider", "serviceOut", f"user", f"serviceIn")
    connections.append(connect_inservice_provider)
    connect_outconfig_provider = (f"user", "configOut", f"provider", f"configIn")
    connections.append(connect_outconfig_provider)

# Node
active = {user: 'running'}
if sat:
    goals = {}
else:
    goals = {}

node = CostRegularNode(id=node_name,
admin=devops, components=[user], 
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