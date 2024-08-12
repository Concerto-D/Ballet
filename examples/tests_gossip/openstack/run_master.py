from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack
from ballet.assembly.concertod.components.openstack.facts import Facts
from ballet.assembly.concertod.components.openstack.common import Common
from ballet.assembly.concertod.components.openstack.mariadb_master import MariadbMaster 
from ballet.assembly.concertod.components.openstack.haproxy import Haproxy 
from ballet.assembly.concertod.components.openstack.memcached import Memcached 
from ballet.assembly.concertod.components.openstack.ovswitch import Ovswitch 
from ballet.assembly.concertod.components.openstack.rabbitmq import Rabbitmq 


from ballet.planner.goal import *
from ballet.utils.dict_utils import *

import argparse
import json

parser = argparse.ArgumentParser(description="Run gossip node script")
parser.add_argument('-worker', type=int, default=1, help='Number of workers')
parser.add_argument('-inventory', type=str, default=None, help='JSON file with inventory')
parser.add_argument('--unsat', action='store_true', help='Indicate if the unsat flag is set')

args = parser.parse_args()

n = args.worker
sat = False if args.unsat else True
inventory_file = args.inventory

node_name = f"node_master"
devops = f"DevOpsMaster"

ADDRESS = 'localhost'
MASTER_PORT = 3000
PORT = MASTER_PORT

# instances
mariadb_master = MariadbMaster()
mariadb_master.set_name(f"mariadbmaster")
common_master = Common()
common_master.set_name(f"commonmaster")
haproxy_master = Haproxy()
haproxy_master.set_name(f"haproxymaster")
memcached_master = Memcached()
memcached_master.set_name(f"memcachedsmaster")
ovswitch_master = Ovswitch()
ovswitch_master.set_name(f"ovswitchmaster")
rabbitmq_master = Rabbitmq()
rabbitmq_master.set_name(f"rabbitmqmaster")
facts_master = Facts()
facts_master.set_name(f"factsmaster")
components = [mariadb_master, common_master, haproxy_master, memcached_master, 
              ovswitch_master, rabbitmq_master, facts_master]


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
connections.append(('factsmaster','service','commonmaster','factsservice'))
connections.append(('factsmaster','service','haproxymaster','factsservice'))
connections.append(('factsmaster','service','memcachedmaster','factsservice'))
connections.append(('factsmaster','service','ovswitchmaster','factsservice'))
connections.append(('factsmaster','service','rabbitmqmaster','factsservice'))
connections.append(('commonmaster','service','mariadbmaster','commonservice'))
connections.append(('haproxymaster','service','mariadbmaster','haproxyservice'))
for wid in range(n):
    connections.append(('mariadbmaster','service',f'mariadbworker{wid}','masterservice'))
    
    

## Active
active = {
    mariadb_master: 'deployed', 
    common_master: 'deployed', 
    haproxy_master: 'deployed', 
    memcached_master: 'deployed', 
    ovswitch_master: 'deployed',
    rabbitmq_master: 'deployed', 
    facts_master: 'deployed'
}

## Goal
if sat:
    goals = {comp : [StateReconfigurationGoal("initial", final=True)] for comp in components}
    goals[mariadb_master].append(BehaviorReconfigurationGoal('update'))
else:
    # TODO setup a scenario
    goals = {comp : [StateReconfigurationGoal("initial", final=True)] for comp in components}
    goals[mariadb_master].append(BehaviorReconfigurationGoal('update'))
    
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