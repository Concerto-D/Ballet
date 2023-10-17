import threading
import time
from concurrent import futures
from typing import Set

import grpc

from ballet.gateway.communication.grpc import gateway_pb2_grpc, gateway_pb2
from ballet.planner.goal import PortReconfigurationGoal, BehaviorReconfigurationGoal, ReconfigurationGoal
from ballet.utils import stream_utils


class MessagingServicer (gateway_pb2_grpc.MessagingServicer):

    def __init__(self, torcv: set[str], address = None):
        pass
        self._goals = {}
        self._waits = torcv
        self._address = address
        self._lock_new_goals = threading.Lock()
        self._lock_new_goal_entry = threading.Lock()

    def ping(self, request, context):
        return gateway_pb2.Pong(message="pong")

    def addPortGoals(self, request_iterator, context):
        for request in request_iterator:
            compId = request.component
            port = request.port
            status = request.status
            final = request.final
            goal = PortReconfigurationGoal(port, status, final)
            with self._lock_new_goals:
                if compId not in self._goals:
                    self._goals[compId] = set()
            with self._lock_new_goal_entry:
                self._goals[compId].add(goal)
        return gateway_pb2.Empty()

    def addBehaviorGoals(self, request_iterator, context):
        for request in request_iterator:
            compId = request.component
            bhv = request.behavior
            final = request.final
            goal = BehaviorReconfigurationGoal(bhv, final)
            with self._lock_new_goals:
                if compId not in self._goals:
                    self._goals[compId] = set()
            with self._lock_new_goal_entry:
                self._goals[compId].add(goal)
        return gateway_pb2.Empty()

    def validate(self, request, context):
        self._waits.remove(request.address)
        return gateway_pb2.Empty()

    def goals(self):
        return self._goals

    def hasWait(self):
        return len(self._waits) != 0


class ClientGrpcDispatcher:

    def __init__(self, myhost, myport, inventory: dict[str, dict[str, int]], goals: dict[str, Set[ReconfigurationGoal]]):
        self.__inventory = inventory
        self._torcv = set()
        self._tosend = set()
        for (compid, access) in inventory.items():
            address, port = access['address'], access['port_front']
            self._torcv.add(f"{address}:{port}")
            self._tosend.add(f"{address}:{port}")
        self._host = myhost
        self._port = myport
        self._address = f"{myhost}:{myport}"
        self._goals = goals
        self._servicer = MessagingServicer(self._torcv, self._address)
        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
        gateway_pb2_grpc.add_MessagingServicer_to_server(self._servicer, self._server)
        self._server.add_insecure_port(f'[::]:{myport}')
        self._server.start()

    def goals(self):
        return self._goals

    def stop(self):
        self._server.stop(None)

    def global_goal_synchronization(self):
        for address in self._tosend:
            ok = False
            while not ok:
                try:
                    ok = self.ping(address)
                except Exception:
                    time.sleep(1)
            self.sendGoals(self._goals, address)
            self.done(address)
        while self._servicer.hasWait():
            pass
        self._goals = self._servicer.goals()

    def ping(self, address: str) -> bool:
        with grpc.insecure_channel(f'{address}') as channel:
            stub = gateway_pb2_grpc.MessagingStub(channel)
            empty = gateway_pb2.Empty()
            pong = stub.ping(empty)
            return pong.message == "pong"

    def done(self, address: str) -> bool:
        with grpc.insecure_channel(f'{address}') as channel:
            stub = gateway_pb2_grpc.MessagingStub(channel)
            msg = gateway_pb2.Done(address=f"{self._address}")
            stub.validate(msg)

    def address(self):
        return self._address

    def sendGoals(self, goals: dict[str, Set[ReconfigurationGoal]], address: str):
        with grpc.insecure_channel(f'{address}') as channel:
            stub = gateway_pb2_grpc.MessagingStub(channel)
            port_goals = []
            bhv_goals = []
            for (comp_id, comp_goals) in goals.items():
                for comp_goal in comp_goals:
                    if comp_goal.isPortGoal():
                        port_goals.append((comp_id, comp_goal))
                    if comp_goal.isBehaviorGoal():
                        bhv_goals.append((comp_id, comp_goal))
            self.__send_port_goals(stub, port_goals)
            self.__send_bhv_goals(stub, bhv_goals)

    def __send_bhv_goals(self, stub, bhv_goals):
        to_send = []
        for (compid, goal) in bhv_goals:
            new_goal = gateway_pb2.BehaviorGoal(component=compid, behavior=goal.behavior(), final=goal.final())
            to_send.append(new_goal)
        if to_send != []:
            stream_to_send = stream_utils.stream_from_list(to_send)
            stub.addBehaviorGoals(stream_to_send)

    def __send_port_goals(self, stub, port_goals):
        to_send = []
        for (compid, goal) in port_goals:
            new_goal = gateway_pb2.PortGoal(component=compid, port=goal.port(), status=goal.isEnable(), final=goal.final())
            to_send.append(new_goal)
        if to_send != []:
            stream_to_send = stream_utils.stream_from_list(to_send)
            stub.addPortGoals(stream_to_send)
# }