from enum import Enum

from ballet.assembly.concertod.component import Component


class InternalInstructionNumAttribution:
    def __init__(self):
        self.all_instructions_num = 0

    def attribute_num(self, instruction):
        instruction.num = self.all_instructions_num
        self.all_instructions_num += 1


class InternalInstruction:
    class Type(Enum):
        ADD = 0
        DEL = 1
        CONNECT = 2
        DISCONNECT = 3
        PUSH_B = 4
        WAIT = 5
        WAIT_ALL = 6

    def __str__(self):
        if self.type is InternalInstruction.Type.ADD:
            return "add(%s,%s)" % (self.args['name'], type(self.args['comp']).__name__)
        elif self.type is InternalInstruction.Type.DEL:
            return "del(%s)" % (self.args['component_name'])
        elif self.type is InternalInstruction.Type.CONNECT:
            return "con(%s.%s,%s.%s)" % (self.args['comp1_name'], self.args['dep1_name'], self.args['comp2_name'],
                                         self.args['dep2_name'])
        elif self.type is InternalInstruction.Type.DISCONNECT:
            return "dcon(%s.%s,%s.%s)" % (self.args['comp1_name'], self.args['dep1_name'], self.args['comp2_name'],
                                          self.args['dep2_name'])
        elif self.type is InternalInstruction.Type.PUSH_B:
            return "pushB(%s,%s)" % (self.args['component_name'], self.args['behavior'])
        elif self.type is InternalInstruction.Type.WAIT:
            return "wait(%s)" % (self.args['component_name'])
        elif self.type is InternalInstruction.Type.WAIT_ALL:
            return "waitAll()"
        else:
            return "{type: %s, arguments: %s}" % (self.type, str(self.args))

    def __init__(self, instr_type, args):
        self.num = None
        self.type = instr_type
        self.args = args

    @property
    def _p_id(self):
        return self.type

    def get_type(self):
        return self.type

    def get_args(self):
        return self.args

    @staticmethod
    def build_add(name: str, comp: Component):
        return InternalInstruction(
            InternalInstruction.Type.ADD,
            {
                "name": name,
                "comp": comp
            })

    @staticmethod
    def build_del(component_name: str):
        return InternalInstruction(
            InternalInstruction.Type.DEL,
            {
                "component_name": component_name
            })

    @staticmethod
    def build_connect(comp1_name: str, dep1_name: str, comp2_name: str, dep2_name: str):
        return InternalInstruction(
            InternalInstruction.Type.CONNECT,
            {
                "comp1_name": comp1_name,
                "dep1_name": dep1_name,
                "comp2_name": comp2_name,
                "dep2_name": dep2_name
            })

    @staticmethod
    def build_disconnect(comp1_name: str, dep1_name: str, comp2_name: str, dep2_name: str):
        return InternalInstruction(
            InternalInstruction.Type.DISCONNECT,
            {
                "comp1_name": comp1_name,
                "dep1_name": dep1_name,
                "comp2_name": comp2_name,
                "dep2_name": dep2_name
            })

    @staticmethod
    def build_push_b(component_name: str, behavior: str):
        return InternalInstruction(
            InternalInstruction.Type.PUSH_B,
            {
                "component_name": component_name,
                "behavior": behavior
            })

    @staticmethod
    def build_wait(component_name: str, wait_for_refusing_provide: bool = False):
        return InternalInstruction(
            InternalInstruction.Type.WAIT,
            {
                "component_name": component_name,
                "wait_for_refusing_provide": wait_for_refusing_provide
            })

    @staticmethod
    def build_wait_all(wait_for_refusing_provide: bool = False):
        return InternalInstruction(
            InternalInstruction.Type.WAIT_ALL,
            {
                "wait_for_refusing_provide": wait_for_refusing_provide
            })

    def apply_to(self, assembly) -> bool:
        import time
        if self.type is InternalInstruction.Type.ADD:
            return assembly._add(self.args['name'], self.args['comp'])
        elif self.type is InternalInstruction.Type.DEL:
            return assembly._del(self.args['component_name'])
        elif self.type is InternalInstruction.Type.CONNECT:
            return assembly._connect(self.args['comp1_name'], self.args['dep1_name'], self.args['comp2_name'],
                                     self.args['dep2_name'])
        elif self.type is InternalInstruction.Type.DISCONNECT:
            return assembly._disconnect(self.args['comp1_name'], self.args['dep1_name'], self.args['comp2_name'],
                                        self.args['dep2_name'])
        elif self.type is InternalInstruction.Type.PUSH_B:
            return assembly._push_b(self.args['component_name'], self.args['behavior'])
        elif self.type is InternalInstruction.Type.WAIT:
            return assembly._wait(self.args['component_name'])
        elif self.type is InternalInstruction.Type.WAIT_ALL:
            return assembly._wait_all(self.args.get('wait_for_refusing_provide', False))
        else:
            raise Exception("Invalid internal instruction type")
