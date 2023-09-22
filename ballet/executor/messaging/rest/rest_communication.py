import json
import os
from os.path import exists

import yaml
import requests

from ballet.executor.logger.debug_logger import log, log_once
from ballet.executor import global_variables

config = {}

CONN = "CONN"
DECONN = "DECONN"
ACTIVE = "ACTIVE"
INACTIVE = "INACTIVE"


"""
inventory: each component should be associated with an ip/port
"""
inventory = {}
communications_cache = {}


def parse_inventory_file():
    absolute_inventory_path = global_variables.get_inventory_absolute_path()
    log.debug(f"Loading inventory from {absolute_inventory_path}")
    with open(absolute_inventory_path, "r") as f:
        loaded_yaml = yaml.safe_load(f)
        for ass_comp_name, host in loaded_yaml.items():
            inventory[ass_comp_name] = host


def _communication_cache_file_path():
    return f"{global_variables.execution_expe_dir}/communication_cache"


def save_communication_cache(assembly_name):
    communication_cache_file = _communication_cache_file_path()
    log.debug(f"Saving communication cache here {communication_cache_file}")
    os.makedirs(communication_cache_file, exist_ok=True)
    with open(f"{communication_cache_file}/{assembly_name}.json", "w") as f:
        json.dump(communications_cache, f)


def load_communication_cache(assembly_name):
    communication_cache_file = _communication_cache_file_path()
    file_name = f"{communication_cache_file}/{assembly_name}.json"
    log.debug(f"Loading communication cache from {file_name}")
    if not exists(file_name):
        log.debug("Cache DOES NOT exists")
        return
    log.debug("Cache EXISTS")
    with open(file_name, "r") as f:
        loaded_json = json.load(f)
        for key_cache, value in loaded_json.items():
            communications_cache[key_cache] = value

    os.remove(file_name)


def clear_communication_cache(assembly_name):
    """TODO: ne pas clear tout le cache, car besoin certainement des infos sur les connexions si on fait des deconn"""
    log.debug("Go from one reconf to another: CLEARING CACHE")
    communications_cache.clear()
    communication_cache_file = _communication_cache_file_path()
    file_name = f"{communication_cache_file}/{assembly_name}.json"
    if exists(file_name):
        os.remove(file_name)


def set_provide_deps_to_provided(provide_deps_list):
    for comp_name, dep_name in provide_deps_list:
        key_cache = "get_nb_dependency_users" + comp_name + dep_name
        communications_cache[key_cache] = "1"


def _is_url_accessible(url):
    try:
        requests.head(url)
        return True
    except requests.exceptions.ConnectionError:
        return False


def get_results_from_request(key_cache, url, default_value, params=None):
    try:
        if _is_url_accessible(url):
            result = requests.get(url, params=params).text
            if result != "":  # TODO: Bug, sometimes API return blank response
                communications_cache[key_cache] = result
                log_once.debug(f"{url}?{params} accessible, result: {result}")
            else:             # TODO: act as if the remote node is unreachable
                result = default_value
        else:
            result = communications_cache[key_cache] if key_cache in communications_cache.keys() else default_value
            log_once.debug(f"{url}?{params} is not accessible, using cache result: {result} instead")
    except requests.exceptions.ConnectionError as e:
        # log_once.debug(e)
        result = communications_cache[key_cache] if key_cache in communications_cache.keys() else default_value
        log_once.debug(f"{url}?{params} raised an exception, using cache result: {result} instead")
    # time.sleep(0.2)
    return result


# TODO: refacto les routes
def get_nb_dependency_users(component_name: str, dependency_name: str) -> int:
    endpoint_name = "get_nb_dependency_users"
    target_host = inventory[component_name]
    url = f"http://{target_host}/{endpoint_name}/{component_name}/{dependency_name}"
    key_cache = endpoint_name + component_name + dependency_name
    result = int(get_results_from_request(key_cache, url, -1))
    return result


def get_refusing_state(component_name: str, dependency_name: str) -> int:
    endpoint_name = "get_refusing_state"
    target_host = inventory[component_name]
    url = f"http://{target_host}/{endpoint_name}/{component_name}/{dependency_name}"
    key_cache = endpoint_name + component_name + dependency_name
    result = get_results_from_request(key_cache, url, "False") == "True"
    return result


def get_data_dependency(component_name: str, dependency_name: str):
    endpoint_name = "get_data_dependency"
    target_host = inventory[component_name]
    url = f"http://{target_host}/{endpoint_name}/{component_name}/{dependency_name}"
    key_cache = endpoint_name + component_name + dependency_name
    result = get_results_from_request(key_cache, url, "")
    return result


def is_conn_synced(syncing_component: str, component_to_sync: str,  dep_provide: str, dep_use: str, action: str):
    endpoint_name = "is_conn_synced"
    target_host = inventory[component_to_sync]
    url = f"http://{target_host}/{endpoint_name}/{syncing_component}/{component_to_sync}/{dep_provide}/{dep_use}/{action}"
    key_cache = endpoint_name + syncing_component + component_to_sync + dep_provide + dep_use + action
    result = get_results_from_request(key_cache, url, "False") == "True"
    return result


def get_remote_component_state(component_name: str, calling_assembly_name: str) -> [ACTIVE, INACTIVE]:
    endpoint_name = "get_remote_component_state"
    target_host = inventory[component_name]
    url = f"http://{target_host}/{endpoint_name}/{component_name}"
    key_cache = component_name
    params = {"calling_assembly_name": calling_assembly_name}
    result = get_results_from_request(key_cache, url, ACTIVE, params=params)
    return result
