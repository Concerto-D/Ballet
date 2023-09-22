from abc import ABC
from typing import Set, Iterable

from ballet.assembly.simplified.assembly import CInstance
from ballet.utils.list_utils import split


class ConstraintMessage (ABC):

    def source(self) -> str:
        pass


class PortConstraintMessage(ConstraintMessage):

    def __init__(self, source: str, port: str, status: str, behavior: str = None):
        self._source = source
        self._port = port
        self._status = status
        self._behavior = behavior

    def __str__(self):
        suff = ""
        if self._behavior != None:
            suff = f"until {self._behavior}"
        return f"the port {self._source}.{self._port} will be {self._status} {suff}"

    def source(self) -> str:
        return self._source

    def port(self) -> str:
        return self._port

    def status(self) -> str:
        return self._status

    def behavior(self) -> str:
        return self._behavior

    def __eq__(self, other):
        if not isinstance(other, PortConstraintMessage):
            return False
        else:
            return self.source() == other.source() and self.port() == other.port() and self.status() == other.status() \
                   and self.behavior() == other.behavior()

    def __hash__(self):
        return hash(self._source) + hash(self._port) + hash(self._behavior) + hash(self._status)

class Messaging (ABC):

    def get_messages(self, comp: CInstance) -> Set[tuple[str, int, ConstraintMessage]]:
        pass

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        pass

    def get_acks(self, comp: CInstance) -> Set[str]:
        pass

    def send_acks(self, source: CInstance, targets: Set[str]):
        pass

    def bcast_root_acks(self, source: CInstance):
        pass

    def get_global_acks(self) -> Set[str]:
        pass

    def stop(self):
        pass

    def n_local_send(self):
        return 0

    def n_remote_send(self):
        return 0

    def n_local_rcv(self):
        return 0

    def n_remote_rcv(self):
        return 0


class LocalMessaging (Messaging):

    def get_messages(self, comp: CInstance) -> Set[tuple[str, int, ConstraintMessage]]:
        pass

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        pass

    def get_acks(self, comp: CInstance) -> Set[str]:
        pass

    def send_acks(self, source: CInstance, targets: Set[str]):
        pass

    def bcast_root_acks(self, source: CInstance):
        pass

    def get_global_acks(self) -> Set[str]:
        pass

    def stop(self):
        pass

    def n_local_send(self):
        return 0

    def n_remote_send(self):
        return 0

    def n_local_rcv(self):
        return 0

    def n_remote_rcv(self):
        return 0


class RemoteMessaging (Messaging):

    def get_messages(self, comp: CInstance) -> Set[tuple[str, int, ConstraintMessage]]:
        pass

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        pass

    def get_acks(self, comp: CInstance) -> Set[str]:
        pass

    def send_acks(self, source: CInstance, targets: Set[str]):
        pass

    def bcast_root_acks(self, source: CInstance):
        pass

    def get_global_acks(self) -> Set[str]:
        pass

    def stop(self):
        pass

    def n_local_send(self):
        return 0

    def n_remote_send(self):
        return 0

    def n_local_rcv(self):
        return 0

    def n_remote_rcv(self):
        return 0


class MailboxMessaging (LocalMessaging):

    def __init__(self, components: Iterable[CInstance]):
        self._mailbox = {comp.id(): set() for comp in components}
        self._acks = {comp.id(): set() for comp in components}
        self._global_acks = set()
        self._local_send = 0
        self._local_rcv = 0

    def get_messages(self, comp: CInstance) -> Set[tuple[str, int, ConstraintMessage]]:
        res = self._mailbox[comp.id()]
        self._local_rcv = self._local_rcv + len(res)
        for (sourceID, round, constr) in res:
            print(f"[LOCAL] {comp.id()} reveived from {sourceID}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
        self._mailbox[comp.id()] = set()
        return res

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        # A message: round, target, constr
        self._local_send = self._local_send + len(messages)
        for (dest, constr) in messages:
            print(
                f"[LOCAL] {source.id()} send to {dest}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
            self._mailbox[dest].add((source.id(), round, constr))

    def get_acks(self, comp: CInstance) -> Set[str]:
        res = self._acks[comp.id()]
        for id in res:
            print(f"[LOCAL] {comp.id()} reveived ack from {id}")
        self._acks[comp.id()] = set()
        return res

    def send_acks(self, source: CInstance, targets: Set[str]):
        for dest in targets:
            print(f"[LOCAL] {source.id()} sends ack to {dest}")
            self._acks[dest].add(source.id())

    def bcast_root_acks(self, source: CInstance):
        self._global_acks.add(source.id())

    def get_global_acks(self) -> Set[str]:
       return self._global_acks

    def stop(self):
        pass

    def n_local_send(self):
        return self._local_send

    def n_local_rcv(self):
        return self._local_rcv


class HybridMessaging (Messaging):

    def __init__(self, local_messaging: LocalMessaging, remote_messaging: RemoteMessaging, local_comps: Set[CInstance]):
        self._local_messaging: LocalMessaging = local_messaging
        self._remote_messaging: RemoteMessaging = remote_messaging
        self._local_comps: Set[CInstance] = local_comps
        self._local_send = 0
        self._remote_send = 0
        self._local_rcv = 0
        self._remote_rcv = 0

    def get_messages(self, comp: CInstance):
        m1 = self._local_messaging.get_messages(comp)
        self._local_rcv = self._local_rcv + len(m1)
        m2 = self._remote_messaging.get_messages(comp)
        self._remote_rcv = self._remote_rcv + len(m2)
        return m1 | m2

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        (m1, m2) = split(lambda msg: msg[0] in map(lambda comp: comp.id(), self._local_comps), messages)
        self._local_messaging.send_messages(source, round, set(m1))
        self._local_send = self._local_send + len(m1)
        self._remote_messaging.send_messages(source, round, set(m2))
        self._remote_send = self._local_send + len(m2)

    def get_acks(self, comp: CInstance) -> Set[str]:
        m1 = self._local_messaging.get_acks(comp)
        m2 = self._remote_messaging.get_acks(comp)
        return m1 | m2

    def send_acks(self, source: CInstance, targets: Set[str]):
        (m1, m2) = split(lambda target: target in map(lambda comp: comp.id(), self._local_comps), targets)
        self._local_messaging.send_acks(source, set(m1))
        self._remote_messaging.send_acks(source, set(m2))

    def bcast_root_acks(self, source: CInstance):
        self._local_messaging.bcast_root_acks(source)
        self._remote_messaging.bcast_root_acks(source)

    def get_global_acks(self) -> Set[str]:
        m1 = self._local_messaging.get_global_acks()
        m2 = self._remote_messaging.get_global_acks()
        return m1 | m2

    def stop(self):
        self._local_messaging.stop()
        self._remote_messaging.stop()

    def n_local_send(self):
       return self._local_send

    def n_remote_send(self):
        return self._remote_send

    def n_local_rcv(self):
        return self._local_rcv

    def n_remote_rcv(self):
        return self._remote_rcv