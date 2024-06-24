from abc import ABC, abstractmethod
from typing import Callable, Optional

import time

class Acknowledgement(ABC):
    
    def __init__(self):
        pass
    

class Node (ABC):
    
    def __init__(self):
        pass
        
    @abstractmethod  
    def get_global_acks(self):
        pass
    
    @abstractmethod
    def id(self):
        pass
    
    @abstractmethod
    def new_received_messages(self):
        pass
    
    @abstractmethod
    def send_messages(self, target, messages):
        pass
    
    @abstractmethod
    def send_message(self, target, message):
        pass 
    
    @abstractmethod
    def send_acks(self, target, acks):
        pass
    
    @abstractmethod
    def send_ack(self, target, ack):
        pass 
    
    @abstractmethod
    def is_root(self):
        pass
    
class Model (ABC):
    
    @abstractmethod
    def solve(self):
        pass


class Message(ABC):
    
    @abstractmethod
    def source(self):
        pass
    
    @abstractmethod
    def target(self):
        pass


class Solution(ABC):
    pass


def check_global_acks(node: Node, roots: list[str]):
    """ Check if one root of the gossip diffusion has sent a global ack """
    def __is_acked(list_of_global_acks, root):
        for ack in list_of_global_acks:
            if ack.source == root:
                return True
        return False
    """ Check if all roots of the gossip diffusion has sent a global ack """
    for root in roots:
        if not __is_acked(node.get_global_acks(), root):
            return False
    return True
    

def gossip (node: Node, roots: list[str],
            f_init: Callable[[Node], Model], 
            f_local: Callable[[Model, Optional[bool]], tuple[list[Message], Optional[Acknowledgement]]], 
            f_msg: Callable[[Node, list[Message]], dict[Node, list[Message]]],
            f_enrich: Callable[[Model, list[Message]], Model],
            f_ack: Callable[[Node, Acknowledgement], dict[Node, Acknowledgement]],
            f_final: Callable[[Model], Solution],
            debug=False):
    """
    Args:
        node: 
            Current node being a part of the assembly
        roots (list[Node]):
            list of nodes from which the diffusion start
        f_init: Node -> Model
            Creates CP model from current node
        f_local: Model -> list[Message] x Option[Acknowledgement]
            Local resolution of the model, and infered output message from results. In some cases, a Ack can be emitted here (e.g., Failure)
        f_msg: Node x list[Message] -> dict[Node, list[Message]]
            Decides from a node and list of message w list of message to deliver to target nodes
        f_enrich: Model x list[Message] -> Model
            How to enrich the local model using received message
        f_ack: Node x Acknowledgement -> dict[Node, Acknowledgement]
            When a node emits a ack, decides to which it must be sent
        f_final: Model -> Solution 
            When gossip ends, make a final resolution
    """
    # Init a CP model from Node
    model = f_init(node)
    ended_resolution = False
    # Initially, only node considered as roots must process an initial CP solving
    must_solve = node.is_root(roots)
    nloop = 0
    while not ended_resolution:
        nloop = nloop + 1 
        received_messages = node.new_received_messages() 
        if received_messages != []:
            must_solve = True
            model = f_enrich(model, received_messages)
        if must_solve:
            must_solve = False
            (out_messages, ack_refuse) = f_local(model, debug)
            if ack_refuse != None:
                # We face a failure... there is no solution? 
                # We then have a Failure ack to send back to roots
                target_acks = f_ack(node, ack_refuse)
                for (target, acks) in target_acks.items():
                    node.send_acks(target, acks)
                break
            elif out_messages != []:
                # A solution is found, leading to new constraint to diffuse
                target_messages = f_msg(node, out_messages)
                for (target, messages) in target_messages.items():
                    node.send_messages(target, messages)
        # Now that the process is done, does the node must send accept acks ?
        target_acks = f_ack(node)
        for (target, acks) in target_acks.items():
            node.send_acks(target, acks)
        # Check global acks to send, and received, and end local solve if needed
        global_acks = node.get_global_acks_to_send(roots)
        if len(global_acks) != 0:
            node.send_global_acks(global_acks)
        ended_resolution = check_global_acks(node, roots)
        if debug:
            print(f"At the end of the {nloop}th loop:")
            node.print_status()
        if debug:
            time.sleep(1)
    return f_final(model)


""" 
node:
f_ack:
    Je dois envoyer un ack:
    - soit un failure
        -> Si mon model local n'a pas de solution
        (1) identifier quelles clauses sont conflictuelles
            * Regarder les messages reçu et comparer
        (2) Envoyer un ack à l'emetteur du message. Ca veut dire qu'a chaque resolution on doit etre capable de dire quels messages j'ai emis,
            et quels messages ont été "neufs" poru cetet resolution
"""