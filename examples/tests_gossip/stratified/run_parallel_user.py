from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.simple_user import SimpleUser
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

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
ENDUSER_PORT = 3001
PORT = ENDUSER_PORT + 1 + id

node_name = "node_user" + str(id)
devops = "DevOpsUser" + str(id)

nprovider = 1 if id < 3 else 3
user = SimpleUser()
local_user = f"user{id}"
user.set_name(local_user)

inventory = {}

if inventory_file != None:
    with open(inventory_file, 'r') as file: 
        inventory = json.load(file)
else:
    inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
    inventory[f'enduser'] =  {'address': ADDRESS, 'port_planner': ENDUSER_PORT}
    for uid in range(0, n):
        inventory[f'user{uid}'] = {'address': ADDRESS, 'port_planner': ENDUSER_PORT + 1 + uid}

connections = []
if n != 0:
    if id < 3: 
        # The current user is in the first layer from provider, then we need to connect it to provider
        connect_service_provider = ("provider", "service", f"user{id}", "service")
        connections.append(connect_service_provider)
        connect_config_provider = ("provider", "config", f"user{id}", "config")
        connections.append(connect_config_provider)
    else: 
        # The user is not in the first layer from provider. 
        # 1. Then we must connect to all user from previous layer
        m = ((id - 3) // 3) * 3
        # Layer l-1 , top user
        connect_service_prev_user0 = (f"user{m}", "service", f"user{id}", "service")
        connections.append(connect_service_prev_user0)
        connect_config_prev_user0 = (f"user{m}", "config", f"user{id}", "config")
        connections.append(connect_config_prev_user0)
        # Layer l-1 , mid user
        connect_service_prev_user1 = (f"user{m+1}", "service", f"user{id}", "service")
        connections.append(connect_service_prev_user1)
        connect_config_prev_user1 = (f"user{m+1}", "config", f"user{id}", "config")
        connections.append(connect_config_prev_user1)
        # Layer l-1 , bot user
        connect_service_prev_user2 = (f"user{m+2}", "service", f"user{id}", "service")
        connections.append(connect_service_prev_user2)
        connect_config_prev_user2 = (f"user{m+2}", "config", f"user{id}", "config")
        connections.append(connect_config_prev_user2)
        
    # 2. Then connect to all user from next layer
    k_port = id % 3
    r = range(((id//3)+1)*3 , min(((id//3)+2)*3, n))
    for k in r:
        connect_service_next_user = (f"user{id}", "service", f"user{k}", f"service")
        connections.append(connect_service_next_user)
        connect_config_next_user = (f"user{id}", "config", f"user{k}", f"config")
        connections.append(connect_config_next_user)
        
    if id >= ((n - 1) // 3) * 3:
        # The user is on the last layer
        enduser_port = id % 3
        connect_service_next_enduser = (f"user{id}", "service", f"enduser", f"service")
        connections.append(connect_service_next_enduser)
        connect_config_next_enduser = (f"user{id}", "config", f"enduser", f"config")
        connections.append(connect_config_next_enduser)
    
active = {user: 'running'}

# Goals
if sat:
    goals = {user: [StateReconfigurationGoal("initial", final=True)]}
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
roots=['provider','enduser']
    
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