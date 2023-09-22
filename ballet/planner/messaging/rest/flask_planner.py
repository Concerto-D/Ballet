from typing import Set
from flask import Flask, request, jsonify, app

from ballet.assembly.simplified.assembly import CInstance
from ballet.planner.messaging.constraint_message import PortConstraintMessage, RemoteMessaging, ConstraintMessage

import multiprocessing
import requests
import time


class FlaskServer:

    def __init__(self, port, components):
        self._mailbox = {comp.id(): set() for comp in components}
        self._acks = {comp.id(): set() for comp in components}
        self._global_acks = set()
        self.__host = "0.0.0.0"
        self.__port = port
        app = Flask(__name__)
        self._server_process = multiprocessing.Process(target=app.run, kwargs={"host": self.__host, "port": self.__port})
        self._server_process.start()

    @app.route("/addAcks", methods=['POST'])
    def AddAckByID(self):
        data = request.get_json()
        if 'targetID' in data and 'sourceID' in data:
            target_id = data['targetID']
            source_id = data['sourceID']
            self._acks[target_id].add(source_id)
            return jsonify({"message": f"Acknowledgment added for targetID: {target_id}"})
        else:
            return jsonify({"error": "Missing 'targetID' or 'sourceID' in request data"}), 400

    @app.route("/addConstraint", method=['POST'])
    def AddPortConstraint(self):
        data = request.get_json()
        if 'behavior' in data and 'sourceID' in data and 'targetID' in data and 'port' in data and 'status' in data and 'round' in data:
            bhv = data['behavior']
            source_id = data['sourceID']
            target_id = data['targetID']
            port = data['port']
            status = data['status']
            round = data['round']
            constr = PortConstraintMessage(source_id, port, status, bhv)
            self._mailbox[target_id].add((source_id, round, constr))
            return jsonify({"message": f"Contraint ({source_id},{status},{bhv}) correctly added to {target_id}"})
        else:
            return jsonify({"error": "Missing 'sourceID' or 'targetID' or 'port' or 'behavior' or 'status' in request data"}), 400

    @app.route("/addGlobalAck", method=['POST'])
    def AddPortConstraint(self):
        data = request.get_json()
        if 'id' in data:
            id = data['id']
            self._global_acks.add(id)
            return jsonify({"message": f"{id} has properly sent a global ack"})
        else:
            return jsonify({"error": "Missing 'id' in request data"}), 400

    @app.route("/ping", method=['GET'])
    def ping(self):
        return "pong"

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

    def stop(self):
        self._server_process.close()


class FlaskMessaging (RemoteMessaging):

    def __init__(self, local_components: list[CInstance], addresses: dict[str, str], port: str, verbose=False):
        self._ips = {}
        toPing = set()
        for comp in addresses.keys():
            comp_host = addresses[comp]["address"]
            comp_port = addresses[comp]["port"]
            full_address = comp_host + ":" + str(comp_port)
            self._ips[comp] = full_address
            toPing.add(full_address)
        self._server = FlaskServer(port=port, components=local_components)
        self.__verbose = verbose
        self.__pingAll(toPing)
        self._remote_send = 0
        self._remote_rcv = 0

    def __ping(self, address):
        rep = requests.get(f"http://{address}/ping")
        if rep != "pong":
            raise Exception(f"Ping failure: {address}")

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
        res = self._server.get_mailbox(comp.id(), reset=True)
        self._remote_rcv = self._remote_rcv + len(res)
        for (sourceID, round, constr) in res:
            print(f"[REMOTE] {comp.id()} received from {sourceID}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
        return res

    def send_messages(self, source: CInstance, round: int, messages: Set[tuple[str, ConstraintMessage]]):
        self._remote_send = self._remote_send + len(messages)
        for (target, constr) in messages:
            print(f"[REMOTE] {source.id()} send to {target}: ({constr.source()},{constr.port()},{constr.status()},{constr.behavior()})")
            if isinstance(constr, PortConstraintMessage):
                data = {
                    "behavior": constr.behavior(),
                    "sourceID": constr.source(),
                    "targetID": target,
                    "port": constr.port(),
                    "round": round,
                    "status": constr.status()
                }
                requests.post(f"http://{target}/addConstraint", json=data)

    def get_acks(self, comp: CInstance) -> Set[str]:
        res = self._server.acks()[comp.id()].copy()
        for m in res:
            print(f"[REMOTE] {comp.id()} received ack from {m}")
        return self._server.acks()[comp.id()]

    def send_acks(self, source: CInstance, targets: Set[str]):
        for target in targets:
            data = {
                "targetID": target,
                "sourceID": source.id()
            }
            requests.post(f"http://{self._ips[target]}/addAcks", json=data)

    def bcast_root_acks(self, source: CInstance):
        data = {
            "id": source.id()
        }
        for ip in self._ips.values():
            requests.post(f"http://{ip}/addGlobalAck", json=data)

    def get_global_acks(self) -> Set[str]:
        return self._server.global_acks()

    def stop(self):
        self._server.stop()

    def n_remote_send(self):
        return self._remote_send

    def n_remote_rcv(self):
        return self._remote_rcv

