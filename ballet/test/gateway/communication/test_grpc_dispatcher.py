import unittest
import threading
import time
import sys

from ballet.gateway.communication.grpc.grpc_dispatcher import ClientGrpcDispatcher
from ballet.planner.goal import BehaviorReconfigurationGoal, PortReconfigurationGoal


class TestClientGrpcDispatcher(unittest.TestCase):

    def setUp(self):
        # Create a list to hold the instances of ClientGrpcDispatcher
        self.dispatchers = []

    def tearDown(self):
        # Clean up resources after each test
        for dispatcher in self.dispatchers:
            # Add any cleanup code here
            pass

    def create_dispatcher(self, address, port, inventory, goals):
        dispatcher = ClientGrpcDispatcher(address, port, inventory, goals)
        self.dispatchers.append(dispatcher)

    def test_global_goal_synchronization(self):
        # Define your inventory and goals
        inventory = {
            "c1" : {"address":"127.0.0.1", "port_front":3001},
            "c2": {"address": "127.0.0.1", "port_front": 3002},
            "c3": {"address": "127.0.0.1", "port_front": 3003}
        }
        g1 = BehaviorReconfigurationGoal("update", final=False)
        g2 = BehaviorReconfigurationGoal("update", final=False)
        g3 = PortReconfigurationGoal("service", True, final=True)
        goals_1 = {"c1": set()}
        goals_1["c1"].add(g1)
        goals_2 = {"c2": set()}
        goals_2["c2"].add(g2)
        goals_3 = {"c3": set()}
        goals_3["c3"].add(g3)

        # Create dispatcher instances
        self.create_dispatcher('127.0.0.1', 3001, inventory, goals_1)
        self.create_dispatcher('127.0.0.1', 3002, inventory, goals_2)
        self.create_dispatcher('127.0.0.1', 3003, inventory, goals_3)

        # Wait for a while to allow the servers to start
        # time.sleep(1)

        # Synchronize goals
        for dispatcher in self.dispatchers:
            thread = threading.Thread(target=dispatcher.global_goal_synchronization)
            thread.start()
        time.sleep(1)

        for dispatcher in self.dispatchers:
            for (cid, g) in {"c1": g1, "c2": g2, "c3": g3}.items():
                assert g in dispatcher.goals()[cid]
            dispatcher.stop()




if __name__ == '__main__':
    unittest.main()
