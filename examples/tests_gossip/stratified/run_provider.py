from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_local_timed, cr_final_timed
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-it', type=int, default=0, help='Iteration')
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

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
ENDUSER_PORT = 3001
PORT = PROVIDER_PORT

node_name = "node_provider"
devops = "DevOpsProvider"

provider = Provider()
provider.set_name(f"provider")

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
    service_enduser = ("provider", "service", "enduser", "service")
    connections.append(service_enduser)
    config_enduser = ("provider", "config", "enduser", "config")
    connections.append(config_enduser)
else:
    bound = n if n < 3 else 3
    for i in range(bound):
        u_id = f"user{i}"
        service_enduser = ("provider", "service", u_id, "service")
        connections.append(service_enduser)
        config_enduser = ("provider", "config", u_id, "config")
        connections.append(config_enduser)
    
active = {provider: 'running'}

# Goals
if sat:
    goals = {provider: [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("running", final=True)]}
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
roots=['provider','enduser']
    
if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)