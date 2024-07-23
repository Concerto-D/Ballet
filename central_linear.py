from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.basics.transformer import Transformer
from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

# Parse command-line arguments
n = 2
sat = True

ADDRESS = 'localhost'
PORT = 3000 

node_name = f"central"
devops = f"DevOps"
print(f"WELCOME TO {node_name} MANAGED BY {devops} RUN ON {ADDRESS}:{PORT}")

# instances
components = []
active = {}
inventory = {}
goals = {}
connections = []

provider = Provider()
provider.set_name(f"provider")
components.append(provider)
active[provider] = "running"
inventory[f'provider'] =  {'address': ADDRESS, 'port_planner': PORT}

if sat:
    goals[provider] = [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("initial", final=True)]
else:
    goals[provider] = [StateReconfigurationGoal("uninstalled", final=True)]

for i in range(n):
    transformer = Transformer()
    transformer.set_name(f"transformer{i}")
    components.append(transformer)
    active[transformer] = "running"
    inventory[f'transformer{i}'] = {'address': ADDRESS, 'port_planner': PORT}
    if i == n-1:
        goals[transformer] = [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("initial", final=True)]
    else:
        goals[transformer] = []

# Connection to the left
connect_config = (f'provider','config',f'transformer0',f'configIn')
connections.append(connect_config)
connect_service = (f'provider','service',f'transformer0',f'serviceIn')
connections.append(connect_service)
for i in range(n-1):
    connect_config = (f'transformer{i}','configOut',f'transformer{i+1}',f'configIn')
    connections.append(connect_config)
    connect_service = (f'transformer{i}','serviceOut',f'transformer{i+1}',f'serviceIn')
    connections.append(connect_service)
    
print(inventory)
print(connections)
    
node = CostRegularNode(id=node_name,
  admin=devops, components=components, 
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