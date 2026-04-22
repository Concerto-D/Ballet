from ballet.assembly.concertod.components.basics import provider
from koda.gossip import gossip
from koda.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Config local node
connections = []
active = {provider: 'running'}
goals = {}
PORT = 3000
inventory = {
    'provider':  {'address': 'localhost', 'port_planner': PORT}
}

config_values = {
    "test1": 0,
    "test2": 1
}

node = CostRegularNode(id="node0",
  admin="DevOps0", components=[provider], 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)
roots=['provider']

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
    print("LOCAL PLAN:")
    for instruction in plan.instructions():
        print(instruction)