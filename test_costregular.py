import warnings

from ballet.assembly.concertod.components.basics.provider import Provider
from ballet.planner.goal import StateReconfigurationGoal
from koda.cost_regular import BinComparator, Var
from koda.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, \
    PortConfigConstraint
from koda.gossip import gossip

warnings.filterwarnings("ignore", category=SyntaxWarning)

PORT = 3000

var1 = Var('test1')
var2 = Var('test2')
var3 = Var('test3')

# Config local node
provider = Provider()
provider.set_name("provider")

connections = []
active = {provider: 'uninstalled'}
goals = {
    provider: [StateReconfigurationGoal('running')]
}
inventory = {
    'provider': {
        'address': 'localhost',
        'port_planner': PORT,
        'variables': [var1, var2]
    },
    'service': {
        'address': 'localhost',
        'port_planner': PORT,
        'variables': [var3]
    }
}

config_values = {
    provider: {
        var1: 0,
        var2: 1,
    }
}
port_config_constraints = [
    PortConfigConstraint('provider', 'service', var1, var3, BinComparator.EQ)
]

node = CostRegularNode(
    "node0",
    admin="DevOps0",
    components=[provider],
    connections=connections,
    active=active,
    goals=goals,
    port=PORT,
    inventory=inventory,
    config_values=config_values,
    port_config_constraints=port_config_constraints,
)
roots = ['provider']

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)

if plan is not None and len(plan.instructions()):
    print("LOCAL PLAN:")
    for instruction in plan.instructions():
        print(instruction)
