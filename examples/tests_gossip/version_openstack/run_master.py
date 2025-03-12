from gossip.gossip import gossip
from gossip.cr_gossip import CostRegularNode, cr_init, cr_local, cr_msg, cr_enrich, cr_final, cr_ack, cr_final_timed, cr_local_timed
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
port = args.port


node_name = f"node_master"
devops = f"DevOpsMaster"

ADDRESS = 'localhost'
MASTER_PORT = 3000
PORT = MASTER_PORT




# instances
versions=["1", "2", "3"]
mariadb_master = MariadbMaster(versions=versions)
mariadb_master.set_name(f"mariadbmaster")
common_master = Common(versions=versions)
common_master.set_name(f"commonmaster")
haproxy_master = Haproxy(versions=versions)
haproxy_master.set_name(f"haproxymaster")
memcached_master = Memcached(versions=versions)
memcached_master.set_name(f"memcachedsmaster")
ovswitch_master = Ovswitch(versions=versions)
ovswitch_master.set_name(f"ovswitchmaster")
rabbitmq_master = Rabbitmq(versions=versions)
rabbitmq_master.set_name(f"rabbitmqmaster")
facts_master = Facts(versions=versions)
facts_master.set_name(f"factsmaster")

components = [mariadb_master, haproxy_master, memcached_master, 
              ovswitch_master, rabbitmq_master, facts_master, common_master]

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
    connections.append(('factsmaster',f'servicev{version}','commonmaster',f'factsservicev{version}'))
    connections.append(('factsmaster',f'servicev{version}','haproxymaster',f'factsservicev{version}'))
    connections.append(('factsmaster',f'servicev{version}','memcachedmaster',f'factsservicev{version}'))
    connections.append(('factsmaster',f'servicev{version}','ovswitchmaster',f'factsservicev{version}'))
    connections.append(('factsmaster',f'servicev{version}','rabbitmqmaster',f'factsservicev{version}'))
    connections.append(('commonmaster',f'servicev{version}','mariadbmaster',f'commonservicev{version}'))
    connections.append(('haproxymaster',f'servicev{version}','mariadbmaster',f'haproxyservice'))
    for wid in range(n):
        connections.append(('mariadbmaster',f'servicev{version}',f'mariadbworker{wid}',f'masterservicev{version}'))
    
    

## Active
active = {
    mariadb_master: 'deployedv1', 
    common_master: 'deployedv1', 
    haproxy_master: 'deployedv1', 
    memcached_master: 'deployedv1', 
    ovswitch_master: 'deployedv1',
    rabbitmq_master: 'deployedv1', 
    facts_master: 'deployedv1'
}

## Goal
if sat:
    goals = {comp : [PortReconfigurationGoal("service", True, final=True)] for comp in components}
    goals[common_master].append(StateReconfigurationGoal('deployedv2'))
else:
    goals = {comp : [PortReconfigurationGoal("service", True, final=True)] for comp in components}
    goals[common_master].append(StateReconfigurationGoal('deployedv2'))
    
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