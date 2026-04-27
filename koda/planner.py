from typing import Any
from ballet.assembly.concertod.component import Component
from ballet.assembly.plan.plan import Instruction
from koda.gossip import gossip
from koda.cr_gossip import (
    CostRegularNode,
    cr_init,
    cr_local,
    cr_msg,
    cr_enrich,
    cr_final,
    cr_ack,
)
from ballet.planner.goal import *


def plan(
    node_name: str,
    devops: str,
    components: list[Component],
    connections: list[tuple[str, str, str, str]],
    active: dict[Component, str],
    goals: dict[Component, list[ReconfigurationGoal]],
    port: int,
    inventory: dict[str, dict[str, Any]],
    roots: list[str],
) -> list[Instruction]:
    """
    Ballet+ 's proposal to calculate a plan for Ballet's executor

    :param node_name: The name of the local node
    :param devops: The name of the responsible of the local node
    :param components: The list of local components
    :param connections: The list of connections, while a connection has the form (provider, provide port, user, use port)
    :param active: A mapping between components and the name of their active place
    :param goals: A mapping between components and their reconfiguration goal
    :param port: The port on which run the grpc server used for communicating on the network
    :param inventory: A map between component names and their location with the port used for the planner
                        (e.g., inventory["comp1"] = {"address": "127.0.0.1", "port_planner": 4000})
    :return: returns a list of instructions (pushB, and wait)
    """
    node = CostRegularNode(
        id=node_name,
        admin=devops,
        components=components,
        connections=connections,
        active=active,
        goals=goals,
        port=port,
        inventory=inventory,
    )
    return gossip(node, roots, cr_init, cr_local, cr_msg, cr_enrich, cr_ack, cr_final)
