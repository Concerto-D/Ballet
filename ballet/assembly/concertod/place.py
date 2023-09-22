#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
.. module:: place
   :synopsis: this file contains the Place and Dock classes.
"""

from ballet.assembly.concertod.transition import Transition


class Dock(object):
    """This Dock class is used to create a dock.

        A dock is an input or an output of a place.
    """

    def __init__(self, place, dock_type, transition: Transition):
        self.place = place
        self.dock_type = dock_type
        self.transition = transition

    @property
    def obj_id(self):
        return f"{self.place.obj_id}_{self.transition.transition_name}"

    def to_json(self):
        return {
            "obj_id": self.obj_id,
            "dock_type": self.dock_type
        }

    def get_place(self):
        """
        This method returns the Place object associated to the dock

        :return: a Place object
        """
        return self.place

    def get_type(self):
        """
        This method returns the type of dock

        :return: self.DOCK_TYPE
        """
        return self.dock_type

    def get_transition(self) -> Transition:
        return self.transition

    def get_behavior(self) -> str:
        return self.get_transition().get_behavior()

    def __str__(self):
        return "Docker place: " + str(self.get_place())


class Place(object):
    """This Place class is used to create a place of a component.

        A place represents an evolution state in the deployment of a component.
    """

    def __init__(self, component, name, override_get_output_docks=None, cp=None):  # TODO remove cp
        self.component = component
        self.place_name = name
        self.override_get_output_docks = override_get_output_docks
        self.input_docks = {}  # dictionary behavior -> docks[]
        self.output_docks = {}  # dictionary behavior -> docks[]
        self.provides = []
        self.cp = cp  # TODO remove cp

    @property
    def obj_id(self):
        return f"{self.component.get_name()}_{self.place_name}"

    def to_json(self):
        return {
            "place_name": self.place_name,
            "input_docks": self.input_docks,
            "output_docks": self.output_docks,
            "provides": self.provides,
            "cp": self.cp,
        }

    def create_input_dock(self, transition: Transition):
        """
        This method creates an additional input dock to the current place.
        This method is called by Transition. An input dock of a place
        corresponds to a destination dock of a transition.

        :param transition: the transition to which the dock will be associated
        :param set: the set of input docks it should be contained in
        :return: the new input dock
        """
        new_dock = Dock(self, 0, transition)
        behavior = transition.get_behavior()
        idset = transition.get_dst_idset()
        if behavior not in self.input_docks:
            self.input_docks[behavior] = dict()
        if idset not in self.input_docks[behavior]:
            self.input_docks[behavior][idset] = []
        self.input_docks[behavior][idset].append(new_dock)
        return new_dock

    def create_output_dock(self, transition):
        """
        This method creates an additional output dock to the current place.
        This method is called by Transition. An output dock of a place
        corresponds to a source dock of a transition.

        :param transition: the transition to which the dock will be associated
        :return: the new output dock
        """
        new_dock = Dock(self, 1, transition)
        behavior = transition.get_behavior()
        if behavior not in self.output_docks:
            self.output_docks[behavior] = []
        self.output_docks[behavior].append(new_dock)
        return new_dock

    def get_name(self):
        """
        This method returns the name of the place

        :return: name
        """
        return self.place_name

    def get_groups_of_input_docks(self, behavior):
        """
        This method returns the list of input docks of the place

        :return: self.input_docks[behavior] if not empty, [] otherwise
        """
        if behavior not in self.input_docks:
            return []
        else:
            return list(self.input_docks[behavior].values())

    def get_output_docks(self, behavior):
        """
        This method returns the list of output docks of the place

        :return: self.output_docks[behavior] if not empty, [] otherwise
        """
        if behavior not in self.output_docks:
            return []
        else:
            if self.override_get_output_docks is not None:
                return [self.output_docks[behavior][i] for i in self.override_get_output_docks(self.cp, behavior)]
            else:
                return self.output_docks[behavior]

    def __str__(self):
        return self.place_name
