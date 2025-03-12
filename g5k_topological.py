from enoslib import *
from enoslib.infra.enos_g5k.g5k_api_utils import get_api_username
from random import randrange
import shutil
import os
import time
import argparse
import json


username = get_api_username()
project_dir = f"/home/{username}/Project/Ballet/"
minizinc = f"/home/{username}/Software/MiniZincIDE-2.7.6-bundle-linux-x86_64/bin"

def minizinc_path():
    return f"export PATH={minizinc}:$PATH"  

_COMPONENT=2
_DEFAULT_TIME = "00:02:00"
_DEFAULT_START = "now"

_SCENARIOS = ["cuser","cprovider","linear","circular","stratified"]

_PORT = 40001

def delete_directory_with_contents(directory_path):
    try:
        shutil.rmtree(directory_path)
        print(f"Directory '{directory_path}' and its contents removed successfully.")
    except OSError as e:
        print(f"Error while deleting directory: {str(e)}")

def clean(nodenames):
    for name in nodenames:
        delete_directory_with_contents(f"/home/{username}/{name}")
    os.system("rm -rf ~/oar*; rm -rf ~/OAR*;")

def merge_files(output_file, input_files):
    try:
        directory_path = os.path.dirname(output_file)
        os.makedirs(directory_path, exist_ok=True)
        os.system(f"touch {output_file}")
        with open(output_file, 'a') as merged_file:
            for file_name in input_files:
                with open(file_name, 'r') as input_file:
                    merged_file.write(input_file.read())
        print("Files merged successfully!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def merge_results(fileout, address_ids, result_dir):
    files = []
    for nodename in address_ids.keys():
        files.append(f"/home/{username}/{nodename}{result_dir}/metrics.csv")
    merge_files(fileout, files)

# -------------
#  ROLES
# -------------
_BALLET = "machine"

_CUSER_USER = "cuseruser"
_CUSER_PROVIDER = "cuserprovider"

_CPROVIDER_PROVIDER = "cproviderprovider"
_CPROVIDER_USER = "cprovideruser"

_LINEAR_PROVIDER="linearprovider"
_LINEAR_TRANSFORMER="lineartransformer"

_CIRCULAR_PROVIDER="circularprovider"
_CIRCULAR_TRANSFORMER="circulartransformer"
_CIRCULAR_USER="circularuser"

_STRATIFIED_PROVIDER="stratifiedprovider"
_STRATIFIED_MIDUSER="stratifiedmiduser"
_STRATIFIED_USER="stratifieduser"


def book(site, cluster, time=_DEFAULT_TIME, start=_DEFAULT_START):
    my_network = G5kNetworkConf(id="my_galera_network", type="prod", roles=["my_network"], site=site)
    if start != "now":
        g5k = G5kConf.from_settings(job_type="allow_classic_ssh", job_name=f"plan_inference_ballet", walltime=time, reservation=start)
    else:
        g5k = G5kConf.from_settings(job_type="allow_classic_ssh", job_name=f"plan_inference_ballet", walltime=time)
    g5k.add_network_conf(my_network)
    # Machine 1: cuser_user; cprovider_provider; linear_provider; circular_provider; stratified_provider
    g5k.add_machine(roles=[_BALLET, _CUSER_USER, _CPROVIDER_PROVIDER, _LINEAR_PROVIDER, _CIRCULAR_PROVIDER, _STRATIFIED_PROVIDER],
                    cluster=cluster, nodes=1, primary_network=my_network)
    # Machine 2: circular_user; stratified_user
    g5k.add_machine(roles=[_BALLET, _CIRCULAR_USER, _STRATIFIED_USER],
                    cluster=cluster, nodes=1, primary_network=my_network)
    # Machine | i ∈ [0;_COMPONENT[ : cuser_provider_i; cprovider_user_i; linear_transformer_i; circular_transformer_i; stratified_miduser_i
    for i in range(_COMPONENT):
        g5k.add_machine(roles=[_BALLET, 
                               _CUSER_PROVIDER, _CUSER_PROVIDER+str(i), 
                               _CPROVIDER_USER, _CPROVIDER_USER+str(i),
                               _LINEAR_TRANSFORMER, _LINEAR_TRANSFORMER+str(i), 
                               _CIRCULAR_TRANSFORMER, _CIRCULAR_TRANSFORMER+str(i), 
                               _STRATIFIED_MIDUSER, _STRATIFIED_MIDUSER+str(i)], 
                        cluster=cluster, nodes=1, primary_network=my_network)
    conf = g5k.finalize()
    provider = G5k(conf)
    roles, networks = provider.init()
    return roles, networks

def make_inventory_content(roles, scenario):
    inventory = {}
    # Inventory for cuser
    if scenario == "cuser":
        user_address = roles[_CUSER_USER][0].address
        inventory["user"] =  {'address': user_address, 'port_planner': _PORT}
        for i in range(_COMPONENT):
            provider_address = roles[_CUSER_PROVIDER+str(i)][0].address
            inventory[f'provider{i}'] =  {'address': provider_address, 'port_planner': _PORT}
    # Inventory for cprovider
    if scenario == "cprovider":
        provider_address = roles[_CPROVIDER_PROVIDER][0].address
        inventory["provider"] =  {'address': provider_address, 'port_planner': _PORT}
        for i in range(_COMPONENT):
            user_address = roles[_CPROVIDER_USER+str(i)][0].address
            inventory[f'user{i}'] =  {'address': user_address, 'port_planner': _PORT}
    # Inventory for linear
    if scenario == "linear":
        provider_address = roles[_LINEAR_PROVIDER][0].address
        inventory["provider"] =  {'address': provider_address, 'port_planner': _PORT}
        for i in range(_COMPONENT):
            transformer_address = roles[_LINEAR_TRANSFORMER+str(i)][0].address
            inventory[f'transformer{i}'] =  {'address':transformer_address, 'port_planner': _PORT}
    # Inventory for circular
    if scenario == "circular":
        provider_address = roles[_CIRCULAR_PROVIDER][0].address
        inventory["provider"] =  {'address': provider_address, 'port_planner': _PORT}
        user_address = roles[_CIRCULAR_USER][0].address
        inventory["user"] =  {'address': user_address, 'port_planner': _PORT}
        for i in range(_COMPONENT):
            transformer_address = roles[_CIRCULAR_TRANSFORMER+str(i)][0].address
            inventory[f'transformer{i}'] = {'address': transformer_address, 'port_planner': _PORT}
    # Inventory for stratified
    if scenario == "stratified":
        provider_address = roles[_STRATIFIED_PROVIDER][0].address
        inventory["provider"] =  {'address': provider_address, 'port_planner': _PORT}
        user_address = roles[_STRATIFIED_USER][0].address
        inventory["enduser"] =  {'address': user_address, 'port_planner': _PORT}
        for i in range(_COMPONENT):
            miduser_address = roles[_STRATIFIED_MIDUSER+str(i)][0].address
            inventory[f'user{i}'] = {'address': miduser_address, 'port_planner': miduser_address}
    return inventory

def make_inventory(roles, scenario):
    inventory = make_inventory_content(roles, scenario)
    content = str(inventory)
    # content = json.dump(inventory)
    print(f"Inventory for {scenario}") 
    print(content) 
    filename = f"{scenario}_inventory.json"
    with play_on(pattern_hosts=_BALLET, roles=roles, run_as=username) as p:
        p.shell("echo \"" + content + "\" >> " + filename )

def run(scenario, roles, ite, result_dir):
    make_inventory(roles, scenario)
    if scenario == "cuser":
        run_cuser(roles, ite, result_dir)
    if scenario == "cprovider":
        run_cprovider(roles, ite, result_dir)
    if scenario == "linear":
        run_linear(roles, ite, result_dir)
    if scenario == "circular":
        run_circular(roles, ite, result_dir)
    if scenario == "stratified":
        run_stratified(roles, ite, result_dir)

def run_cuser(roles, ite, result_dir):
    #1 Copy right python file
    script_place = f"{project_dir}examples/tests_gossip/central_user/"
    for i in range(_COMPONENT):
        with play_on(pattern_hosts=_CUSER_PROVIDER, roles=roles, run_as=username) as p:
            p.shell(f"cp {script_place}run_provider.py {project_dir}")
    with play_on(pattern_hosts=_CUSER_USER, roles=roles, run_as=username) as p:
        p.shell(f"cp {script_place}run_user.py {project_dir}")
    #2.1 run SAT 
    for i in range(_COMPONENT):
        with play_on(pattern_hosts=_CUSER_PROVIDER, roles=roles, run_as=username) as p:
            p.shell(f"{minizinc_path()}; python {project_dir}run_provider.py -n 15 -i {i} -inventory cuser_inventory.json --time -it {ite}  --port {_PORT} >> {result_dir}user_sat_provider{i}.log", background=True)
    with play_on(pattern_hosts=_CUSER_USER, roles=roles, run_as=username) as p:
        p.shell(f"{minizinc_path()}; python {project_dir}run_user.py -n 15 -inventory cuser_inventory.json --time -it {ite}  --port {_PORT} >> {result_dir}cuser_sat_user.log")
    #2.2 run UNSAT
    for i in range(_COMPONENT):
        with play_on(pattern_hosts=_CUSER_PROVIDER, roles=roles, run_as=username) as p:
            p.shell(f"{minizinc_path()}; python {project_dir}run_provider.py -n 15 -i {i} --unsat -inventory cuser_inventory.json --time -it {ite} --port {_PORT}  >> {result_dir}cuser_unsat_provider{i}.log", background=True)
    with play_on(pattern_hosts=_CUSER_USER, roles=roles, run_as=username) as p:
        p.shell(f"{minizinc_path()}; python {project_dir}run_user.py -n 15  --unsat -inventory cuser_inventory.json --time -it {ite} --port {_PORT} >> {result_dir}cuser_unsat_user.log")
    #3 Get results and clean
    for i in range(_COMPONENT):
        with play_on(pattern_hosts=_CUSER_PROVIDER, roles=roles, run_as=username) as p:
            p.fetch(src=f"{result_dir}cuser_sat_provider{i}.log", dest="~")
            p.fetch(src=f"{result_dir}cuser_unsat_provider{i}.log", dest="~")
            p.shell(f"rm {project_dir}run_provider.py ")
    with play_on(pattern_hosts=_CUSER_USER, roles=roles, run_as=username) as p:
        p.fetch(src=f"{result_dir}cuser_sat_user.log", dest="~")
        p.fetch(src=f"{result_dir}cuser_unsat_user.log", dest="~")
        p.shell(f"rm {project_dir}run_user.py ")

def run_cprovider(roles):
    pass

def run_linear(roles):
    pass

def run_circular(roles):
    pass

def run_stratified(roles):
    pass

if __name__ == "__main__":
    timestamp="0"
    result_dir = f"/tmp/{timestamp}/"
    roles, networks = book(site="nancy", cluster="gros")
    with play_on(pattern_hosts=_BALLET, roles=roles, run_as=username) as p:
        p.shell(f"mkdir {result_dir}")
    for ite in range(10):
        for scenario in _SCENARIOS:
            run(scenario, roles, ite, result_dir)