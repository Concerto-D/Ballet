from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final
from ballet.assembly.concertod.components.openstack.mariadb_master import MariadbMaster
from ballet.assembly.concertod.components.openstack.mariadb_worker import MariadbWorker
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.planner.goal import *
from gossip.cost_regular import PortConstraint, CostRegular

from ballet.utils.dict_utils import *

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
mariadb_master.set_name("master")
facts_master = Facts()
facts_master.set_name("facts")
worker1 = MariadbWorker()
worker1.set_name("worker1")
worker2 = MariadbWorker()
worker2.set_name("worker2")


node = CostRegularNode(id="main_node",
  admin="Dédé", components=[mariadb_master, facts_master, worker1, worker2], 
  connections=[('master', 'service', 'worker0', 'master_service'),('master', 'service', 'worker1', 'master_service'),('master', 'service', 'worker2', 'master_service')],
  active={
    mariadb_master: "deployed", 
    facts_master:"deployed",
    worker1: 'deployed',
    worker2: 'deployed'
    },
  goals={
    mariadb_master: [StateReconfigurationGoal("initial", final=True), BehaviorReconfigurationGoal("update")], 
    worker1: [StateReconfigurationGoal("initial", final=True)], 
    worker2: [StateReconfigurationGoal("initial", final=True)], 
    facts_master: [StateReconfigurationGoal("initial", final=True)]
    },
  roots=['master', 'facts', 'worker1', 'worker2']
  )

model = cr_init(node)
out_messages, ack_fail = cr_local(model)
targets = cr_msg(node, out_messages) # -> dict[str, list[Message]]
set_of_messages = set()
for (dest, messages) in targets.items():
  if dest in model.get_components():
    for message in messages:
      set_of_messages.add(message)
for message in set_of_messages:
  print(f"{message}")
enriched_model = cr_enrich(model, set_of_messages)

plan = cr_final(enriched_model)

print(plan)
