# -*- coding: utf-8 -*-

"""
.. module:: remote_dependency
   :synopsis: this file contains the RemoteDependency class.
"""
from ballet.executor.messaging import communication_handler
from ballet.assembly.concertod.dependency import Dependency, DepType


class RemoteDependency(Dependency):
    """
    This class represents a remote_dependency, it serves as an intermediary between this
    assembly an the one that host the real dependency.
    """

    def __init__(self, remote_component_name: str, name: str, dep_type: DepType):
        Dependency.__init__(self, None, name, dep_type)
        self.remote_component_name = remote_component_name

    def get_nb_users(self) -> int:
        """
        On fait dans le topic plutôt qu'en local car la dépendance est remote
        """
        return communication_handler.get_nb_dependency_users(self.remote_component_name, self.dependency_name)

    def set_refusing_state(self, value: bool):
        return

    @property
    def is_refusing(self):
        return communication_handler.get_refusing_state(self.get_component_name(), self.get_name())

    def get_data(self):
        self.check_get_data_is_provide()
        return communication_handler.get_data_dependency(self.get_name(), self.get_component_name())

    def write(self, data):
        self.check_get_data_is_provide()
        return communication_handler.write_data_dependency(self.get_name(), self.get_component_name(), data)

    @property
    def obj_id(self):
        return f"{self.remote_component_name}-{self.dependency_name}"

    def get_component_name(self):
        return self.remote_component_name

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.dependency_name == other.dependency_name and self.remote_component_name == other.remote_component_name

    def __hash__(self):
        return hash((self.dependency_name, self.remote_component_name))
