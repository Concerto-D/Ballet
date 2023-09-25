from abc import ABCMeta, abstractmethod
from typing import Dict, Tuple, List, Optional, Union

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType


class MadeusComponent(metaclass=ABCMeta):
    @abstractmethod
    def create(self):
        pass

    def __init__(self):
        self.places: List[str] = []
        self.transitions: Dict[str, Tuple] = {}
        self.dependencies: Dict[str, Tuple[DepType, Union[List[str], List[List[str]]]]] = {}
        self.initial_place: Optional[str] = None

        self.create()

        self._concerto_component = None

    def print_color(self, string: str):
        self._concerto_component.print_color(string)

    def read(self, name: str):
        return self._concerto_component.read(name)

    def write(self, name: str, val):
        return self._concerto_component.write(name, val)


class _MadeusConcertoComponent(Component):
    AUTO_BEHAVIOR = 'autodeploy'

    def __init__(self, mc: MadeusComponent):
        mc._concerto_component = self
        self.mc = mc
        super().__init__()

    def create(self):
        self.places = self.mc.places
        # self.groups = self.mc.groups
        # self.dependencies = self.mc.dependencies
        self.initial_place = self.mc.initial_place

        # Converting transitions
        for t in self.mc.transitions:
            if len(self.mc.transitions[t]) != 3:
                raise Exception("Error: invalid Madeus transition '%s'!" % t)
            (source, destination, action) = self.mc.transitions[t]
            self.transitions[t] = (source, destination, self.AUTO_BEHAVIOR, 0, action)

        # Converting dependencies
        self.dependencies = dict()
        group_id = 0
        for dep_name, dep_details in self.mc.dependencies.items():
            dep_type, bindings = dep_details
            if dep_type == DepType.DATA_PROVIDE or dep_type == DepType.DATA_USE:
                raise Exception("Port %s has type DATA_USE or DATA_PROVIDE which does not make sense!")
            if dep_type == DepType.USE:
                self.dependencies[dep_name] = (DepType.USE, bindings)
            else:
                # bindings is a list of lists of places
                current_group_list: List[str] = []
                for source_places in bindings:
                    self.groups["_group%d" % group_id] = self.get_accessible_places_from(source_places,
                                                                                         [self.AUTO_BEHAVIOR])
                    current_group_list.append("_group%d" % group_id)
                    group_id += 1
                self.dependencies[dep_name] = (DepType.PROVIDE, current_group_list)
