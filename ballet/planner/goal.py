from abc import ABC
from typing import Union

from ballet.assembly.simplified.assembly import Place, Port, Behavior, ComponentInstance

"""
List of goals that can be set:
    - ReconfigurationGoal
        - BehaviorReconfigurationGoal
            -> "You must proceed this behaviorr"
        - StateReconfigurationGoal
            -> "You must reach this state"
        - PortReconfigurationGoal
            -> "You must enable or disable this port"
    - PortConstraint
            -> "I need you to enable / disable this port, until I do that"
"""


class Goal (ABC):

    def isGoal(self) -> bool:
        return False

    def isBehaviorGoal(self) -> bool:
        return False

    def isPortGoal(self) -> bool:
        return False

    def isPlaceGoal(self) -> bool:
        return False

    def isStateGoal(self) -> bool:
        return False


class ReconfigurationGoal(Goal, ABC):

    def isGoal(self) -> bool:
        return True


class BehaviorReconfigurationGoal(ReconfigurationGoal):

    def __init__(self, bhv: Union[Behavior, str], final: bool = False):
        self._bhv = bhv.name() if type(bhv) == Behavior else bhv
        self._final = final

    def behavior(self) -> str:
        return self._bhv

    def final(self) -> bool:
        return self._final

    def isBehaviorGoal(self) -> bool:
        return True

    def __eq__(self, other) -> bool:
        if isinstance(other, BehaviorReconfigurationGoal):
            return self.behavior() == other.behavior() and self.final() == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._bhv) + hash(self._final)

    def __str__(self):
        return f"[BEHAVIOR] {self._bhv} " + ("(final)" if self._final else "")


class StateReconfigurationGoal(ReconfigurationGoal):

    def __init__(self, state: str, final: bool = True):
        self._state = state
        self._final = final

    def isStateGoal(self) -> bool:
        return True

    def state(self) -> str:
        return self._state

    def final(self) -> bool:
        return self._final

    def __eq__(self, other) -> bool:
        if isinstance(other, StateReconfigurationGoal):
            return self.state() == other.state() and self.final() == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._state) + hash(self._final)

    def __str__(self):
        return f"[STATE] {self._state} " + "(final)" if self._final else ""


class PlaceReconfigurationGoal(ReconfigurationGoal):

    def __init__(self, place: Union[str, Place], final: bool = True):
        self._place = place.name() if type(place) == Place else place
        self._final = final

    def isPlaceGoal(self) -> bool:
        return True

    def place(self) -> str:
        return self._place

    def final(self) -> bool:
        return self._final

    def __eq__(self, other) -> bool:
        if isinstance(other, PlaceReconfigurationGoal):
            return self.place() == other.place() and self.final() == other.final()
        else:
            return False

    def __hash__(self):
        return hash(self._place) + hash(self._final)

    def __str__(self):
        return f"[PLACE] {self._place} " + "(final)" if self._final else ""


class PortReconfigurationGoal(ReconfigurationGoal):

    def __init__(self, port: Union[Port, str], enable: bool, final: bool = True):
        self._port = port.name() if type(port) == Port else port
        self._final = final
        self._enable = enable

    def port(self) -> str:
        return self._port

    def final(self) -> bool:
        return self._final

    def isEnable(self) -> bool:
        return self._enable

    def isDisable(self) -> bool:
        return not self._enable

    def isPortGoal(self) -> bool:
        return True

    def __eq__(self, other) -> bool:
        if isinstance(other, PortReconfigurationGoal):
            return self.port() == other.port() and self.final() == other.final() and self.isEnable() == other.isEnable()
        else:
            return False

    def __hash__(self):
        return hash(self._port) + hash(self._final) + hash(self._enable)

    def __str__(self):
        return f"[PORT] {self._port} - " + ("on" if self._enable else "off") + (" (final)" if self._final else "")


class PortConstraint(Goal):

    def __init__(self, component: Union[ComponentInstance, str], port: Union[Port, str], behavior: Union[Behavior, str],
                 status: Union[bool, str], wait: bool = True):
        self._component = component.id() if type(component) == ComponentInstance else component
        self._port = port.name() if type(port) == Port else port
        self._bhv = behavior.name() if type(behavior) == Behavior else behavior
        self._status = str(status) if type(status) == bool else status
        self._wait = wait

    def component(self) -> str:
        return self._component

    def port(self) -> str:
        return self._port

    def behavior(self) -> str:
        return self._bhv

    def status(self) -> str:
        return self._status

    def wait(self) -> bool:
        return self._wait

    def __eq__(self, other) -> bool:
        if isinstance(other, PortConstraint):
            return self.port() == other.port() and self.component() == other.component() \
                   and self.wait() == other.wait() and self.behavior() == other.behavior() \
                   and self.status() == other.status()
        else:
            return False

    def __hash__(self):
        return hash(self._port) + hash(self._component) + hash(self._bhv) + hash(self._status) + hash(self._wait)

    def __str__(self):
        return f"[PORT] {self._port} - {self._status} " + (f"(until {self._component}.{self._bhv})" if self._component != None else "")