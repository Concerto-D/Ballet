from typing import List

from ballet.executor.communication.zenoh import zenoh_communication
from ballet.executor.communication.rest import rest_communication
from ballet.executor import global_variables

config = {}

CONN = "CONN"
DECONN = "DECONN"
ACTIVE = "ACTIVE"
INACTIVE = "INACTIVE"


def get_nb_dependency_users(component_name: str, dependency_name: str) -> int:
    if global_variables.is_concerto_d_asynchronous():
        return zenoh_communication.get_nb_dependency_users(component_name, dependency_name)
    else:
        return rest_communication.get_nb_dependency_users(component_name, dependency_name)


def send_nb_dependency_users(nb: int, component_name: str, dependency_name: str):
    if global_variables.is_concerto_d_asynchronous():
        zenoh_communication.send_nb_dependency_users(nb, component_name, dependency_name)
    else:
        return


def get_refusing_state(component_name: str, dependency_name: str) -> int:
    if global_variables.is_concerto_d_asynchronous():
        return zenoh_communication.get_refusing_state(component_name, dependency_name)
    else:
        return rest_communication.get_refusing_state(component_name, dependency_name)


def send_refusing_state(value: int, component_name: str, dependency_name: str):
    if global_variables.is_concerto_d_asynchronous():
        zenoh_communication.send_refusing_state(value, component_name, dependency_name)
    else:
        return


def get_data_dependency(component_name: str, dependency_name: str):
    if global_variables.is_concerto_d_asynchronous():
        return zenoh_communication.get_data_dependency(component_name, dependency_name)
    else:
        return rest_communication.get_data_dependency(component_name, dependency_name)


# TODO: check les utilisations de write
def write_data_dependency(component_name: str, dependency_name: str, data):
    if global_variables.is_concerto_d_asynchronous():
        zenoh_communication.write_data_dependency(component_name, dependency_name)
    else:
        return


def send_syncing_conn(syncing_component: str, component_to_sync: str,  dep_provide: str, dep_use: str, action: str):
    if global_variables.is_concerto_d_asynchronous():
        zenoh_communication.send_syncing_conn(syncing_component, component_to_sync, dep_provide, dep_use, action)
    else:
        return


def is_conn_synced(syncing_component: str, component_to_sync: str,  dep_provide: str, dep_use: str, action: str):
    if global_variables.is_concerto_d_asynchronous():
        return zenoh_communication.is_conn_synced(syncing_component, component_to_sync, dep_provide, dep_use, action)
    else:
        return rest_communication.is_conn_synced(syncing_component, component_to_sync, dep_provide, dep_use, action)


def set_component_state(state: [ACTIVE, INACTIVE], component_name: str, reconfiguration_name: str):
    if global_variables.is_concerto_d_asynchronous():
        zenoh_communication.set_component_state(state, component_name, reconfiguration_name)
    else:
        return


def get_remote_component_state(component_name: str, calling_assembly_name: str, reconfiguration_name: str) -> [ACTIVE, INACTIVE]:
    """
    TODO: harmoniser synchrone et asynchrone
    """
    if global_variables.is_concerto_d_asynchronous():
        return zenoh_communication.get_remote_component_state(component_name, reconfiguration_name)
    else:
        return rest_communication.get_remote_component_state(component_name, calling_assembly_name)


def clear_communication_cache(assembly):
    if global_variables.is_concerto_d_asynchronous():
        return
    else:
        rest_communication.clear_communication_cache(assembly)


def set_provide_deps_to_provided(deps_to_acknowledge: List):
    """
    Passe l'état des dépendences listées à provided
    """
    if global_variables.is_concerto_d_asynchronous():
        return
    else:
        rest_communication.set_provide_deps_to_provided(deps_to_acknowledge)
