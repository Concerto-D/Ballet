from abc import ABC, abstractmethod
from typing import Callable, Optional

import time

class Acknowledgement(ABC):
    
    def __init__(self):
        pass
    
    def is_failure(self):
        pass


class GlobalAcknowledgement(ABC):
    
    def __init__(self):
        pass
    
    def is_failure(self):
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
    
    @abstractmethod
    def get_failing_reasons(self):
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
    has_fail_ack = False
    """ Check if one root of the gossip diffusion has sent a global ack """
    def __is_acked(list_of_global_acks, root):
        for ack in list_of_global_acks:
            if ack.source == root:
                return True
        return False
    """ Check if one root of the gossip diffusion has sent a failure global ack """
    def __is_fail_acked(list_of_global_acks, root):
        for ack in list_of_global_acks:
            if ack.source == root and ack.is_failure():
                return True
        return False
    """ Check if all roots of the gossip diffusion has sent a global ack """
    for root in roots:
        if not __is_acked(node.get_global_acks(), root):
            return False, has_fail_ack
        has_fail_ack = has_fail_ack or __is_fail_acked(node.get_global_acks(), root)
    return True, has_fail_ack
    

def gossip (node: Node, roots: list[str],
            f_init: Callable[[Node], Model], 
            f_local: Callable[[Model, Optional[bool]], tuple[list[Message], list[Acknowledgement]]], 
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
        f_msg: Node x list[Message] -> dict[str, list[Message]]
            Decides from a node and list of message w list of message to deliver to target nodes
        f_enrich: Model x list[Message] -> Model
            How to enrich the local model using received message
        f_ack: Node x Acknowledgement -> dict[str, Acknowledgement]
            When a node emits a ack, decides to which it must be sent
        f_final: Model -> Solution 
            When gossip ends, make a final resolution
    """
    # Init a CP model from Node
    model = f_init(node)
    ended_resolution = False
    # Initially, only node considered as roots must process an initial CP solving
    node_is_root = node.is_root(roots)
    must_solve = node_is_root
    # Different tracker for debug and unsat management
    nloop = 0
    is_unsat = False
    has_fail_ack = False
    while not ended_resolution:
        nloop = nloop + 1 
        if debug:
            print(f"====================================================")
            print(f"At the beginning of the {nloop}th loop:")
            node.print_status()
            print(f"====================================================")
        if not is_unsat:
            received_messages = node.new_received_messages() 
            if debug:
                for message in received_messages:
                    print(f"RECEIVE MSG {message}")
            if received_messages != []:
                must_solve = True
                model = f_enrich(model, received_messages)
            if must_solve:
                must_solve = False
                (out_messages, acks_refuse) = f_local(model, debug=debug)
                if acks_refuse != []:
                    # We face a failure... there is no solution? 
                    # We then have FailureAcks to send back
                    target_acks = f_ack(node, acks_refuse)
                    for (target, acks) in target_acks.items():
                        if debug:
                            for ack in acks:
                                print(f"SEND ACK {ack}")
                        node.send_acks(target, acks)
                        is_unsat = True
                elif out_messages != []:
                    # A solution is found, leading to new constraint to diffuse
                    target_messages = f_msg(node, out_messages)
                    for (target, messages) in target_messages.items():
                        if debug:
                            for message in messages:
                                print(f"SEND MSG {message}")
                        node.send_messages(target, messages)
            # Now that the process is done, does the node must send accept acks ?
            target_acks = f_ack(node)
            for (target, acks) in target_acks.items():
                if debug:
                    for ack in acks:
                        print(f"SEND ACK {ack}")
                node.send_acks(target, acks)
            # Check global acks to send, and received, and end local solve if needed
        global_acks = node.get_global_acks_to_send(roots)
        if len(global_acks) != 0:
            if debug:
                for ack in global_acks:
                    print(f"SEND GLOBAL ACK {ack}")
            node.send_global_acks(global_acks)
        ended_resolution, has_fail_ack = check_global_acks(node, roots)
        if debug:
            print(f"====================================================")
            print(f"At the end of the {nloop}th loop:")
            node.print_status()
            print(f"====================================================")
            time.sleep(1)
        node.new_received_ack()
    if has_fail_ack:
        if node_is_root:
            print(node.get_failing_reasons())
        else:
            print("The reconfiguration is unsat considering the current submitted goals.")
            print(node.get_local_conflict())
        return None 
    else:
        return f_final(model)