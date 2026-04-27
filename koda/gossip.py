import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, NewType

from ballet.utils.dict_utils import min_max_set_size_with_keys

ComponentName = NewType('ComponentName', str)

@dataclass
class Message(ABC):
    source: ComponentName
    target: ComponentName


@dataclass
class Acknowledgement(ABC):
    source: ComponentName
    target: ComponentName
    
    def is_failure(self):
        return False

    def is_success(self):
        return False


@dataclass
class GlobalAcknowledgement(ABC):
    source: ComponentName

    def is_failure(self):
        return False

    def is_success(self):
        return False


class Node(ABC):
        
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
    
class Model(ABC):
    
    @abstractmethod
    def solve(self):
        pass
    
    @abstractmethod
    def get_constraints(self):
        pass


class Solution(ABC): ...

""" Check if one root of the gossip diffusion has sent a global ack """
def __is_acked(list_of_global_acks, root):
    for ack in list_of_global_acks:
        if ack.source == root:
            return True
    return False

def check_all_acked(node: Node, roots: list[str]):
    """ Check if all roots of the gossip diffusion has sent a global ack """
    global_acks = node.get_global_acks()
    # print("CURRENT RECEIVED GLOBAL ACK: ")
    # for glack in global_acks:
    #     print(f"\t {glack.source} ({glack})")
    for root in roots:
        if not __is_acked(global_acks, root):
            return False
    return True

def check_global_acks(node: Node, roots: list[str]):
    has_fail_ack = False
    all_acked = True
    """ Check if one root of the gossip diffusion has sent a failure global ack """
    def __is_fail_acked(list_of_global_acks, root):
        for ack in list_of_global_acks:
            if ack.source == root and ack.is_failure():
                return True
        return False
    """ Check if all roots of the gossip diffusion has sent a global ack """
    global_acks = node.get_global_acks()
    for root in roots:
        has_fail_ack = has_fail_ack or __is_fail_acked(global_acks, root)
        if not __is_acked(global_acks, root):
            all_acked = False
        if not all_acked and has_fail_ack:
            break
    return all_acked, has_fail_ack
    

def gossip (node: Node, roots: list[str],
            f_init: Callable[[Node], Model], 
            f_local: Callable[[Model, Optional[bool]], tuple[list[Message], list[Acknowledgement]]], 
            f_msg: Callable[[Node, list[Message]], dict[Node, list[Message]]],
            f_enrich: Callable[[Model, list[Message]], Model],
            f_ack: Callable[[Node, list[Acknowledgement]], dict[Node, list[Acknowledgement]]],
            f_final: Callable[[Model], Solution],
            debug=False, timed=False, iteration=0):
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
    start_time = time.time()
    # Init a CP model from Node
    node.set_roots(roots)
    model = f_init(node)
    ended_resolution = False
    # Initially, only node considered as roots must process an initial CP solving
    node_is_root = node.is_root()
    must_solve = node_is_root
    # Different tracker for debug and unsat management
    nloop = 0
    is_unsat = False
    has_fail_ack = False
    has_sent_global_ack = False
    num_of_loop = 0
    while not ended_resolution:
        time.sleep(random.uniform(0, 2.0))  
        # Check if all global acks have been sent
        # And if there is a global "failed acked"
        all_acked, has_fail_ack = check_global_acks(node, roots)
        if all_acked:
            break  
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
            all_acked, has_fail_ack = check_global_acks(node, roots)
            if all_acked:
                break
            if received_messages:
                must_solve = True
                model = f_enrich(model, received_messages)
            if must_solve:
                if debug:
                    print(f"====================================================")
                    print(f"During the {nloop}th loop:")
                    node.print_status()
                    print(f"====================================================")
                must_solve = False 
                all_acked, has_fail_ack = check_global_acks(node, roots)
                if all_acked:
                    break
                if debug:
                    print("BEGIN SOLVE")
                (out_messages, acks_refuse) = f_local(model, debug=debug)
                if debug:
                    print("END SOLVE")
                if acks_refuse:
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
                    all_acked, has_fail_ack = check_global_acks(node, roots)
                    if all_acked:
                        break   
                    # A solution is found, leading to new constraint to diffuse
                    target_messages = f_msg(node, out_messages)
                    for (target, messages) in target_messages.items():
                        if debug:
                            for message in messages:
                                print(f"SEND MSG {message}")
                        node.send_messages(target, messages)
            # Now that the process is done, does the node must send accept acks ?
            all_acked, has_fail_ack = check_global_acks(node, roots)
            if all_acked:
                break  
            target_acks = f_ack(node)
            for (target, acks) in target_acks.items():
                if debug:
                    for ack in acks:
                        print(f"SEND ACK {ack}")
                node.send_acks(target, acks)
            # Check global acks to send, and received, and end local solve if needed
        else:
            received_messages = node.new_received_messages() 
            target_acks = f_ack(node)
            # TODO make ack to accept received_messages
            for (target, acks) in target_acks.items():
                if debug:
                    for ack in acks:
                        print(f"SEND ACK {ack}")
                node.send_acks(target, acks)

        if not has_sent_global_ack:
            global_acks = node.get_global_acks_to_send(roots)  
            if len(global_acks) != 0:
                if debug:
                    for ack in global_acks:
                        print(f"SEND GLOBAL ACK {ack}")
                node.send_global_acks(global_acks)
                has_sent_global_ack = True
        all_acked, has_fail_ack = check_global_acks(node, roots)
        if debug:
            print(f"CHECK GLOBAL ACK: all_acked={all_acked} ; has_fail_ack:{has_fail_ack}")
            print(node.get_global_acks())
        ended_resolution = all_acked
        if debug:
            print(f"====================================================")
            print(f"At the end of the {nloop}th loop:")
            node.print_status()
            print(f"ENDED RESOLUTION : {ended_resolution}")
            print(f"====================================================")
            time.sleep(3)  
        num_of_loop += 1  
    if debug:
        print(f"====================================================")
        print(f"At the end :")
        node.print_status()
        print(f"====================================================")

    if has_fail_ack and not timed:
        if node_is_root:
            print(node.get_failing_reasons())
        else:
            print("The reconfiguration is unsat considering the current submitted goals.")
            print(node.get_local_conflict())
        result = None 
    else:
        result = f_final(model)
    # node.global_synchro()

    end_time = time.time()  # Record end time
    elapsed_time = end_time - start_time  # Compute elapsed time
    total_time = f"{elapsed_time:.6f}"

    if timed:
        total_messages = node.get_len_messages()
        model_constraints = model.get_constraints()
        (min_key, min_size), (max_key, max_size) = min_max_set_size_with_keys(model_constraints)
        # component|key|iteration|value
        print(f"{node.id}|total_time|{iteration}|{total_time}", flush=True)
        print(f"{node.id}|loops|{iteration}|{num_of_loop}", flush=True)
        print(f"{node.id}|messages|{iteration}|{total_messages}", flush=True)
        print(f"{min_key}|min_constraint|{iteration}|{min_size}", flush=True)
        print(f"{max_key}|max_constraint|{iteration}|{max_size}", flush=True)

    return result
