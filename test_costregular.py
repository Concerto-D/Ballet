# from ballet.assembly.concertod.components.basics import provider
from koda.gossip import gossip
from koda.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, PortConfigConstraint

import warnings

from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import BehaviorReconfigurationGoal, StateReconfigurationGoal

warnings.filterwarnings("ignore", category=SyntaxWarning)

a_provider = Provider()
a_provider.set_name("provider")

# Config local node
connections = []
active = {a_provider: 'running'}
goals = {a_provider: [BehaviorReconfigurationGoal('update'), StateReconfigurationGoal("initial", final=True)]}

PORT = 3000
inventory = {
    'provider':  {'address': 'localhost', 'port_planner': PORT}
}

config_values = {
    "provider": {
        "test1": 0,
        "test2": 1
    }
}

a_port_config_constraint = PortConfigConstraint("provider",
                                                "service","test1",
                                                "test3","==")

node = CostRegularNode(id="node0",
                       admin="DevOps0", components=[a_provider],
                       connections=connections,
                       active=active,
                       goals=goals,
                       port=PORT,
                       inventory=inventory,
                       config_values=config_values,
                       port_config_constraints=[a_port_config_constraint])
roots=['provider']

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
    print("LOCAL PLAN:")
    for instruction in plan.instructions():
        print(instruction)