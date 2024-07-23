from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.transformer import Transformer
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-n', type=int, default=1, help='Number of users')
parser.add_argument('-i', type=int, default=1, help='ID of user')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()

n = args.n
id = args.i
sat = False if args.unsat else True

ADDRESS = 'localhost'
PROVIDER_PORT = 3000 
PORT = PROVIDER_PORT + id

node_name = f"node_transformer{id-1}"
devops = f"DevOpsTransformer{id-1}"
print(f"WELCOME TO {node_name} MANAGED BY {devops} RUN ON {ADDRESS}:{PORT}")

# instances
transformer = Transformer()
transformer.set_name(f"transformer{id-1}")

# inventory
inventory = {}
inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PROVIDER_PORT}
for i in range(n):
  inventory[f'transformer{i}'] = {'address': ADDRESS, 'port_planner': PROVIDER_PORT + i + 1}

print("Inventory:")
for (comp, con) in inventory.items():
      print(f"{comp} @ {con['address']}:{con['port_planner']}")



connections = []
# Connection to the left
if id == 1:
    connect_config = (f'provider','config',f'transformer{0}',f'configIn')
    connections.append(connect_config)
    connect_service = (f'provider','service',f'transformer{0}',f'serviceIn')
    connections.append(connect_service)
    print(connect_config)
    print(connect_service)
else: 
    connect_config = (f'transformer{id-2}','configOut',f'transformer{id-1}',f'configIn')
    connections.append(connect_config)
    connect_service = (f'transformer{id-2}','serviceOut',f'transformer{id-1}',f'serviceIn')
    connections.append(connect_service)
    print(connect_config)
    print(connect_service)
# Connection to the right
if id != n:
    connect_config = (f'transformer{id-1}','configOut',f'transformer{id}',f'configIn')
    connections.append(connect_config)
    connect_service = (f'transformer{id-1}','serviceOut',f'transformer{id}',f'serviceIn')
    connections.append(connect_service)
    print(connect_config)
    print(connect_service)
    
active = {transformer: 'running'}


# Goals
goals = {}
if not sat and id==n:
    goals[transformer] = [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("initial", final=True)]
else: 
    goals[transformer] = []

node = CostRegularNode(id=node_name,
  admin=devops, components=[transformer], 
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
    print(f'UNSAT and N > 0: roots = {roots}')
    
# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)