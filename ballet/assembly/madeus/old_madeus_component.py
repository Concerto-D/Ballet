from abc import ABCMeta, abstractmethod
from typing import Dict, Tuple, List, Optional

from ballet.assembly.concertod.component import Component


class OldMadeusComponent(metaclass=ABCMeta):
    @abstractmethod
    def create(self):
        pass

    def __init__(self):
        self.places: List[str] = []
        self.transitions: Dict[str, Tuple] = {}
        self.groups: Dict[str, List[str]] = {}
        self.dependencies: Dict[str, Tuple] = {}
        self.initial_place: Optional[str] = None

        self.create()

        self._concerto_component = None

    def print_color(self, string: str):
        self._concerto_component.print_color(string)

    def read(self, name: str):
        return self._concerto_component.read(name)

    def write(self, name: str, val):
        return self._concerto_component.write(name, val)


class _OldMadeusConcertoComponent(Component):
    AUTO_BEHAVIOR = 'autodeploy'

    def __init__(self, mc: OldMadeusComponent):
        mc._concerto_component = self
        self.mc = mc
        super().__init__()

    def create(self):
        self.places = self.mc.places
        self.groups = self.mc.groups
        self.dependencies = self.mc.dependencies
        self.initial_place = self.mc.initial_place

        # Converting transitions
        for t in self.mc.transitions:
            if len(self.mc.transitions[t]) != 3:
                raise Exception("Error: invalid Madeus transition '%s'!" % t)
            (source, destination, action) = self.mc.transitions[t]
            self.transitions[t] = (source, destination, self.AUTO_BEHAVIOR, 0, action)