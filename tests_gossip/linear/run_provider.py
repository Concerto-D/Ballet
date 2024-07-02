from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()
n = args.n
sat = False if args.unsat else True

ADDRESS = 'localhost'
PROVIDER_PORT = 3000
PORT = PROVIDER_PORT

node_name = "node_provider"
devops = "DevOpsProvider"
print(f"WELCOME TO {node_name} MANAGED BY {devops} RUN ON {ADDRESS}:{PORT}")

# instances
provider = Provider()
provider.set_name(f"provider")

# inventory
inventory = {}
inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
for i in range(n):
  inventory[f'transformer{i}'] = {'address': ADDRESS, 'port_planner': PROVIDER_PORT + i + 1}

print("Inventory:")
for (comp, con) in inventory.items():
      print(f"{comp} @ {con['address']}:{con['port_planner']}")
      
connections = []

if n > 0:
    connect_config = (f'provider','config',f'transformer{0}',f'config_in')
    connections.append(connect_config)
    connect_service = (f'provider','service',f'transformer{0}',f'service_in')
    connections.append(connect_service)
    print(connect_config)
    print(connect_service)
    
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
    
plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)