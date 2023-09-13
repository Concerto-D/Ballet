from abc import ABC


class Instruction(ABC):
    pass


class Wait(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self):
        return self._component

    def behavior(self):
        return self._behavior

    def triplet(self):
        return ('wait', self._component, self._behavior)

    def __str__(self):
        return f"wait({self._component}, {self._behavior})"


class PushB(Instruction):

    def __init__(self, component: str, behavior: str):
        self._component = component
        self._behavior = behavior

    def component(self):
        return self._component

    def behavior(self):
        return self._behavior

    def triplet(self):
        return ('pushB', self._component, self._behavior)

    def __str__(self):
        return f"pushB({self._component}, {self._behavior})"


class Plan:

    def __init__(self, name: str, instructions: list[Instruction]):
        self._name = name
        self._instructions = instructions

    def name(self):
        return self._name

    def instructions(self):
        return self._instructions

    def __str__(self):
        res = f"==============\n{self._name}\n==============\n"
        return res + '\n'.join(map(lambda instr: str(instr), self._instructions))
