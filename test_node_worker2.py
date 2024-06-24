from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.openstack.mariadb_master import MariadbMaster
from ballet.assembly.concertod.components.openstack.mariadb_worker import MariadbWorker
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.planner.goal import *
from ballet.utils.dict_utils import *

# -----------------------------------------------------------------------
#  SETUP LOADED FROM .yaml FILES
# -----------------------------------------------------------------------

ADDRESS = 'localhost'
PORT = 3002

# instancess
worker2 = MariadbWorker()
worker2.set_name("worker2")

# inventory
inventory = {}
inventory['master'] = {'address': ADDRESS, 'port_planner': 3000}
inventory['facts'] = {'address': ADDRESS, 'port_planner': 3000}
inventory['worker1'] = {'address': ADDRESS, 'port_planner': 3001}
inventory['worker2'] = {'address': ADDRESS, 'port_planner': PORT}

# node
node = CostRegularNode(id="main_node",
  admin="Dédé", components=[worker2], 
  connections=[('master', 'service', 'worker2', 'master_service')],
  active={
    worker2: 'deployed'
    },
  goals={
    worker2: [StateReconfigurationGoal("initial", final=True)]
    },
  port=PORT,
  inventory=inventory)

# roots
roots=['master']

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final)
for instruction in plan.instructions():
  print(instruction)