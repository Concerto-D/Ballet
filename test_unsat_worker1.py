from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, ConstraintMessage
from ballet.assembly.concertod.components.openstack.mariadb_master import MariadbMaster
from ballet.assembly.concertod.components.openstack.mariadb_worker import MariadbWorker
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

# -----------------------------------------------------------------------
#  SETUP LOADED FROM .yaml FILES
# -----------------------------------------------------------------------

ADDRESS = 'localhost'
PORT = 3001

# instances
worker1 = MariadbWorker()
worker1.set_name("worker1")

# inventory
inventory = {}
inventory['master'] = {'address': ADDRESS, 'port_planner': 3000}
inventory['facts'] = {'address': ADDRESS, 'port_planner': 3000}
inventory['worker1'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['worker2'] = {'address': ADDRESS, 'port_planner': 3002}

# node
node = CostRegularNode(id="main_node",
  admin="Dédé", components=[worker1], 
  connections=[('master', 'service', 'worker1', 'master_service')],
  active={
    worker1:"deployed"
    },
  goals={
    worker1: [StateReconfigurationGoal("initial", final=True)]
    },
  port=PORT,
  inventory=inventory)


# # # roots

roots=['master']
plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)

print("\n----------------------\n")
if plan != None:
  for instruction in plan.instructions():
    print(instruction) 