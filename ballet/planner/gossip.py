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
        # (i)   Concretely send the message if the message has never been sent before
        # (ii)  If sent: record message, to then decide when a ack can be sent
        pass 
    
    def send_acks(self, target, acks):
        for ack in acks:
            self.send_ack(target, ack)
    
    def send_ack(self, target, ack):
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
            f_local: Callable[[Model], (list[Message], Optional[Acknowledgement])], 
            f_msg: Callable[[Node, list[Message]], dict[Node, list[Message]]],
            f_enrich: Callable[[Model, list[Message]], Model],
            f_ack: Callable[[Node, Acknowledgement], dict[Node, Acknowledgement]],
            f_final: Callable[[Model], Solution]):
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
    must_solve = node in roots
    while not ended_resolution:
        received_messages = node.new_received_messages() 
        if received_messages != []:
            must_solve = True
            model = f_enrich(model, received_messages)
            node.add_received_message(received_messages)
        if must_solve:
            (out_messages, ack_refuse) = f_local(model)
            if ack_refuse != None:
                # We face a failure... there is no solution? 
                # We then have a Failure ack to send back to roots
                target_acks = f_ack(node, ack_refuse)
                for (target, acks) in target_acks:
                    node.send_acks(target, acks)
            elif out_messages != []:
                # A solution is found, leading to new constraint to diffuse
                target_messages = f_msg(node, out_messages)
                for (target, messages) in target_messages.items():
                    node.send_messages(target, messages)
        # Now that the process is done, does the node must send accept acks ?
        target_acks = f_ack(node, AckAccept())
        node.send_acks(target, acks)
        ended_resolution = check_global_acks(node, roots)
    return f_final(model)


""" 
node:
    Doit avoir:
        {out_message: Option[Ack]} , pour chaque message envoyé, a-t-il recu un ack? Et quel ack?
        {in_message: Option[Ack]} , pour chaque message recu, a-t-il deja validé via un ack?
        Une liste de global_acks reçu
        A function to send a message to a component

f_init:
    Construit un automate depuis le composant et les goals
    
f_local:
    Trouve un mot, et en deduis l'etat des ports. Pour chaque port qui change:
        provide_port:   on -> off           at the end, the related use ports must be deactivated
                        on -> off -> on     at a moment, the related use ports must be deactivated
        use_port:       off -> on           at the end, the related provide ports must be actived
                        off -> on -> off    at a moment, the related provide ports must be actived
    Faire un message en consequence (port: Port, status: bool, final: bool, wait_behavior: Option[Behavior])
           
f_msg:
    Pour chaque message:  Envoyer le message à chaque composant connecté à ce port.

f_enrich:
    Ajouter 
        + les contraintes de port_status a la resolution (ie, passer par un etat qui valide ce port status)
        + les transitions de wait_comp_behavior

f_ack:
    Je dois envoyer un ack:
    - soit un failure
        -> Si mon model local n'a pas de solution
        (1) identifier quelles clauses sont conflictuelles
            * Regarder les messages reçu et comparer
        (2) Envoyer un ack à l'emetteur du message. Ca veut dire qu'a chaque resolution on doit etre capable de dire quels messages j'ai emis,
            et quels messages ont été "neufs" poru cetet resolution
        
    - soit un success
        -> Si je n'ai rien à envoyer de nouveau, et si pour tout message deja envoyé, j'ai deja recu un ack
        (1) Garder une liste des messages à envoyer et à qui
        (2) A chque fois qu'on emet un nouveau message, on le garde dans un dict: {message: bool} (dans message on a le destinataire)
        (3) A chaque fois qu'on recoit un ack, on passe à true dans {message: bool}
        
f_final:
    Depuis les messages qui avait wait_behavior ≠ None, ajouter une contraintes pour que la transition aparaisse dans le mot puis resoudre
    
"""