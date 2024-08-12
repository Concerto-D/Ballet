from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.openstack.neutron import Neutron 


from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-worker', type=int, default=1, help='Number of workers')
parser.add_argument('-i', type=int, default=1, help='Id of worker')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()

n = args.worker
sat = False if args.unsat else True
inventory_file = args.inventory
i = args.i

node_name = f"node_neutron{i}"
devops = f"DevOpsNeutron{i}"

ADDRESS = 'localhost'
MASTER_PORT = 3000
PORT =  MASTER_PORT + 10 * (i + 1) + 2
 
# instances
neutron_worker = Neutron()
neutron_worker.set_name(f"neutron{i}")
components = [neutron_worker]

# inventory
inventory = {}
if inventory_file != None:
    with open(inventory_file, 'r') as file:
        inventory = json.load(file)
else:
    inventory[f'mariadbmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'commonmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'haproxymaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'memcachedmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'ovswitchmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'rabbitmqmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    inventory[f'factsmaster'] =  {'address': ADDRESS, 'port_planner': MASTER_PORT}
    for wid in range(n):
        WORKER_MARIADB_PORT = MASTER_PORT + 10 * (wid + 1) 
        inventory[f'mariadbworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'commonworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'haproxyworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'memcachedworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'ovswitchworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'rabbitmqworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT}
        inventory[f'factsworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT} 
        inventory[f'keystoneworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT} 
        inventory[f'glanceworker{wid}'] =  {'address': ADDRESS, 'port_planner': WORKER_MARIADB_PORT} 
        WORKER_NOVA_PORT = WORKER_MARIADB_PORT + 1
        inventory[f'novaworker{wid}'] = {'address': ADDRESS, 'port_planner': WORKER_NOVA_PORT} 
        WORKER_NEUTRON_PORT = WORKER_MARIADB_PORT + 2 
        inventory[f'neutronworker{wid}'] = {'address': ADDRESS, 'port_planner': WORKER_NEUTRON_PORT} 
        
connections = []
connections.append((f'mariadbworker{i}','service', f'neutron{i}', 'mariadbservice'))  
connections.append((f'keystone{i}','service', f'neutron{i}', 'keystoneservice'))  

## Active
active = {
    neutron_worker : 'deployed'
}

## Goal
if sat:
    goals = {}
else:
    goals = {}
    
node = CostRegularNode(id=node_name,
  admin=devops, components=components, 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

# roots
roots=[]

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)