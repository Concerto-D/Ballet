from ballet.executor.internal_instruction import InternalInstruction


class Reconfiguration:
    def __init__(self):
        self._instructions = []

    def add(self, instance_name, componentType, *args, **kwargs):
        self._instructions.append(InternalInstruction.build_add(instance_name, componentType(*args, **kwargs)))
        return self

    def delete(self, instance_name):
        self._instructions.append(InternalInstruction.build_del(instance_name))
        return self

    def connect(self, instance1_name: str, dep1_name: str, instance2_name: str, dep2_name: str):
        self._instructions.append(
            InternalInstruction.build_connect(instance1_name, dep1_name, instance2_name, dep2_name))
        return self

    def disconnect(self, instance1_name: str, dep1_name: str, instance2_name: str, dep2_name: str):
        self._instructions.append(
            InternalInstruction.build_disconnect(instance1_name, dep1_name, instance2_name, dep2_name))
        return self

    def push_behavior(self, instance_name: str, behavior_name: str):
        self._instructions.append(InternalInstruction.build_push_b(instance_name, behavior_name))
        return self

    def wait(self, instance_name: str):
        self._instructions.append(InternalInstruction.build_wait(instance_name))
        return self

    def wait_all(self):
        self._instructions.append(InternalInstruction.build_wait_all())
        return self

    def call(self, other_reconfiguration):
        self._instructions += other_reconfiguration._get_instructions()

    def _get_instructions(self):
        return self._instructions
