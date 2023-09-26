from typing import Set

from ballet.assembly.simplified.assembly import CInstance, Place
from ballet.planner.goal import ReconfigurationGoal, StateReconfigurationGoal, PlaceReconfigurationGoal


class Dispatcher:

    def __init__(self, address: str, port: int, instances: Set[CInstance], active: dict[CInstance, Place],
                 inventory: dict[str, [str, int]],
                 goals: dict[str, ReconfigurationGoal], goal_states: dict[CInstance, Set[ReconfigurationGoal]]):
        self._local_instances = set()
        # Removed unneeded instances
        local_compIDs = set()
        for instance in instances:
            if inventory[instance.id()]["address"] == address and inventory[instance.id()]["port_front"] == port:
                self._local_instances.add(instance)
                local_compIDs.add(instance.id())
        # Cleaned active places dictionary
        self._active_places = {}
        for (instance, place) in active.items():
            if instance.id() in local_compIDs:
                self._active_places[instance] = place
        # The behavior and port goals are shared between all nodes
        self._goals = goals
        # The state goals are local, and become place goals
        self._place_goals = {}
        for (instance, state_goals) in goal_states.items():
            if instance.id() in local_compIDs:
                self._place_goals[instance] = set()
                for state_goal in state_goals:
                    if type(state_goal) == StateReconfigurationGoal:
                        if state_goal.state() == "start":
                            place = self._active_places[instance]
                        elif state_goal.state() == "initial":
                            place = instance.type().initial_place()
                        elif state_goal.state() == "running":
                            place = instance.type().running_place()
                        else:
                            place = state_goal.state()
                        self._place_goals[instance].add(PlaceReconfigurationGoal(place, final=state_goal.final()))
        # TODO exchange all goals with the other nodes
        # The inventory remains global
        self._inventory = inventory

    def instances(self):
        return self._local_instances

    def goals(self):
        return self._goals

    def place_goals(self):
        return self._place_goals

    def active_places(self):
        return self._active_places