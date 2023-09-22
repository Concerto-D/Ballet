import json
import queue
import shutil
import os
from datetime import datetime

from ballet.assembly.concertod.assembly import Assembly
from ballet.executor import global_variables
from ballet.assembly.concertod.component import Component, Group
from ballet.assembly.concertod.connection import Connection
from ballet.assembly.concertod.dependency import DepType, Dependency
from ballet.executor.logger.debug_logger import log
from ballet.assembly.concertod.place import Dock, Place
from ballet.executor.logger.time_logger import create_timestamp_metric, TimestampType
from ballet.assembly.concertod.transition import Transition

ARCHIVE_DIR_NAME = "archives_reprises"
REPRISE_DIR_NAME = "reprise_configs"


class FixedEncoder(json.JSONEncoder):
    """
    Control how to dump each fields of the json object. Each call to the default method correspond to one
    field.
    """
    def default(self, obj):
        if any(isinstance(obj, k) for k in [Assembly, Component, Dependency, Dock, Connection, Place, Transition, Group]):
            return obj.to_json()
        elif isinstance(obj, DepType):
            return obj.name
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, queue.Queue):
            return list(obj.queue)
        else:
            return obj


def build_saved_config_file_path(assembly_name: str) -> str:
    return f"{global_variables.execution_expe_dir}/{REPRISE_DIR_NAME}/saved_config_{assembly_name}.json"


def build_archive_config_file_path(assembly_name: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path_dir = f"{global_variables.execution_expe_dir}/{ARCHIVE_DIR_NAME}/{assembly_name}"
    os.makedirs(path_dir, exist_ok=True)
    return f"{path_dir}/saved_config_{timestamp}.json"


@create_timestamp_metric(TimestampType.TimestampEvent.SAVING_STATE)
def save_config(assembly):
    log.debug("Saving current conf ...")
    assembly.global_nb_instructions_done[global_variables.reconfiguration_name] = global_variables.current_nb_instructions_done
    with open(build_saved_config_file_path(assembly.name), "w") as outfile:
        json.dump(assembly, outfile, cls=FixedEncoder, indent=4)


def load_previous_config(assembly):
    log.debug("Retrieving previous conf ...")
    file_path = build_saved_config_file_path(assembly.name)
    with open(file_path, "r") as infile:
        result = json.load(infile)
        log.debug("done")

    log.debug(f"Archiving file in {build_archive_config_file_path(assembly.get_name())}")
    shutil.copyfile(
        file_path,
        build_archive_config_file_path(assembly.get_name())
    )
    log.debug(f"Removing previous conf ...")
    os.remove(file_path)
    log.debug("done")
    return result


def restore_previous_config(assembly, previous_config):
    """
    This method fill the empty instanciated <assembly> with the values of <previous_config>, that contains
    the previous state of the assembly (the state he was into before going to sleep)
    """
    # Restore components
    components_dicts = previous_config['components']
    components_names = components_dicts.keys()
    components = _instanciate_components(assembly, previous_config)
    for comp_values in components_dicts.values():
        component = _restore_component(assembly, comp_values, components_names, components)
        assembly.components[component.obj_id] = component

    assembly.connections = {}
    # Restore connections between components
    for conn_data in previous_config['connections'].keys():
        dep1_id, dep2_id = conn_data.split("/")
        comp1_name, dep1_name = dep1_id.split("-")
        comp2_name, dep2_name = dep2_id.split("-")

        dep1, dep2 = assembly._compute_dependencies_from_names(comp1_name, dep1_name, comp2_name, dep2_name)
        conn = Connection(dep1, dep2)
        if comp1_name in assembly.components.keys():
            assembly.component_connections[comp1_name].add(conn)
        if comp2_name in assembly.components.keys():
            assembly.component_connections[comp2_name].add(conn)
        assembly.connections[conn.obj_id] = conn

    assembly.act_components = set(previous_config['act_components'])
    for k, v in previous_config['global_nb_instructions_done'].items():
        assembly.global_nb_instructions_done[k] = v
    assembly.waiting_rate = previous_config['waiting_rate']
    assembly.components_states = previous_config['components_states']
    assembly.remote_confirmations = set(remote_conf for remote_conf in previous_config['remote_confirmations'])


def _instanciate_components(assembly, previous_config):
    components_dicts = previous_config['components']
    components = {}
    for comp_values in components_dicts.values():
        comp_id = comp_values['obj_id']
        comp_type = comp_values['component_type']
        component = assembly.instanciate_component(comp_id, comp_type)
        components[comp_id] = component

    return components


def _restore_component(assembly, comp_values, components_names, components):
    comp_id = comp_values['obj_id']
    component = components[comp_id]
    assembly.component_connections[comp_id] = set()
    component.initialized = comp_values['initialized']

    # Restore dependencies
    for dep_values in comp_values['st_dependencies'].values():
        dep_comp = component.st_dependencies[dep_values['dependency_name']]
        dep_comp.set_refusing_state(dep_values['is_refusing'])
        dep_comp.nb_users = dep_values['nb_users']
        dep_comp.data = dep_values['data']

    # Restore groups
    for group_name in comp_values['st_groups'].keys():
        group_comp = component.st_groups[group_name]
        group_vals = comp_values['st_groups'][group_name]
        group_comp.nb_tokens = group_vals['nb_tokens']

    # Restore active places
    for place_dict in comp_values['act_places']:
        place_comp = component.st_places[place_dict['place_name']]
        component.act_places.add(place_comp)

    # Restore active transitions
    for transitions_dict in comp_values['act_transitions']:
        transitions_comp = component.st_transitions[transitions_dict['transition_name']]
        component.act_transitions.add(transitions_comp)

    # Restore active odocks
    for odock in comp_values['act_odocks']:

        # Finding corresponding odock
        for transition in component.st_transitions.values():
            if transition.src_dock.obj_id == odock['obj_id']:
                component.act_odocks.add(transition.src_dock)

    # Restore active idocks
    for idock in comp_values['act_idocks']:

        # Finding corresponding idock
        for transition in component.st_transitions.values():
            if transition.dst_dock.obj_id == idock['obj_id']:
                component.act_idocks.add(transition.dst_dock)

    # Restore active behavior
    component.set_behavior(comp_values['act_behavior'])

    # Restore queued behaviors
    for bhv in comp_values['queued_behaviors']:
        component.queue_behavior(bhv)

    # Restore visited places
    for place_dict in comp_values['visited_places']:
        place_comp = component.st_places[place_dict['place_name']]
        component.visited_places.add(place_comp)

    # Restore round_reconf
    component.round_reconf = comp_values["round_reconf"]  # Used only for central reconfiguration

    return component
