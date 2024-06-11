from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg
from ballet.assembly.concertod.components.openstack.mariadb_master import MariadbMaster
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.planner.goal import *

# goals = {StateConstraint("deployed", final=True, goal= True, source="Asked by DevOps team 1"),
#          TransitionConstraint("update", goal= True, source="Asked by DevOps team 1")
#         }

# infered = {
#          PortConstraint("service", "enabled", final=True, source="Whatever"),
#          PortConstraint("service", "disabled", final=True, source="Infered by (master, service, disable, final)")
#          }

# constraints = goals | infered

# # Model from component
# cr = CostRegular(["initiated","configured","deployed"], 
#                  ["deploy","update","uninstall"], 
#                  {"initiated" : {"deploy":"deployed"},
#                   "configured": {"deploy":"deployed"},
#                   "deployed": {"update":"configured", "uninstall":"initiated"}}, 
#                  {"initiated" : {"deploy":2},
#                   "configured": {"deploy":1},
#                   "deployed": {"update":1, "uninstall":1}}, 
#                  "initiated",
#                  {"service":["deployed"], "facts_service":["configured", "deployed"]},
#                  constraints)


# try:
#   res = cr.solve(mode="minizinc", print_model=False, write_file=False)
#   print("states = ", res.solution.states)
#   print("sequence = ", res.solution.sequence)
#   print("service = ", res.solution.service_status)
#   print("facts_service = ", res.solution.facts_service_status)
# except FindMUSException as e:
#   print(e)
#   stdout, stderr = cr.solve(mode="choco", findmus=True, print_model=False, write_file=False)
#   print(stdout)
  
mariadb_master = MariadbMaster()
mariadb_master_2 = MariadbMaster()
facts_master = Facts()
mariadb_master.set_name("master")
mariadb_master_2.set_name("master2")
facts_master.set_name("facts")


node = CostRegularNode(id="main_node",
  admin="Dédé", components=[mariadb_master,mariadb_master_2, 
                            facts_master], 
  connections=[('master', 'service', 'worker0', 'master_service'),('master', 'service', 'worker1', 'master_service'),('master', 'service', 'worker2', 'master_service')],
  active={
    mariadb_master: "deployed", 
    mariadb_master_2: "deployed", 
    facts_master:"deployed"
    },
  goals={
    mariadb_master: [StateReconfigurationGoal("initial", final=True), BehaviorReconfigurationGoal("update"), BehaviorReconfigurationGoal("uninstall")], 
    # mariadb_master_2: [StateReconfigurationGoal("initial", final=True), BehaviorReconfigurationGoal("update"), PortReconfigurationGoal("service", False, final=True)], 
    facts_master: [StateReconfigurationGoal("initial", final=True)]
    }
  )

model = cr_init(node)
out_messages, ack_fail = cr_local(model)
targets = cr_msg(node, out_messages)
print(targets)