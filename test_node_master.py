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
PORT = 3000

# instances
mariadb_master = MariadbMaster()
mariadb_master.set_name("master")
facts_master = Facts()
facts_master.set_name("facts")

# inventory
inventory = {}
inventory['master'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['facts'] = {'address': ADDRESS, 'port_planner': PORT}
inventory['worker1'] = {'address': ADDRESS, 'port_planner': 3001}
inventory['worker2'] = {'address': ADDRESS, 'port_planner': 3002}

# node
node = CostRegularNode(id="main_node",
  admin="Dédé", components=[mariadb_master, facts_master], 
  connections=[('master', 'service', 'worker1', 'master_service'),('master', 'service', 'worker2', 'master_service')],
  active={
    mariadb_master: "deployed", 
    facts_master:"deployed",
    },
  goals={
    mariadb_master: [StateReconfigurationGoal("initial", final=True), BehaviorReconfigurationGoal("update")], 
    facts_master: [StateReconfigurationGoal("initial", final=True)]
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