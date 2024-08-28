from gossip.gossip import gossip, timed_gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.parallel_user import ParallelUser
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import json
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')

parser.add_argument('--time', action='store_true', help='Indicate if the time flag is set')
parser.add_argument('-it', type=int, default=0, help='Iteration')


args = parser.parse_args()
ctime = True if args.time else False
it = args.it
n = args.n
sat = False if args.unsat else True
inventory_file = args.inventory

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
ENDUSER_PORT = 3001
PORT = ENDUSER_PORT

node_name = "node_enduser"
devops = "DevOpsEndUser"

m = 1 if n == 0 else ((n - 1) % 3) + 1
enduser = ParallelUser(m)
enduser.set_name(f"enduser")

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
if n == 0:
    service_enduser = ("provider", "service", "enduser", "service0")
    connections.append(service_enduser)
    config_enduser = ("provider", "config", "enduser", "config0")
    connections.append(config_enduser)
else:
    for i in range(n):
        u_id = f"user{i}"
        if i >= ((n - 1) // 3) * 3:
            service_enduser = (u_id, "service", "enduser", "service" + str(i % 3))
            connections.append(service_enduser)
            config_enduser = (u_id, "config", "enduser", "config" + str(i % 3))
            connections.append(config_enduser)
    
active = {enduser: 'running'}

# Goals

goals = {enduser: [BehaviorReconfigurationGoal('suspend'), StateReconfigurationGoal("initial", final=True)]}
    
node = CostRegularNode(id=node_name,
admin=devops, components=[enduser], 
connections=connections,
active=active,
goals=goals,
port=PORT,
inventory=inventory)
    
# roots
roots=['provider','enduser']
    

if ctime:
    plan = timed_gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, iteration=it)
else:
  plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
  if plan != None and len(plan.instructions()):
    print("LOCAL PLAN:")
    for instruction in plan.instructions():
      print(instruction)