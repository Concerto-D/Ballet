from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.circular_provider import CircularProvider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import json
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-it', type=int, default=0, help='Iteration')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('-port', type=int, default=-1, help='port')
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
PROVIDER_PORT = 3000
USER_PORT = 3001
PORT = PROVIDER_PORT

if port == -1:
    PROVIDER_PORT = 3000
    USER_PORT = 3001
    PORT = PROVIDER_PORT
else:
    PROVIDER_PORT = port
    USER_PORT = port
    PORT = port

# Local content
node_name = "node_user"
devops = "DevOpsUser"
provider = CircularProvider()
provider.set_name("provider")

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
    # connect to first transformer
    connect_outservice_first_transformer = (f"provider", "serviceOut", f"transformer0", f"serviceIn")
    connections.append(connect_outservice_first_transformer)
    connect_inconfig_first_transformer =  (f"transformer0", "configOut", f"provider", f"configIn")
    connections.append(connect_inconfig_first_transformer)
else:
    # connect to user
    connect_outservice_user = (f"provider", "serviceOut", f"user", f"serviceIn")
    connections.append(connect_outservice_user)
    connect_inconfig_user = (f"user", "configOut", f"provider", f"configIn")
    connections.append(connect_inconfig_user)

# Node
active = {provider: 'running'}
if sat:
    goals = {provider: [StateReconfigurationGoal("running", final=True), BehaviorReconfigurationGoal("suspend")]}
else:
    goals = {}


node = CostRegularNode(id=node_name,
admin=devops, components=[provider], 
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