from abc import ABC, abstractmethod
from typing import Callable, Optional


class Acknowledgement(ABC):
    
    @abstractmethod
    def accept(): 
        pass
    
    
class AckAccept(Acknowledgement):
    
    def __int__(self):
        pass
    
    def accept(): 
        return True
    
    
class AckRefuse(Acknowledgement):
    
    def __int__(self, message: str):
        self.__message = message
    
    @property
    def message(self):
        return self.__message
    
    def accept(): 
        return False
    

class Node (ABC):
    
    def __init__(self):
        self.__global_acks = {}
        self.__messages = {}
        
    @property   
    def global_acks(self):
        return self.__global_acks
    
    @abstractmethod
    def id(self):
        pass
    
    def new_received_messages(self):
        new_messages = []
        for message in self.__messages.keys():
            if self.__messages[message]:
                new_messages.append(message)
                self.__messages[message] = False
        return new_messages
    
    def send_messages(self, target, messages):
        for message in messages:
            self.send_message(target, message)
    
    def send_message(self, target, message):
        # TODO
        # (i)   Concretely send the message if the message has never been sent before
        # (ii)  If sent: record message, to then decide when a ack can be sent
        pass 
    
    def send_acks(self, target, acks):
        for ack in acks:
            self.send_ack(target, ack)
    
    def send_ack(self, target, ack):
        # TODO
        # (i)   Concretely send the ack
        # (ii)  If sent: mark it somewhere
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


def check_global_acks(node: Node, roots: list[Node]):
    """ Check if all roots of the gossip diffusion has sent a global ack """
    for root in roots:
        if root not in node.global_acks:
            return False
    return True
    

def gossip (node: Node, roots: list[Node],
            f_init: Callable[[Node], Model], 
            f_local: Callable[[Model], (list[Message], Optional[AckRefuse])], 
            f_msg: Callable[[list[Message]], dict[Node, list[Message]]],
            f_enrich: Callable[[Model, list[Message]], Model],
            f_ack: Callable[[Node, Acknowledgement], dict[Node, Acknowledgement]],
            f_final: Callable[[Model], Solution]):
    model = f_init(node)
    ended_resolution = False
    must_solve = node in roots
    while not ended_resolution:
        received_messages = node.new_received_messages() 
        if received_messages != []:
            must_solve = True
            model = f_enrich(model)
            # TODO store these received message in node. It will be useful for knowing to which the 
        if must_solve:
            (out_messages, ack_refuse) = f_local(model)
            if ack_refuse != None:
                # TODO we face a failure... there is no solution. We then have a Failure ack to send back to roots
                target_acks = f_ack(node, ack_refuse)
                for (target, acks) in target_acks:
                    node.send_acks(target, acks)
            elif out_messages == []:
                # TODO we found a solution with nothing to propagate. Then we need to send success acks to nodes which sent messages before
                target_acks = f_ack(node, AckAccept())
                for (target, acks) in target_acks:
                    node.send_acks(target, acks)
            else:
                # A solution is found, leading to new constraint to propagate
                target_messages = f_msg(out_messages)
                for (target, messages) in target_messages.items():
                    node.send_messages(target, messages)
            
        ended_resolution = check_global_acks(node, roots)
    return f_final(model)