from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.parallel_user import ParallelUser
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='Id of intermediate user')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')

args = parser.parse_args()
n = args.n
i = args.i
sat = False if args.unsat else True
inventory_file = args.inventory

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
ENDUSER_PORT = 3001
PORT = ENDUSER_PORT + 1 + i

node_name = "node_user" + str(i)
devops = "DevOpsUser" + str(i)

nprovider = 1 if i < 3 else 3
user = ParallelUser(nprovider)
local_user = f"user{i}"
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
    if i < 3: 
        # The current user is in the first layer from provider, then we need to connect it to provider
        connect_service_provider = ("provider", "service", f"user{i}", "service0")
        connections.append(connect_service_provider)
        connect_config_provider = ("provider", "config", f"user{i}", "config0")
        connections.append(connect_config_provider)
    else: 
        # The user is not in the first layer from provider. 
        # 1. Then we must connect to all user from previous layer
        m = ((i - 3) // 3) * 3
        # Layer l-1 , top user
        connect_service_prev_user0 = (f"user{m}", "service", f"user{i}", "service0")
        connections.append(connect_service_prev_user0)
        connect_config_prev_user0 = (f"user{m}", "config", f"user{i}", "config0")
        connections.append(connect_config_prev_user0)
        # Layer l-1 , mid user
        connect_service_prev_user1 = (f"user{m+1}", "service", f"user{i}", "service1")
        connections.append(connect_service_prev_user1)
        connect_config_prev_user1 = (f"user{m+1}", "config", f"user{i}", "config1")
        connections.append(connect_config_prev_user1)
        # Layer l-1 , bot user
        connect_service_prev_user2 = (f"user{m+2}", "service", f"user{i}", "service2")
        connections.append(connect_service_prev_user2)
        connect_config_prev_user2 = (f"user{m+2}", "config", f"user{i}", "config2")
        connections.append(connect_config_prev_user2)
        
    # 2. Then connect to all user from next layer
    k_port = i % 3
    r = range(((i//3)+1)*3 , min(((i//3)+2)*3, n))
    for k in r:
        connect_service_next_user = (f"user{i}", "service", f"user{k}", f"service{k_port}")
        connections.append(connect_service_next_user)
        connect_config_next_user = (f"user{i}", "config", f"user{k}", f"config{k_port}")
        connections.append(connect_config_next_user)
        
    if i >= ((n - 1) // 3) * 3:
        # The user is on the last layer
        enduser_port = i % 3
        connect_service_next_enduser = (f"user{i}", "service", f"enduser", f"service{enduser_port}")
        connections.append(connect_service_next_enduser)
        connect_config_next_enduser = (f"user{i}", "config", f"enduser", f"config{enduser_port}")
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
    
plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)    