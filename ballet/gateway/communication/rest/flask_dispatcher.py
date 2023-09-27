import multiprocessing
from typing import Set

import requests
from flask import Flask, request, app, jsonify

from ballet.planner.goal import BehaviorReconfigurationGoal, PortReconfigurationGoal, ReconfigurationGoal
from ballet.utils import set_utils


class FlaskDispatcher:

    def __init__(self, port, components):
        self._goals = {comp.id(): set() for comp in components}
        self.__host = "0.0.0.0"
        self.__port = port
        app = Flask(__name__)
        self._server_process = multiprocessing.Process(target=app.run,
                                                       kwargs={"host": self.__host, "port": self.__port})

    def start(self):
        self._server_process.start()

    def __parseBool(self, input: str):
        return input in ["True","true","TRUE","OUI","Oui","oui","T","t","Yes","yes","YES","1"]

    @app.route("/ping", methods=['GET'])
    def ping(self):
        return jsonify({'message':"pong"}), 400

    def __parse_bhv_goals(self, input: str) -> Set[BehaviorReconfigurationGoal]:
        # behaviors = "[(bhv,false),(bhv,false),(bhv,false)]"
        res = set()
        cleaned = input.replace('[','').replace(']','').replace('(','').replace(')','').split(',')
        for i in range(0, len(cleaned), 2):
            bhv = cleaned[i]
            final = self.__parseBool(cleaned[i + 1]) if i + 1 < len(cleaned) else False
            res.add(BehaviorReconfigurationGoal(bhv, final))
        return res

    def __parse_port_goals(self, input: str) -> Set[PortReconfigurationGoal]:
        # ports == "[(port,status,false),(port,status,false),(port,status,false)]"
        res = set()
        cleaned = input.replace('[','').replace(']','').replace('(','').replace(')','').split(',')
        for i in range(0, len(cleaned), 3):
            bhv = cleaned[i]
            status = self.__parseBool(cleaned[i + 1]) if i + 1 < len(cleaned) else True
            final = self.__parseBool(cleaned[i + 2]) if i + 2 < len(cleaned) else False
            res.add(PortReconfigurationGoal(bhv, status, final))
        return res

    @app.route("/addGoals", methods=['POST'])
    def addGoals(self):
        data = request.get_json()
        if 'compid' in data and 'behavior' in data and 'port' in data:
            compid, behaviors, ports = data['compid'], data['behavior'], data['port']
            for goal in self.__parse_bhv_goals(behaviors):
                self._goals[compid].add(goal)
            for goal in self.__parse_port_goals(ports):
                self._goals[compid].add(goal)
            return jsonify({"message": f"The goals has been shared"}), 200
        else:
            return jsonify({"error": "Missing 'compid', 'port' or 'status' in request data"}), 400

class ClientDispatcher:

    def __init__(self, inventory: dict[str, dict[str, int]]):
        self.__inventory = inventory

    def sendGoals(self, goals: dict[str, Set[ReconfigurationGoal]]):
        for address in self.__inventory:
            self.__sendgoals_to_one(goals, address, self.__inventory[address]["port_front"])

    def ping(self, address: str, port: int) -> bool:
        rep = requests.get(f"http://{address}:{port}/ping")
        if rep != "pong":
            raise Exception(f"Ping failure: {address}:{port}")

    def __sendgoals_to_one(self, goals: dict[str, Set[ReconfigurationGoal]], address: str, port: int):
        while not self.ping(address, port):
            pass
        for (compId, compGoals) in goals.items():
            str_behavior_goals = \
                ','.join(map(lambda g: f"({g.behavior()},{g.final()})",
                             set_utils.findAll_in_set(lambda g: g.isBehaviorGoal(), dict[compId]))
                         )
            str_port_goals = \
                ','.join(map(lambda g: f"({g.port()},{g.isEnable()},{g.final()})",
                             set_utils.findAll_in_set(lambda g: g.isPortGoal(), dict[compId]))
                         )
            data = {
                "compid": compId,
                "behavior": f"{str_behavior_goals}",
                "port": f"{str_port_goals}"
            }
            requests.post(f"http://{address}:{port}/addGoals", json=data)
