from typing import Set
from concurrent import futures

from ballet.assembly.simplified.assembly import CInstance
from ballet.planner.communication.constraint_message import PortConstraintMessage, RemoteMessaging, ConstraintMessage
from ballet.planner.communication.grpc import message_pb2_grpc, message_pb2
from ballet.planner.communication.grpc.message_pb2_grpc import MessagingServicer

import time
import grpc


class MyServicer(MessagingServicer):

    def __init__(self, components):
        self._mailbox = {comp.id(): set() for comp in components}
        self._acks = {comp.id(): set() for comp in components}
        self._global_acks = set()

    def AddAckByID(self, request, context):
        self._acks[request.targetID].add(request.sourceID)
        return message_pb2.Empty()

    def AddPortConstraint(self, request, context):
        bhv = request.behavior if request.behavior not in ["NONE", "None", "none", ""] else None
        constr = PortConstraintMessage(request.sourceID, request.port, request.status, bhv)
        self._mailbox[request.targetID].add((request.sourceID, request.round, constr))
        return message_pb2.Empty()

    def AddGlobalAck(self, request, context):
        self._global_acks.add(request.id)
        return message_pb2.Empty()

    def ping(self, request, context):
        return message_pb2.Empty()

    def mailbox(self):
        return self._mailbox

    def acks(self):
        return self._acks

    def global_acks(self):
        return self._global_acks

    def reset_mailbox(self, compId):
        self._mailbox[compId] = set()

    def get_mailbox(self, compId, reset=True):
        received = set()
        for m in self._mailbox[compId]:
            received.add(m)
        res = set()
        for (sourceID, round, constr) in received:
            if (constr.port() != "") and (constr.status() != ""):
                res.add((sourceID, round, constr))
        if reset:
            self.reset_mailbox(compId)
        return res

class gRPCMessaging (RemoteMessaging):

    def __init__(self, local_components: list[CInstance], addresses: dict[str, dict[str, str]], port: str, verbose=False):
        self._ips = {}
        toPing = set()
        for comp in addresses.keys():
            comp_host = addresses[comp]["address"]
            comp_port = addresses[comp]["port_planner"]
            full_address = comp_host + ":" + str(comp_port)
            self._ips[comp] = full_address
            toPing.add(full_address)
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self._servicer = MyServicer(local_components)
        message_pb2_grpc.add_MessagingServicer_to_server(self._servicer, self._server)
        self._server.add_insecure_port(f'[::]:{port}')
        self._server.start()
        self.__verbose = verbose
        self.__pingAll(toPing)
        self._remote_send = 0
        self._remote_rcv = 0

    def __ping(self, address):
        with grpc.insecure_channel(address) as channel:
            stub = message_pb2_grpc.MessagingStub(channel)
            msg = message_pb2.Empty()
            stub.ping(msg)

    def __pingAll(self, addresses: list[str]):
        toPing = addresses.copy()
        if self.__verbose:
            print(f"Try to ping the following [{','.join(toPing)}]")
        while len(toPing) != 0:
            addresses_to_ping = toPing.copy()
            for address in addresses_to_ping:
                try:
                    self.__ping(address)
                    toPing.remove(address)
                    if self.__verbose:
                        print(f"{address} successfully pinged. Remaining: [{','.join(toPing)}]")
                except:
                    pass
            time.sleep(1)

    def get_messages(self, comp: CInstance) -> Set[tuple[str, int, ConstraintMessage]]:
        res = self._servicer.get_mailbox(comp.id(), reset=True)
        self._remote_rcv = self._remote_rcv + len(res)
        for (sourceID, round, constr) in res:
            print(f"[REMOTE] {comp.id()} received from {sourceID}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
        return res

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        self._remote_send = self._remote_send + len(messages)
        for (target, constr) in messages:
            print(f"[REMOTE] {source.id()} send to {target}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
            if isinstance(constr, PortConstraintMessage):
                with grpc.insecure_channel(self._ips[target]) as channel:
                    stub = message_pb2_grpc.MessagingStub(channel)
                    msg = message_pb2.portConstraint(sourceID=source.id(), targetID=target, round=str(round), port=constr.port(), status=constr.status(), behavior=constr.behavior())
                    stub.AddPortConstraint(msg)

    def get_acks(self, comp: CInstance) -> Set[str]:
        res = self._servicer.acks()[comp.id()].copy()
        for m in res:
            print(f"[REMOTE] {comp.id()} received ack from {m}")
        return self._servicer.acks()[comp.id()]

    def send_acks(self, source: CInstance, targets: Set[str]):
        for target in targets:
            print(f"[REMOTE] {source.id()} send ack to {target} (at {self._ips[target]})")
            with grpc.insecure_channel(self._ips[target]) as channel:
                stub = message_pb2_grpc.MessagingStub(channel)
                msg = message_pb2.AckID(sourceID=source.id(), targetID=target)
                stub.AddAckByID(msg)

    def bcast_root_acks(self, source: CInstance):
        for ip in self._ips.values():
            with grpc.insecure_channel(ip) as channel:
                stub = message_pb2_grpc.MessagingStub(channel)
                msg = message_pb2.globalAckID(id=source.id())
                stub.AddGlobalAck(msg)

    def get_global_acks(self):
        return self._servicer.global_acks()

    def stop(self):
        self._server.stop()

    def n_remote_send(self):
        return self._remote_send

    def n_remote_rcv(self):
        return self._remote_rcv