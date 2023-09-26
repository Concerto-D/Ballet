from typing import Set, Iterable

from ballet.assembly.simplified.assembly import CInstance, Place
from ballet.assembly.simplified.assembly_d import DecentralizedComponentInstance
from ballet.assembly.simplified.type.tagging import classtag
from ballet.planner.goal import ReconfigurationGoal, PortReconfigurationGoal, BehaviorReconfigurationGoal, \
    StateReconfigurationGoal
from ballet.utils.dict_utils import sum_dicts
from ballet.utils.iterable_utils import find_in_iterable
from ballet.utils.list_utils import sum_lists
from ballet.utils.set_utils import find_in_set, remove_in_set
from ballet.utils.yaml_utils import addYamlExtension, replace_variables, extract_loop_values
import ballet.assembly.simplified.type.all

import yaml
import re
import string

class AssemblyParser:

    def __init__(self):
        pass

    @staticmethod
    def __yaml_loop_comp(block, variable, lrng, hrng, variables):
        components: dict[str, str] = {}
        active: dict[str, str] = {}
        for value in range(lrng, hrng):
            variables[variable] = value
            for key, value in block.items():
                comp_name = replace_variables(key, variables)
                components[comp_name] = replace_variables(value["type"], variables)
                active[comp_name] = replace_variables(value["active"], variables)
        variables[variable] = None
        return components, active

    @staticmethod
    def __yaml_loop_connects(block, variable, lrng, hrng, variables):
        connects: list[(str, str, str, str)] = []
        for value in range(lrng, hrng):
            variables[variable] = value
            for connections in block:
                source, port_source, target, port_target = connections.split(',')
                source_name = replace_variables(source, variables)
                port_source_name = replace_variables(port_source, variables)
                target_name = replace_variables(target, variables)
                port_target_name = replace_variables(port_target, variables)
                connects.append((source_name, port_source_name, target_name, port_target_name))
        variables[variable] = None
        return connects

    def simple_parse(self, filename) -> (dict[str, str], list[(str, str, str, str)], dict[str, str]):
        components: dict[str, str] = {}
        active: dict[str, str] = {}
        connections: list[(str, str, str, str)] = []
        variables: dict[str, str] = {}
        # Load the YAML file
        with open(addYamlExtension(filename), 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        for key, value in data.items():
            if key == "components":
                for component in value:
                    if re.match(r'\$\{\{ each (\w+) in range\((\d+),(\w+)\)\}\}', component):
                        it_value, lbound, hbound = extract_loop_values(component, variables)
                        block = value[component]
                        new_components, new_active = self.__yaml_loop_comp(block, it_value, lbound, hbound, variables)
                        components = sum_dicts(components, new_components)
                        active = sum_dicts(active, new_active)
                    else:
                        comp_name = replace_variables(component, variables)
                        components[comp_name] = replace_variables(value[component]["type"], variables)
                        active[comp_name] = replace_variables(value[component]["active"], variables)
            elif key == "connections":
                for connect in value:
                    if re.match(r'\$\{\{ each (\w+) in range\((\d+),(\w+)\)\}\}', connect):
                        it_value, lbound, hbound = extract_loop_values(connect, variables)
                        block = value[connect]
                        new_connections = self.__yaml_loop_connects(block, it_value, lbound, hbound, variables)
                        connections = sum_lists(connections, new_connections)
            else:
                variables[key] = value
        return components, connections, active

    @staticmethod
    def get_type(type_name):
        return classtag.find_class_by_tag(type_name)

    def parse(self, filename):
        components, connections, active_places = self.simple_parse(filename)
        id_comps = {}
        instances = set()
        active = {}
        for compId, compType in components.items():
            compT = self.get_type(compType)()
            component = DecentralizedComponentInstance(compId, compT)
            id_comps[compId] = component
            instances.add(component)
        for source_name, port_source_name, target_name, port_target_name in connections:
            if source_name in components.keys():
                my_comp = id_comps[source_name]
                my_port = my_comp.type().get_port(port_source_name)
                if my_port.is_use_port():
                    my_comp.connect_use_port(my_comp.type().get_port(port_source_name), target_name, port_target_name)
                else:
                    my_comp.connect_provide_port(my_comp.type().get_port(port_source_name), target_name, port_target_name)
            if target_name in components.keys():
                my_comp = id_comps[target_name]
                my_port = my_comp.type().get_port(port_target_name)
                if my_port.is_use_port():
                    my_comp.connect_use_port(my_comp.type().get_port(port_target_name), source_name, port_source_name)
                else:
                    my_comp.connect_provide_port(my_comp.type().get_port(port_target_name), target_name, port_source_name)
        for str_comp, str_place in active_places.items():
            my_comp = id_comps[str_comp]
            if str_place == "running":
                my_place = my_comp.type().running_place()
            elif str_place == "initial":
                my_place = my_comp.type().initial_place()
            else:
                try:
                    my_place = my_comp.type().get_place(str_place)
                except AssertionError:
                    raise ValueError(f"{str_place} is not a valide place for {str_comp}. It must be either an existing place or running | initial.")
            active[my_comp] = my_place
        return instances, active, components, connections


class InventoryParser:

    def __init__(self):
        pass

    def parse(self, filename) -> dict[str, dict[str, str]]:
        # Load the YAML file
        with open(addYamlExtension(filename), 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        result: dict[str, dict[str, str]] = {}
        # Iterate through the data and create the dictionary
        for key, values in data.items():
            # Assuming each component has two elements: address and port
            result[key] = {'address': values[0]['address'], 'port_front': values[1]['port_front'],
                           'port_planner': values[2]['port_planner'], 'port_executor': values[3]['port_executor']}
        return result


class GoalParser:

    def __init__(self, instances: Iterable[CInstance], active: dict[CInstance, Place]):
        self.__instances = instances
        self.__active = active

    @staticmethod
    def parse_behavior_goal(goal, goals, instances: Iterable[CInstance]):
        if 'forall' in goal:
            behavior = goal['forall']
            for instance in instances:
                goals[instance.id()].add(BehaviorReconfigurationGoal(behavior))
        if 'component' in goal and 'behavior' in goal:
            component_id = goal['component']
            behavior = goal['behavior']
            goals[component_id].add(BehaviorReconfigurationGoal(behavior))

    @staticmethod
    def parse_port_goal(goal, goals, instances: Iterable[CInstance]):
        if 'forall' in goal:  # Status of ports for all ports of all instances
            # Getting values
            port_status = goal['forall']
            assert port_status == "active" or port_status == "inactive"
            active = True if port_status == "active" else False
            # For all ports of all instances, creating a PortReconfigurationGoal (active or inactive)
            for instance in instances:
                for port in instance.type().ports():
                    # Add if there is not already a goal for this instance and this port
                    if find_in_set(lambda goal: type(goal) == PortReconfigurationGoal and goal.port() == port,
                                   goals[instance.id()]) is None:
                        goals[instance.id()].add(PortReconfigurationGoal(port, active, final=True))

        if 'component' in goal and 'port' in goal and 'status' in goal: # Status of port for specific instance
            # Getting values
            component_id = goal['component']
            port = goal['port']
            port_status = goal['status']
            assert port_status == "active" or port_status == "inactive"
            active = True if port_status == "active" else False
            # Removing existing goal for this instance and this port
            remove_in_set(lambda goal: type(goal) == PortReconfigurationGoal and goal.port() == port,
                          goals[component_id])
            # Adding a new port goal
            goals[component_id].add(PortReconfigurationGoal(port, active, final=True))

    @staticmethod
    def parse_state_goal(goal, goals, instances: Iterable[CInstance]):
        if 'forall' in goal:
            comp_status = goal['forall']
            assert comp_status == "start" or comp_status == "initial" or comp_status == "running"
            for instance in instances:
                # Add if there is not already a state goal for this instance
                if find_in_set(lambda goal: type(goal) == StateReconfigurationGoal, goals[instance]) is None:
                    goals[instance].add(StateReconfigurationGoal(comp_status, final=True))

        if 'component' in goal and 'status' in goal:
            component_id = goal['component']
            component = find_in_iterable(lambda a: a.id() == component_id, instances)
            comp_status = goal['status']
            assert comp_status == "start" or comp_status == "initial" or comp_status == "running"
            # We remove an existing state goal for this instance
            remove_in_set(lambda goal: type(goal) == StateReconfigurationGoal, goals[component])
            goals[component].add(StateReconfigurationGoal(comp_status, final=True))

    def parse(self, filename) -> (dict[string, Set[ReconfigurationGoal]], dict[CInstance, Set[ReconfigurationGoal]]):
        # Load the YAML file
        with open(addYamlExtension(filename), 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        goals: dict[string, Set[ReconfigurationGoal]] = {instance.id(): set() for instance in self.__instances}
        goals_states: dict[CInstance, Set[ReconfigurationGoal]] = {instance: set() for instance in self.__instances}
        # Behavior goals
        if 'behaviors' in data:
            bhv_goals = data["behaviors"]
            for goal in bhv_goals:
                self.parse_behavior_goal(goal, goals, self.__instances)
        # Port goals
        if 'ports' in data:
            port_goals = data["ports"]
            for goal in port_goals:
                self.parse_port_goal(goal, goals, self.__instances)
        # Component status goals
        if 'components' in data:
            component_goals = data["components"]
            for goal in component_goals:
                self.parse_state_goal(goal, goals_states, self.__instances)
        return goals, goals_states

