import multiprocessing
import time
from typing import Set

import requests
from flask import Flask, request, jsonify, make_response

from ballet.planner.goal import BehaviorReconfigurationGoal, PortReconfigurationGoal, ReconfigurationGoal
from ballet.utils import set_utils

global waits
waits = {}
global goals
goals = {}

class FlaskDispatcher:
    global app
    app = Flask(__name__)
    instance = None

    def __init__(self, address, port, torcv: set[str]):
        self._host = address
        self._port = port
        self._address = f"{address}:{port}"
        self._server_process = multiprocessing.Process(target=app.run,
                                                       kwargs={"host": self._host, "port": self._port})
        # FlaskDispatcher.wait = torcv
        waits[self._address] = torcv
        goals[self._address] = {}
        FlaskDispatcher.instance = self

    def start(self):
        self._server_process.start()

    def goals(self):
        return goals[self._address]

    def address(self):
        return self._address

    def __parseBool(self, input: str):
        return input in ["True","true","TRUE","OUI","Oui","oui","T","t","Yes","yes","YES","1"]

    def remove_wait(self, address):
        my_address = f"{self._host}:{self._port}"
        waits[my_address].remove(address)

    def has_wait(self):
        return waits[f"{self._host}:{self._port}"] == set()

    @staticmethod
    @app.route("/ping", methods=['GET'])
    def ping():
        return make_response(jsonify({'message':"pong"}), 200)

    @staticmethod
    @app.route("/done", methods=['POST'])
    def done():
        data = request.get_json()
        if 'address' in data:
            to_remove = data['address']
            FlaskDispatcher.instance.remove_wait(to_remove)
            return make_response(jsonify({'message':f"{to_remove} has been considered as done"}), 200)
        else:
            return make_response(jsonify({'message':f"Can't find address to remove"}), 400)

    def _parse_bhv_goals(self, input: str) -> Set[BehaviorReconfigurationGoal]:
        # behaviors = "[(bhv,false),(bhv,false),(bhv,false)]"
        res = set()
        cleaned = input.replace('[','').replace(']','').replace('(','').replace(')','').split(',')
        if len(cleaned) >= 2:
            for i in range(0, len(cleaned), 2):
                bhv = cleaned[i]
                final = self.__parseBool(cleaned[i + 1]) if i + 1 < len(cleaned) else False
                res.add(BehaviorReconfigurationGoal(bhv, final))
        return res

    def _parse_port_goals(self, input: str) -> Set[PortReconfigurationGoal]:
        # ports == "[(port,status,false),(port,status,false),(port,status,false)]"
        res = set()
        cleaned = input.replace('[','').replace(']','').replace('(','').replace(')','').split(',')
        if len(cleaned) >= 3:
            for i in range(0, len(cleaned), 3):
                port = cleaned[i]
                status = self.__parseBool(cleaned[i + 1]) if i + 1 < len(cleaned) else True
                final = self.__parseBool(cleaned[i + 2]) if i + 2 < len(cleaned) else False
                res.add(PortReconfigurationGoal(port, status, final))
        return res

    @staticmethod
    @app.route("/addGoals", methods=['POST'])
    def addGoals():
        # goals = FlaskDispatcher.instance.goals()
        data = request.get_json()
        if 'compid' in data and 'behavior' in data and 'port' in data:
            print(f"received: {data}")
            compid, behaviors, ports = data['compid'], data['behavior'], data['port']
            for goal in FlaskDispatcher.instance._parse_bhv_goals(behaviors):
                print(f"Add goal: {compid}:{goal}")
                if compid not in goals[FlaskDispatcher.instance.address()]:
                    # TODO add lock1
                    goals[FlaskDispatcher.instance.address()][compid] = set()
                    # TODO add unlock1
                # TODO add lock2
                print(f"before adding {goals[FlaskDispatcher.instance.address()][compid]} ({id(goals)})")
                goals[FlaskDispatcher.instance.address()][compid].add(goal)
                print(f"after adding {goals[FlaskDispatcher.instance.address()][compid]}  ({id(goals)})")
                # TODO add unlock2
            for goal in FlaskDispatcher.instance._parse_port_goals(ports):
                print(f"Add goal: {compid}:{goal}  ({id(goals)})")
                if compid not in goals[FlaskDispatcher.instance.address()]:
                    # TODO add lock3
                    goals[FlaskDispatcher.instance.address()][compid] = set()
                    # TODO add unlock3
                # TODO add lock4
                goals[FlaskDispatcher.instance.address()][compid].add(goal)
                # TODO add unlock4
            return make_response(jsonify({"message": f"The goals has been shared"}), 200)
        else:
            return make_response(jsonify({"error": "Missing 'compid', 'port' or 'status' in request data"}), 400)

class ClientDispatcher:

    def __init__(self, myaddress, myport, inventory: dict[str, dict[str, int]], goals: dict[str, Set[ReconfigurationGoal]]):
        self.__inventory = inventory
        self._torcv = set()
        self._tosend = set()
        for (compid, access) in inventory.items():
            address, port = access['address'], access['port_front']
            self._torcv.add(f"{address}:{port}")
            self._tosend.add(f"{address}:{port}")
        self._address = myaddress
        self._port = myport
        self._server = FlaskDispatcher(myaddress, myport, self._torcv)
        self._server.start()
        self._goals = goals

    def global_goal_synchronization(self):
        print(f"Initially: {goals}, {waits}")
        for address in self._tosend:
            ok = False
            while not ok:
                try:
                    ok = self.ping(address)
                except Exception:
                    time.sleep(1)
            self.sendGoals(self._goals, address)
            self.done(address)
            print(f"my goals: {self._goals}")
        while self._server.has_wait():
            pass
        print(f"Goals have been synchronized, here there are: {self._server.goals()}  ({id(self._server.goals())}, {id(goals)})")
        return goals

    def ping(self, address: str) -> bool:
        rep = requests.get(f"http://{address}/ping")
        rep = rep.json()
        return rep['message'] == "pong"

    def done(self, address: str) -> bool:
        data = {'address': f'{self._address}:{self._port}'}
        rep = requests.post(f"http://{address}/done", json=data)
        rep = rep.json()
        return rep

    def sendGoals(self, goals: dict[str, Set[ReconfigurationGoal]], address: str):
        for (compId, compGoals) in goals.items():
            behavior_goals = set_utils.findAll_in_set(lambda g: g.isBehaviorGoal(), goals[compId])
            port_goals = set_utils.findAll_in_set(lambda g: g.isPortGoal(), goals[compId])
            if behavior_goals != [] or port_goals != []:
                str_behavior_goals = \
                    ','.join(map(lambda g: f"({g.behavior()},{g.final()})", behavior_goals))
                str_port_goals = \
                    ','.join(map(lambda g: f"({g.port()},{g.isEnable()},{g.final()})", port_goals))
                data = { "compid": compId,
                         "behavior": f"{str_behavior_goals}",
                         "port": f"{str_port_goals}" }
                requests.post(f"http://{address}/addGoals", json=data)
