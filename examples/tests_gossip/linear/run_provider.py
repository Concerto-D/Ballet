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
parser.add_argument('-port', type=int, default=-1, help='port')
parser.add_argument('--verbose', action='store_true', help='Indicate if the time debug is set')

args = parser.parse_args()

n = args.n
it = args.it
sat = False if args.unsat else True
ctime = True if args.time else False
verbose = True if args.verbose else False
inventory_file = args.inventory
port = args.port

ADDRESS = 'localhost'

if port == -1:
    PROVIDER_PORT = 3000
    PORT = PROVIDER_PORT
else:    
    PROVIDER_PORT = port
    PORT = port


node_name = "node_provider"
devops = "DevOpsProvider"

# instances
provider = Provider()
provider.set_name(f"provider")

# inventory
inventory = {}
if inventory_file != None:
    with open(inventory_file, 'r') as file:
        inventory = json.load(file)
else:
    inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
    for i in range(n):
        inventory[f'transformer{i}'] = {'address': ADDRESS, 'port_planner': PROVIDER_PORT + i + 1}
          
connections = []

if n > 0:
    connect_config = (f'provider','config',f'transformer{0}',f'configIn')
    connections.append(connect_config)
    connect_service = (f'provider','service',f'transformer{0}',f'serviceIn')
    connections.append(connect_service)
    
active = {provider: 'running'}

# Goals
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
if sat or n == 0:
    roots=['provider']
else:
    roots=['provider', f'transformer{n-1}']

if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)