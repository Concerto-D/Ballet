import unittest
import threading
import time
import sys

from ballet.gateway.communication.grpc.grpc_dispatcher import ClientGrpcDispatcher
from ballet.planner.goal import BehaviorReconfigurationGoal, PortReconfigurationGoal

def global_goal_synchronization(id):
    # Define your inventory and goals
    inventory = {
        "c1" : {"address":"127.0.0.1", "port_front":3001},
        "c2": {"address": "127.0.0.1", "port_front": 3002},
        "c3": {"address": "127.0.0.1", "port_front": 3003}
    }
    goals_1 = {"c1": set()}
    goals_1["c1"].add(BehaviorReconfigurationGoal("update", final=False))
    goals_2 = {"c2": set()}
    goals_2["c2"].add(BehaviorReconfigurationGoal("update", final=False))
    goals_3 = {"c3": set()}
    goals_3["c3"].add(PortReconfigurationGoal("service", True, final=True))

    if id == 1:
        goals = goals_1
        port = 3001
    elif id == 2:
        goals = goals_2
        port = 3002
    elif id == 3:
        goals = goals_3
        port = 3003
    else:
        goals = goals_1
        port = 3001


    # Create dispatcher instances
    dispatcher = ClientGrpcDispatcher('127.0.0.1', port, inventory, goals)

    # Wait for a while to allow the servers to start
    # time.sleep(1)

    # Synchronize goals
    dispatcher.global_goal_synchronization()
    print(f"{dispatcher.address()}")
    print(dispatcher.goals())


if __name__ == '__main__':
    global_goal_synchronization(3)
