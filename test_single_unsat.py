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
PORT = 3000

# instances
mariadb_master = MariadbMaster()
mariadb_master.set_name("master")
facts_master = Facts()
facts_master.set_name("facts")
worker1 = MariadbWorker()
worker1.set_name("worker1")
worker2 = MariadbWorker()
worker2.set_name("worker2")

# inventory
inventory = {}
inventory['master'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['facts'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['worker1'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['worker2'] = {'address': ADDRESS, 'port_planner': PORT}

# node
node = CostRegularNode(id="main_node",
  admin="Dédé", components=[mariadb_master, facts_master, worker1, worker2], 
  connections=[('master', 'service', 'worker1', 'master_service'),('master', 'service', 'worker2', 'master_service')],
  active={
    mariadb_master: "deployed", 
    facts_master:"deployed", 
    worker1:"deployed", 
    worker2:"deployed"
    },
  goals={
    mariadb_master: [StateReconfigurationGoal("initiated", final=True)], 
    facts_master: [StateReconfigurationGoal("initial", final=True)],
    worker1: [StateReconfigurationGoal("initial", final=True)],
    worker2: [StateReconfigurationGoal("initial", final=True)]
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