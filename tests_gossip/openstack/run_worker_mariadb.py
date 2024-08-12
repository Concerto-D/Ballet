from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.assembly.concertod.components.openstack.common import Common
from ballet.assembly.concertod.components.openstack.mariadb_worker import MariadbWorker
from ballet.assembly.concertod.components.openstack.haproxy import Haproxy 
from ballet.assembly.concertod.components.openstack.memcached import Memcached 
from ballet.assembly.concertod.components.openstack.ovswitch import Ovswitch 
from ballet.assembly.concertod.components.openstack.rabbitmq import Rabbitmq 
from ballet.assembly.concertod.components.openstack.keystone import Keystone
from ballet.assembly.concertod.components.openstack.glance import Glance 


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

node_name = f"node_worker{i}"
devops = f"DevOpsWorker{i}"

ADDRESS = 'localhost'
MASTER_PORT = 3000
PORT =  MASTER_PORT + 10 * (i + 1)
 
# instances
mariadb_worker = MariadbWorker()
mariadb_worker.set_name(f"mariadbworker{i}")
common_worker = Common()
common_worker.set_name(f"commonworker{i}")
haproxy_worker = Haproxy()
haproxy_worker.set_name(f"haproxyworker{i}")
memcached_worker = Memcached()
memcached_worker.set_name(f"memcachedsworker{i}")
ovswitch_worker = Ovswitch()
ovswitch_worker.set_name(f"ovswitchworker{i}")
rabbitmq_worker = Rabbitmq()
rabbitmq_worker.set_name(f"rabbitmqworker{i}")
facts_worker = Facts()
facts_worker.set_name(f"factsworker{i}")
keystone_worker = Keystone()
keystone_worker.set_name(f"keystoneworker{i}")
glance_worker = Glance()
glance_worker.set_name(f"glanceworker{i}")
components = [mariadb_worker, common_worker, haproxy_worker, memcached_worker, 
              ovswitch_worker, rabbitmq_worker, facts_worker, keystone_worker, 
              glance_worker]

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
connections.append(('mariadbmaster','service',f'mariadbworker{i}','masterservice'))  
connections.append((f'factsworker{i}','service',f'commonworker{i}','factsservice'))
connections.append((f'factsworker{i}','service',f'haproxyworker{i}','factsservice'))
connections.append((f'factsworker{i}','service',f'memcachedworker{i}','factsservice'))
connections.append((f'factsworker{i}','service',f'ovswitchworker{i}','factsservice'))
connections.append((f'factsworker{i}','service',f'rabbitmqworker{i}','factsservice'))
connections.append((f'commonworker{i}','service',f'mariadbworker{i}','commonservice'))
connections.append((f'haproxyworker{i}','service',f'mariadbworker{i}','haproxyservice'))
connections.append((f'mariadbworker{i}','service', f'keystoneworker{i}', 'mariadbservice'))  
connections.append((f'mariadbworker{i}','service', f'glanceworker{i}', 'mariadbservice'))  
connections.append((f'mariadbworker{i}','service', f'novaworker{i}', 'mariadbservice'))  
connections.append((f'mariadbworker{i}','service', f'neutronworker{i}', 'mariadbservice'))  
connections.append((f'keystoneworker{i}','service', f'novaworker{i}', 'keystoneservice'))  
connections.append((f'keystoneworker{i}','service', f'neutronworker{i}', 'keystoneservice'))  
connections.append((f'keystoneworker{i}','service', f'glanceworker{i}', 'keystoneservice'))  

## Active
active = {
    mariadb_worker : 'deployed',
    common_worker : 'deployed',
    haproxy_worker : 'deployed',
    memcached_worker : 'deployed',
    ovswitch_worker : 'deployed',
    rabbitmq_worker : 'deployed',
    facts_worker : 'deployed',
    keystone_worker : 'deployed',
    glance_worker : 'deployed'
}

## Goal
if sat:
    goals = {comp : [StateReconfigurationGoal("initial", final=True)] for comp in components}
else:
    # TODO setup a scenario
    goals = {comp : [StateReconfigurationGoal("initial", final=True)] for comp in components}
    
node = CostRegularNode(id=node_name,
  admin=devops, components=components, 
  connections=connections,
  active=active,
  goals=goals,
  port=PORT,
  inventory=inventory)

# roots
roots=['mariadbmaster']

# -----------------------------------------------------------------------
#  PLAN
# -----------------------------------------------------------------------

plan = gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final, debug=True)
if plan != None and len(plan.instructions()):
  print("LOCAL PLAN:")
  for instruction in plan.instructions():
    print(instruction)