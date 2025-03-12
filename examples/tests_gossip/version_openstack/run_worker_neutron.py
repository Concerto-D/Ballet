from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_final_timed, cr_local_timed
from ballet.assembly.concertod.components.openstack.neutron import Neutron 


from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-worker', type=int, default=1, help='Number of workers')
parser.add_argument('-i', type=int, default=1, help='ID of user')
parser.add_argument('-it', type=int, default=0, help='Iteration')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')
parser.add_argument('-port', type=int, default=-1, help='port')
parser.add_argument('--time', action='store_true', help='Indicate if the time flag is set')
parser.add_argument('--verbose', action='store_true', help='Indicate if the time debug is set')

args = parser.parse_args()

n = args.worker
it = args.it
sat = False if args.unsat else True
ctime = True if args.time else False
verbose = True if args.verbose else False
inventory_file = args.inventory
i = args.i
port = args.port

node_name = f"node_neutron{i}"
devops = f"DevOpsNeutron{i}"

ADDRESS = 'localhost'
MASTER_PORT = 3000
PORT =  MASTER_PORT + 10 * (i + 1) + 2
 

# instances
versions=["1", "2", "3"]
neutron_worker = Neutron(versions=versions)
neutron_worker.set_name(f"neutronworker{i}")
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
for version in versions:
    connections.append((f'mariadbworker{i}', f'servicev{version}', f'neutronworker{i}', f'mariadbservicev{version}'))  
    connections.append((f'keystoneworker{i}', f'servicev{version}', f'neutronworker{i}', f'keystoneservicev{version}'))  

## Active
active = {
    neutron_worker : 'deployedv1'
}

## Goal
if sat:
    goals = {comp : [PortReconfigurationGoal("service", enable=True, final=True)] for comp in components}
else:
    goals = {comp : [PortReconfigurationGoal("service", enable=True, final=True)] for comp in components}
    
node = CostRegularNode(id=node_name,
  admin=devops, components=components, 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

# roots
if sat:
    roots=['commonmaster']
else:
    roots=['commonmaster', 'keystoneworker0']

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

if ctime:
    plan = gossip(node, roots, cr_init, cr_local_timed, cr_msg, cr_enrich, cr_ack, cr_final_timed, timed=True, iteration=it)
    # node.global_synchro()
else:
    plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=verbose)
    # node.global_synchro()
    if plan != None and len(plan.instructions()):
        print("LOCAL PLAN:")
        for instruction in plan.instructions():
            print(instruction)