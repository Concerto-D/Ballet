from typing import Optional
from gossip.gossip import Node, Acknowledgement, GlobalAcknowledgement
from ballet.planner.automata import matrix_from_concerto_component
from gossip.cost_regular import CostRegular, MultiCostRegular, MultiPortConstraint, PortConstraint, TransitionConstraint
from ballet.assembly.concertod.component import Component
from ballet.planner.goal import Goal
from ballet.utils.list_utils import find
from ballet.utils.dict_utils import reverse_dict
from ballet.utils import set_utils
from ballet.utils import string_utils
from ballet.utils import time_utils
from ballet.assembly.concertod.dependency import DepType
from ballet.assembly.plan.plan import Plan, Wait, PushB, merge_plans
from gossip.grpc import gossip_pb2_grpc
from gossip.grpc import gossip_pb2

from concurrent import futures

import grpc
import threading
import time

class ConstraintMessage:
    
    def __init__(self, source, target, port, status, behavior, passed_by, final=False):
        self._source = source
        self._target = target
        self._port = port
        self._status = status
        if behavior == "" or  behavior == "None":        
            self._behavior = None
        else:
            self._behavior = behavior
        self._final = final
        self._passed_by = passed_by

    @property
    def source(self):
        return self._source
    
    @property
    def passed_by(self):
        return self._passed_by

    @property
    def target(self):
        return self._target

    @property
    def port(self):
        return self._port

    @property
    def status(self):
        return self._status
    
    @property
    def behavior(self):
        return self._behavior
    
    @property
    def final(self):
        return self._final
    
    def has_to_wait(self):
        return not self._behavior == ""
    
    @property
    def passed_by(self):
        return self._passed_by
    
    def __str__(self):
        str_passed_by = f"[{','.join(self._passed_by)}]"
        return f"(from:{self._source}, to:{self._target}, port:{self._port}, status:{self._status}, bhv:{self._behavior}, passedby: {str_passed_by},"+ f"final:{self._final})"

    def __eq__(self, value):
        if isinstance(value, ConstraintMessage):
            return self.source == value.source and self.target == value.target \
                and self.port == value.port and self.status == value.status \
                and self.behavior == value.behavior \
                and self.final == value.final
                
    def __hash__(self):
        return hash(f"({self.source}->{self.target}:{self.port}^{self._status}~{self.behavior}[{self.final}]||{','.join(self.passed_by)})")
    
    
class AckMessage (Acknowledgement):
    
    def __init__(self):
        pass
    
    def is_failure(self):
        return False
    
    def is_success(self):
        return False
    
    
class AckFailure (AckMessage):
    
    def __init__(self, source, target, constraint, cause):
        self._source = source
        self._target = target
        self._constraint = constraint
        self._cause = cause
    
    @property
    def source(self):
        return self._source
    
    @property
    def target(self):
        return self._target
    
    @property
    def constraint(self):
        return self._constraint
    
    @property
    def cause(self):
        return self._cause
    
    def is_failure(self):
        return True
    
    def set_target(self, value):
        self._target = value
    
    def __eq__(self, value):
        if isinstance(value, AckFailure):
            return self.source == value.source and self.target == value.target \
                and self.constraint == value.constraint and self.cause == value.cause
        return False
                
    def __hash__(self):
        return hash(f"{self.source},{self.target},{self.constraint},{self.cause}")
    
    def __str__(self):
        return (f"AckFailure(FROM {self.source} TO {self.target} ON {self.constraint} BECAUSE OF {self.cause})")
        
    
     
class AckSuccess (AckMessage):
    
    def __init__(self, source, target, constraint):
        self._source = source
        self._target = target
        self._constraint = constraint
        
    @property
    def source(self):
        return self._source
    
    @property
    def target(self):
        return self._target
    
    @property
    def constraint(self):
        return self._constraint
    
    def is_success(self):
        return True
    
    def __eq__(self, value):
        if isinstance(value, AckSuccess):
            return self.source == value.source and self.target == value.target \
                and self.constraint == value.constraint
        return False
                
    def __hash__(self):
        return hash(f"{self.source},{self.target},{self.constraint}")
    
    def __str__(self):
        return f"AckSuccess(FROM {self.source} TO {self.target} ON {self.constraint})"
    
    
class GlobalAckSuccess(GlobalAcknowledgement):
    
    def __init__(self, source):
        self._source = source
    
    @property
    def source(self):
        return self._source
    
    def is_failure(self):
        return False
    
    def __eq__(self, value):
        if isinstance(value, GlobalAckSuccess):
            return self.source == value.source 
        return False
                
    def __hash__(self):
        return hash(f"global-success-{self.source}")
    
    def __str__(self):
        return f"global-success-{self.source}"

    
    
class GlobalAckFailure(GlobalAcknowledgement):
    
    def __init__(self, source):
        self._source = source
    
    @property
    def source(self):
        return self._source
    
    def is_failure(self):
        return True
    
    def __eq__(self, value):
        if isinstance(value, GlobalAckFailure):
            return self.source == value.source 
        return False
                
    def __hash__(self):
        return hash(f"global-failure-{self.source}")
    
    def __str__(self):
        return f"global-failure-{self.source}"



class CRServicer(gossip_pb2_grpc.CostRegularGossipServiceServicer):
    
    def __init__(self):
        self._mailbox = {}
        self._acks = {}
        self._global_acks = set()
        self._lock_new_mailbox = threading.Lock()
        self._lock_add_message = threading.Lock()
        self._lock_new_global_ack = threading.Lock()
        self._lock_new_acks = threading.Lock()
        self._lock_add_ack = threading.Lock()
    
    def add_message(self, request, context):
        target = request.component_target
        passed_by = request.passed_by[1:-1].split(',') 
        message = ConstraintMessage(request.component_source, target, request.port, 
                                    request.status, request.behavior, passed_by, 
                                    request.final)
        with self._lock_new_mailbox:
            if target not in self._mailbox.keys():
                self._mailbox[target] = set()
        with self._lock_add_message:
            self._mailbox[target].add(message)
        return gossip_pb2.Empty()
        
    def get_messages(self, comp_name):
        if comp_name not in self._mailbox.keys():
            return set()
        messages = self._mailbox[comp_name]
        with self._lock_add_message:
            self._mailbox[comp_name] = set()
        return messages

    def add_ack_success(self, request, context):
        target = request.component_target
        message_to_ack = request.to_message 
        passed_by = message_to_ack.passed_by[1:-1].split(',') 
        constraint_to_ack = ConstraintMessage(source=message_to_ack.component_source, target=message_to_ack.component_target, 
                                       port=message_to_ack.port, status=message_to_ack.status, 
                                       behavior=message_to_ack.behavior, passed_by=passed_by,
                                       final=message_to_ack.final)
        ack = AckSuccess(request.component_source, request.component_target, constraint_to_ack)
        # print(f"------ MARK -------")
        # print(f"I RECEIVED ACKSUCCESS FROM {request.component_source} FOR THE CONSTRAINT {constraint_to_ack}")
        with self._lock_new_acks:
            if target not in self._acks.keys():
                self._acks[target] = set()
        with self._lock_add_ack:
            self._acks[target].add(ack)
        return gossip_pb2.Empty()
    
    def get_acks(self, comp_name):
        if comp_name not in self._acks.keys():
            return set()
        acks = self._acks[comp_name]
        with self._lock_add_ack:
            self._acks[comp_name] = set()
        return acks
    
    def get_global_acks(self):
        return self._global_acks

    def add_ack_failure(self, request, context):
        target = request.component_target
        message_to_ack = request.to_message 
        passed_by = message_to_ack.passed_by[1:-1].split(',') 
        constraint_to_ack = ConstraintMessage(source=message_to_ack.component_source, target=message_to_ack.component_target, 
                                       port=message_to_ack.port, status=message_to_ack.status, 
                                       behavior=message_to_ack.behavior, passed_by=passed_by,
                                       final=message_to_ack.final)
        ack = AckFailure(request.component_source, request.component_target, constraint_to_ack, request.cause)
        # print(f"------ MARK -------")
        # print(f"I RECEIVED ACKFAILURE FROM {request.component_source} FOR THE CONSTRAINT {constraint_to_ack}")
        with self._lock_new_acks:
            if target not in self._acks.keys():
                self._acks[target] = set()
        with self._lock_add_ack:
            self._acks[target].add(ack)
        return gossip_pb2.Empty()

    def add_global_ack_success(self, request, context):
        source = request.component_source
        ack = GlobalAckSuccess(source)
        # print(f"GLOBAL ACK FROM {ack.source} ({ack}) IS ADDED")
        with self._lock_new_global_ack:
            self._global_acks.add(ack)
        return gossip_pb2.Empty()
        
    def add_global_ack_failure(self, request, context):
        source = request.component_source
        ack = GlobalAckFailure(source)
        with self._lock_new_global_ack:
            self._global_acks.add(ack)
        return gossip_pb2.Empty()

    def ping(self, request, context):
        return gossip_pb2.Empty()


class CRServer:
    
    def __init__(self, servicer=CRServicer(), port=3000, max_workers=16, inventory: dict[str, dict[str, str]]={}):
        self.__inventory = inventory
        self._full_address = {}
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
        gossip_pb2_grpc.add_CostRegularGossipServiceServicer_to_server(servicer=servicer, server=server)
        server.add_insecure_port(f'[::]:{port}')
        server.start()
        self._server = server
        self._servicer = servicer
        self._wait_for_all()
        
    def stop(self):
        self._server.stop()
    
    def __ping(self, address):
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            msg = gossip_pb2.Empty()
            stub.ping(msg)

    def get_messages(self, component):
        return self._servicer.get_messages(component)
    
    def get_acks(self, component):
        return self._servicer.get_acks(component)
    
    def get_global_acks(self):
        return self._servicer.get_global_acks()

    def _wait_for_all(self):
        to_ping = {}
        n = 0
        for comp in self.__inventory.keys():
            comp_host = self.__inventory[comp]["address"]
            comp_port = self.__inventory[comp]["port_planner"]
            full_address = comp_host + ":" + str(comp_port)
            self._full_address[comp] = full_address
            if full_address not in to_ping.keys():
                to_ping[full_address] = True
                n = n+1
        while n != 0:
            for (address, has_to_be_pinged) in to_ping.items():
                if has_to_be_pinged:
                    try:
                        self.__ping(address)
                        to_ping[address] = False
                        n = n-1
                    except:
                        pass
            
            
class CRClient:
    
    def __init__(self, inventory: dict[str, dict[str, str]]):
        self.__inventory = inventory
        
    @property
    def inventory(self):
        return self.__inventory
    
    def __get_address(self, component):
        comp_host = self.__inventory[component]["address"]
        comp_port = self.__inventory[component]["port_planner"]
        return comp_host + ":" + str(comp_port)
        
    def __get_all_addresses(self):
        addresses = set()
        for component in self.__inventory.keys():
            addresses.add(self.__get_address(component))
        return addresses
        
    def send_message(self, message):
        address = self.__get_address(message.target)
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            passed_by = "["+','.join(message.passed_by)+"]"
            to_send = gossip_pb2.SyncSpec(component_source=message.source, component_target=message.target, 
                                          port=message.port, status=message.status, behavior=message.behavior,
                                          passed_by=passed_by, final=message.final)
            stub.add_message(to_send)
    
    def __send_ack_success(self, ack: AckSuccess):
        address = self.__get_address(ack.target)
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            passed_by = "["+','.join(ack.constraint.passed_by)+"]"
            acked_message = gossip_pb2.SyncSpec(component_source=ack.constraint.source, component_target=ack.constraint.target, 
                                                port=ack.constraint.port, status=ack.constraint.status, behavior=ack.constraint.behavior, 
                                                passed_by=passed_by, final=ack.constraint.final) 
            to_send = gossip_pb2.AckSuccess(component_source = ack.source, component_target = ack.target, 
                                            to_message = acked_message)
            stub.add_ack_success(to_send)
            
    def __send_ack_failure(self, ack: AckFailure):
        address = self.__get_address(ack.target)
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            passed_by = "["+','.join(ack.constraint.passed_by)+"]"
            acked_message = gossip_pb2.SyncSpec(component_source=ack.constraint.source, component_target=ack.constraint.target, 
                                                port=ack.constraint.port, status=ack.constraint.status, behavior=ack.constraint.behavior, 
                                                passed_by=passed_by, final=ack.constraint.final) 
            to_send = gossip_pb2.AckFailure(component_source = ack.source, component_target = ack.target, 
                                            to_message = acked_message, cause = ack.cause)
            
            # print(f"FROM PROXY POV, I AM SENDING : {ack}")
            stub.add_ack_failure(to_send)
    
    def send_ack(self, ack: AckMessage):
        # print(f"FROM CLIENT POV, I AM SENDING : {ack}")
        if isinstance(ack, AckSuccess):
            # print(f"WHICH IS SUCCESS")
            self.__send_ack_success(ack)
        elif isinstance(ack, AckFailure):
            # print(f"WHICH IS FAILURE")
            self.__send_ack_failure(ack)
            
    def __send_global_ack_success(self, address, ack: GlobalAckSuccess):
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            to_send = gossip_pb2.GlobalAckSuccess(component_source=ack.source)
            stub.add_global_ack_success(to_send)      
    
    def __send_all_global_ack_success(self, ack: GlobalAckSuccess):
        addresses = self.__get_all_addresses()
        for address in addresses:
            self.__send_global_ack_success(address, ack)
            
    def __send_global_ack_failure(self, address, ack: GlobalAckFailure):
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            to_send = gossip_pb2.GlobalAckFailure(component_source=ack.source)
            stub.add_global_ack_failure(to_send)          
        
    def __send_all_global_ack_failure(self, ack: GlobalAckSuccess):
        addresses = self.__get_all_addresses()
        for address in addresses:
            self.__send_global_ack_failure(address, ack)
        
    def send_global_ack(self, ack: GlobalAcknowledgement):
        if isinstance(ack, GlobalAckSuccess):
            self.__send_all_global_ack_success(ack)
        elif isinstance(ack, GlobalAckFailure):
            self.__send_all_global_ack_failure(ack)
    
    
class CRP2P:
    
    def __init__(self, port, inventory: dict[str, dict[str, str]]):
        self._server = CRServer(port=port, inventory=inventory)
        self._client = CRClient(inventory=inventory)
    
    def send_message(self, message):
        self._client.send_message(message)
    
    def send_ack(self, ack):
        self._client.send_ack(ack)
    
    def send_global_ack(self, ack):
        self._client.send_global_ack(ack)
    
    def get_messages(self, component):
        return self._server.get_messages(component)
    
    def get_acks(self, component):
        return self._server.get_acks(component)
    
    def get_global_acks(self):
        return self._server.get_global_acks()
    
    def wait_for_all(self):
        self._server._wait_for_all()
    

class CostRegularNode(Node):
    
    def __init__(self, id: str, admin: str, connections: list[(str, str, str, str)], components: list[Component], active: dict[Component, str], goals: dict[Component, list[Goal]], port, inventory):
        self._id = id
        self._components = components
        self.__dict_components = {component.get_name(): component for component in components}
        self._active = active
        self._goals = goals
        self._connections = connections
        for comp in components:
            if comp not in goals:
                goals[comp] = []
        self._admin = admin
        self._passed_by = set()
        # Communication management
        self.__global_acks = set()
        self.__out_message = {comp_name: {} for comp_name in self.__dict_components.keys()} # pour chaque message envoyé, a-t-il recu un ack? Et quel ack?
        self.__in_message = {comp_name: {} for comp_name in self.__dict_components.keys()}  # pour chaque message recu, a-t-il deja validé via un ack?
        self._p2p_service = CRP2P(port, inventory) 
        # Track constraint-messages
        self.__latest_constraints = []
        self.__origin_of_constraint = {} # For a constraint, establish what message made it
        self.__consequence_of_constraint = {} # For a constraint, establish what messages have been emitted 
        self.__origin_constraint_of_message = {} # For a message, what constraint led to it (reverse of __consequence_of_constraint)
        self.__local_conflicting_reasons = ""
        self.__roots = []
        
    def __is_processed(self, list_of_global_acks, root):
        for ack in list_of_global_acks:
            if ack.source == root:
                return True
        return False
    
    def __root_processed(self):
        global_acks = self.get_global_acks()
        for root in self.__roots:
            if not self.__is_processed(global_acks, root):
                return False
        return True
            
    def set_roots(self, roots):
        self.__roots = roots
        
    def add_root(self, root):
        self.__roots.add(root)
        
    def is_comp_root(self, comp):
        return comp in self.__roots
        
    def set_local_conflict(self, local):
        self.__local_conflicting_reasons = local
        
    def get_local_conflict(self):
        return self.__local_conflicting_reasons
        
    def set_lastest_constraints(self, latest):
        self.__latest_constraints = latest
        
    def get_lastest_constraints(self):
        res = self.__latest_constraints
        self.__latest_constraints = []    
        return res
    
    def get_out_message(self):
        return self.__out_message
        
    def get_in_message(self):
        return self.__in_message
    
    def get_failing_reasons(self):
        count = 1
        results = []
        for (_, message_ack) in self.__out_message.items():
            for (_, ack) in message_ack.items():
                if ack != None and isinstance(ack, AckFailure):
                    cause = ack.cause.replace('_9_', ',').replace('/\\', '\n \t & ')
                    results.append(f"{count}. {cause}\n")
                    count = count + 1
        return '\n'.join(results)
    
    def add_origin_of_constraint(self, constraint, message):
        self.__origin_of_constraint[constraint] = message
        
    def get_origin_of_constraint(self, constraint):
        for (constr, origin) in self.__origin_of_constraint.items():
            if constraint == constr: 
                return origin
        return None
    
    def get_all_origins_of_constraint(self):
        return self.__origin_of_constraint
    
    def get_origin_constraint_of_a_message(self, message):
        if message in self.__origin_constraint_of_message.keys():
            return self.__origin_constraint_of_message[message]
        return None
    
    def get_all_origin_constraints_of_a_message(self,):
        return self.__origin_constraint_of_message
    
    def add_consequence_of_constraints(self, constraints, message):
        for constraint in constraints:
            self.add_consequence_of_constraint(constraint, message)
    
    def add_consequence_of_constraint(self, constraint, messages):
        if constraint not in self.__consequence_of_constraint.keys():
            self.__consequence_of_constraint[constraint] = set()
        for message in messages:
            self.__consequence_of_constraint[constraint].add(message)
            self.__origin_constraint_of_message[message] = constraint 
    
    def get_len_messages(self):
        number_of_messages = 0
        for comp_name in self.__out_message.keys():
            number_of_messages = number_of_messages + len(self.__out_message[comp_name].keys())
        return number_of_messages
    
    def print_status(self):
        print(f"PASSED BY: [{','.join(self._passed_by)}]", flush=True)
        print("OUT_MESSAGES:", flush=True)
        for comp_name in self.__out_message.keys():
            print(f"\t- {comp_name}:", flush=True)
            for message in self.__out_message[comp_name].keys():
                if self.__out_message[comp_name][message] != None and isinstance(self.__out_message[comp_name][message], AckSuccess):
                    acked = "ACKED SUCCESS"
                if self.__out_message[comp_name][message] != None and isinstance(self.__out_message[comp_name][message], AckFailure):
                    acked = "ACKED FAILURE"
                else:
                    acked = str(self.__out_message[comp_name][message])
                str_message = f"({message.source}, {message.target}, {message.port}, {message.status}, {message.behavior}, [{','.join(message.passed_by)}], {message.final})"
                print(f"\t\t* {str_message}: {acked}", flush=True)
            
        print("IN_MESSAGES:", flush=True)
        for comp_name in self.__in_message.keys():
            print(f"\t- {comp_name}", flush=True)
            for message in self.__in_message[comp_name].keys():
                if self.__in_message[comp_name][message] != None and isinstance(self.__in_message[comp_name][message], AckSuccess):
                    acked = "ACKED SUCCESS"
                if self.__in_message[comp_name][message] != None and isinstance(self.__in_message[comp_name][message], AckFailure):
                    acked = "ACKED FAILURE"
                else:
                    acked = str(self.__in_message[comp_name][message])
                    
                str_message = f"({message.source}, {message.target}, {message.port}, {message.status}, {message.behavior}, [{','.join(message.passed_by)}], {message.final})"
                print(f"\t\t* {str_message}: {acked}", flush=True)
        
    def new_received_messages(self):
        all_new_messages = set()
        for component in self._components:
            comp_name = component.name
            messages = self._p2p_service.get_messages(comp_name)
            # all_new_messages = all_new_messages | messages
            for message in messages:
                for passed_by in message.passed_by:
                    if passed_by not in self._passed_by:
                        self._passed_by.add(passed_by)
                if not message in self.__in_message[comp_name].keys():
                    self.__in_message[comp_name][message] = None
                    all_new_messages.add(message)
        return list(all_new_messages)
    
    def send_messages(self, target, messages):
        for message in messages:
            self.send_message(target, message)
            
    def send_message(self, target, message):
        assert target == message.target
        def __sec_send_message(message):
            try:
                self._p2p_service.send_message(message)
                if message not in self.__out_message[message.source].keys():
                    self.__out_message[message.source][message] = None
            except Exception as e:
                if not self.__root_processed():
                    __sec_send_message(message)
                else:
                    print(f"UNREACHABLE HOST FOR SENDING {message}", flush=True)
                    time.sleep(10)
                    raise e
        __sec_send_message(message)
        
        
    def send_acks(self, target, acks):
        for ack in acks:
            self.send_ack(target, ack)
    
    def send_ack(self, target, ack):
        def __sec_send_ack(ack):
            try:
                self._p2p_service.send_ack(ack)
            except Exception as e:
                if not self.__root_processed():
                    __sec_send_ack(ack)
                else:
                    print(f"UNREACHABLE HOST FOR SENDING {ack}", flush=True)
                    time.sleep(10)
                    raise e
        # print(f"---------- MARK ---------")
        # print(f"SENDING ACK {ack} ..... ")
        self.mark_in_message(ack.source, ack.constraint, ack) 
        __sec_send_ack(ack)
            
        
        
    def new_received_ack(self):
            for component in self._components:
                comp_name = component.name
                acks = self._p2p_service.get_acks(comp_name) 
                for ack in acks:
                    for message in self.__out_message[comp_name].keys():
                        if message == ack.constraint:
                            self.__out_message[comp_name][message] = ack
        
    def remove_deplicata(self, out_messages):
        result = set()
        already_sent = set() 
        for comp_name in self.__out_message.keys():
            for message in self.__out_message[comp_name].keys():
                already_sent.add(message)
        for message in out_messages:
            if message not in already_sent:
                result.add(message)
        return list(result)
    
    def get_global_acks_to_send(self, roots):
        result = set()
        for comp_name in self.__out_message.keys():
            if comp_name in roots:
                ack_to_send = True
                ack_is_success = True
                # 3 cases: no ack to send, a neg_ack if exists on message with neg_global_ack, a pos_global_ack if all message have pos_ack
                for message in self.__out_message[comp_name].keys():
                    if self.__out_message[comp_name][message] == None:
                        ack_to_send = False
                        break
                    if isinstance(self.__out_message[comp_name][message], AckFailure):
                        ack_is_success = False
                        break
                if ack_to_send:
                    for message in self.__in_message[comp_name].keys():
                        if self.__in_message[comp_name][message] == None:
                            ack_to_send = False
                            break
                        if isinstance(self.__in_message[comp_name][message], AckFailure):
                            ack_is_success = False
                            break
                if ack_to_send:
                    # print(f"I HAVE TO SEND A GLOBAL ACK ! (success ? {ack_is_success}). Here my data:")
                    # self.print_status()
                    if ack_is_success:
                        result.add(GlobalAckSuccess(comp_name))
                    else:
                        result.add(GlobalAckFailure(comp_name))
        return result
    
    def is_root(self, roots):
        for comp_name in self.__out_message.keys():
            if comp_name in roots:
                return True
        return False
    
    def send_global_acks(self, acks):
        for ack in acks:
            self.send_global_ack(ack)
            
    def send_global_ack(self, ack):
        def __sec_send_global_ack(ack):
            try:
                self._p2p_service.send_global_ack(ack)
            except Exception as e:
                if not self.__root_processed():
                    __sec_send_global_ack(ack)
                else:
                    # print(f"UNREACHABLE HOST FOR SENDING {ack}")
                    time.sleep(10)
                    raise e
        __sec_send_global_ack(ack)
        
    def sync_global_acks(self):   
        acks = self._p2p_service.get_global_acks()
        for ack in acks:
            self.__global_acks.add(ack)
        return self.__global_acks
        
    def get_ack_in_message(self, comp_name, message):
        return self.__in_message[comp_name][message]
    
    def get_ack_out_message(self, comp_name, message):
        return self.__out_message[comp_name][message]
    
    def mark_in_message(self, comp_name, message, to_send_ack):
        self.__in_message[comp_name][message] = to_send_ack
    
    @property
    def global_acks(self):
        return self.sync_global_acks()
    
    def get_global_acks(self):
        return self.global_acks
    
    @property
    def components(self):
        return self._components
    
    def use_by(self, provider, provide_port):
        res = []
        for (_provider, _provide_port, _user, _use_port) in self._connections:
            if provider == _provider and _provide_port == provide_port:
                res.append(_user)
        return res
    
    def use_by_port(self, provider, provide_port, user):
        res = []
        for (_provider, _provide_port, _user, _use_port) in self._connections:
            if provider == _provider and _provide_port == provide_port and user == _user:
                res.append(_use_port)
        return res
    
    def provide_by(self, user, use_port):
        res = []
        for (_provider, _provide_port, _user, _use_port) in self._connections:
            if user == _user and _use_port == use_port:
                res.append(_provider)
        return res
    
    def provide_by_port(self, user, use_port, provider):
        res = []
        for (_provider, _provide_port, _user, _use_port) in self._connections:
            if user == _user and _use_port == use_port and _provider == provider:
                res.append(_provide_port)
        return res
    
    @property
    def id(self):
        return self._id
        
    def components_from_str(self, key):
        return self.__dict_components[key]
    
    @property
    def active(self):
        return self._active
    
    @property
    def goals(self):
        return self._goals
    
    @property
    def admin(self):
        return self._admin
    
    @property
    def connections(self):
        return self._connections
    
    @property
    def passed_by(self):
        return self._passed_by
    
    def global_synchro(self):
        self._p2p_service.wait_for_all()


def refine_status(sequence, port_status):
    curr_status = port_status[0]
    res = [(None, curr_status)]
    for i in range(len(sequence)):
        if port_status[i+1] != curr_status:
            res.append((sequence[i], port_status[i+1]))
            curr_status = port_status[i+1]
    return res
    
def make_messages(sequence, port_name, port_status, passed_by, component: Component):
    curr_passed_by = set_utils.copy(passed_by)
    curr_passed_by.add(component.get_name())
    result = set()
    port = find(lambda p: p[0] == port_name, component.get_ports())
    port_type = port[1]
    refined_port_status = refine_status(sequence, port_status)
    if port_type == DepType.PROVIDE:
        if port_status[-1] == "disabled":
            # at the end, the related use ports must be deactivated
            message = ConstraintMessage(component.get_name(), None, port_name, "disabled", None, curr_passed_by, final=True)
            result.add(message)
        for i in range(len(refined_port_status)-2):
            if refined_port_status[i][1] == "enabled" and refined_port_status[i+1][1] == "disabled" and refined_port_status[i+2][1] == "enabled":
                # at a moment, the provide port is deactivate by a behavior. It is activate then
                behavior = refined_port_status[i+1][0]
                message = ConstraintMessage(component.get_name(), None, port_name, "disabled", behavior, curr_passed_by)   
                result.add(message) 
    elif port_type == DepType.USE:
        if port_status[-1] == "enabled":
            # at the end, the related provide ports must be activated
            message = ConstraintMessage(component.get_name(), None, port_name, "enabled", None, curr_passed_by, final=True)
            result.add(message)
        for i in range(len(refined_port_status)-2):
            if refined_port_status[i][1] == "disabled" and refined_port_status[i+1][1] == "enabled" and refined_port_status[i+2][1] == "disabled":
                # at a moment, the use port is activate by a behavior. It is activate then
                behavior = refined_port_status[i+1][0]
                message = ConstraintMessage(component.get_name(), None, port_name, "enabled", behavior, curr_passed_by)
                result.add(message)          
    return result
  
def cr_init(cr_node : CostRegularNode): 
    models = {}
    for component in cr_node.components:
        states, beahviors, matrix, costs = matrix_from_concerto_component(component)
        init_state = cr_node.active[component]
        tmp_ports = reverse_dict(component.get_bindings())
        ports = {port_name : list(filter(lambda pl: pl in states, places)) for (port_name, places) in tmp_ports.items()}
        constraints = set(
            map(lambda goal: CostRegular.constraint_from_goal(goal, cause=f"goal({cr_node.id}_9_{cr_node.admin})", active=init_state, component=component), 
                cr_node.goals[component]))
        models[component.name] = CostRegular(states, beahviors, matrix, costs, init_state, ports, constraints)
    return MultiCostRegular(models, cr_node)


def is_caused_internally(reason: str):
    if string_utils.startswith(reason, "model") or string_utils.startswith(reason, "state"):
        return True
    elif string_utils.startswith(reason, "port") or string_utils.startswith(reason, "transition"):
        return not ("infer" in reason)
    else:
        return True

def split_reason(reason):
    reason_constraint,reason_message = None, None 
    if string_utils.startswith(reason, "port"):
        port_reason = reason[len("port")+1:-1]
        port_name, status, isFinal, isGoal_asInt, infered = port_reason.split(',')
        isFinal = True if isFinal == "True" or isFinal == "1" else False 
        isGoal = True if isGoal_asInt == "1" else False 
        msg_source, msg_target, msg_port, msg_status, msg_behavior, msg_isFinal = \
            infered.replace(")","").replace("infer(","").replace("goal(","").split('_9_')
        msg_isFinal = True if msg_isFinal == "True" or msg_isFinal == "1" else False 
        msg_behavior = None if msg_behavior == "None" else msg_behavior
        reason_message = ConstraintMessage(msg_source, msg_target, msg_port, msg_status, msg_behavior, [], msg_isFinal) # HERE also get the real message, with passed_by
        reason_constraint = PortConstraint(port_name, status, infered, isFinal, isGoal)
    elif string_utils.startswith(reason, "transition"):
        port_reason = reason[len("transition")+1:-1]
        transition, isGoal_asInt, infered = port_reason.split(',')
        isGoal = True if isGoal_asInt == "1" else False 
        msg_source, msg_target, msg_port, msg_status, msg_behavior, msg_isFinal = \
            infered.replace(")","").replace("infer(","").replace("goal(","").split('_9_')
        msg_isFinal = True if msg_isFinal == "True" or msg_isFinal == "1" else False 
        msg_behavior = None if msg_behavior == "None" else msg_behavior
        reason_message = ConstraintMessage(msg_source, msg_target, msg_port, msg_status, msg_behavior, [], msg_isFinal) # HERE also get the real message, with passed_by
        reason_constraint = TransitionConstraint(transition, infered, isGoal)
    return reason_constraint,reason_message


def make_reason_explicit(reason):
    #TODO 
    return reason

def cr_local(cr_model: MultiCostRegular, write_file=False, debug=False, time=0):
    if debug:
        write_file = True
    out_messages = set()
    node: CostRegularNode = cr_model.get_node()
    opt_ack = set()
    
    results = cr_model.solve(write_file=write_file)
    
    for (comp_name, result) in results.items():
        if result.is_sat:
            sequence = cr_model.get_sequence(comp_name)
            if debug:
                print(f"{comp_name}:", flush=True)
                print(f"Raw: {result}", flush=True)
                print("\tstates = ", cr_model.get_states(comp_name), flush=True)
                print("\tsequence = ", sequence, flush=True)
            for (port_name, _) in cr_model.get_port_statuses(comp_name).items():
                port_status = cr_model.get_port_status(comp_name, port_name)
                port_status_str = list(map(lambda v: "enabled" if v == 1 or v == "enabled" else "disabled", port_status))
                if debug:
                    print(f"\t{port_name}: {port_status_str}", flush=True)
                component = node.components_from_str(comp_name)
                msgs = make_messages(sequence, port_name, port_status, node.passed_by, component)
                out_messages = out_messages | msgs
            if debug:
                print("\n", flush=True)
        else:
            all_reasons = [s for s in result.result.split('\n') if s.strip()]
            # print(f"Model is unsat. Here are all reasons \n \t {all_reasons}")
            explainity = '/\\'.join(map(lambda reason: make_reason_explicit(reason), all_reasons))
            node.set_local_conflict(explainity)
            # TODO if exists internal reason, also print all reasons for local devops. Store it somewhere ?
            for reason in all_reasons:
                if not is_caused_internally(reason):
                    # print(f"Looking for the message to ack in {reason} since it is external")
                    message_to_ack = None
                    (_, reason_message) = split_reason(reason)
                    for (_, messages) in node.get_in_message().items():
                        for (message, _) in messages.items():
                            if message == reason_message:
                                message_to_ack = message
                    if message_to_ack != None:
                        fail_ack = AckFailure(comp_name, None, message_to_ack, explainity)
                        opt_ack.add(fail_ack)
    out_messages = cr_model.get_node().remove_deplicata(out_messages)
    return out_messages, list(opt_ack)



def cr_local_timed(cr_model: MultiCostRegular, write_file=True, debug=False, iteration=0):
    out_messages = set()
    node: CostRegularNode = cr_model.get_node()
    opt_ack = set()
    results = cr_model.solve_timed(write_file=write_file, step="flocal", iteration=iteration)
    
    for (comp_name, result) in results.items():
        if result.is_sat:
            sequence = cr_model.get_sequence(comp_name)
            for (port_name, _) in cr_model.get_port_statuses(comp_name).items():
                port_status = cr_model.get_port_status(comp_name, port_name)
                component = node.components_from_str(comp_name)
                msgs = make_messages(sequence, port_name, port_status, node.passed_by, component)
                out_messages = out_messages | msgs
        else:
            all_reasons = [s for s in result.result.split('\n') if s.strip()]
            explainity = '/\\'.join(map(lambda reason: make_reason_explicit(reason), all_reasons))
            node.set_local_conflict(explainity)
            for reason in all_reasons:
                if not is_caused_internally(reason):
                    message_to_ack = None
                    (_, reason_message) = split_reason(reason)
                    for (_, messages) in node.get_in_message().items():
                        for (message, _) in messages.items():
                            if message == reason_message:
                                message_to_ack = message
                    if message_to_ack != None:
                        fail_ack = AckFailure(comp_name, None, message_to_ack, explainity)
                        opt_ack.add(fail_ack)
    out_messages = cr_model.get_node().remove_deplicata(out_messages)
    return out_messages, list(opt_ack)


def check_to_be_diffused(node: CostRegularNode, msg: ConstraintMessage):
    # If source has no goal constraint, and no inferred constraint from remote message, do not create a message !
    # It means, it solves a model tat was not needed to be solved... 
    has_remote_constraint = len(node.get_in_message()[msg.source]) != 0
    has_reconf_goal = node.is_comp_root(msg.source)
    return has_remote_constraint or has_reconf_goal
    

def cr_msg(node: CostRegularNode, msgs: list[ConstraintMessage]): #-> dict[str, list[Message]]
    res = {}
    out_messages = set()
    for msg in msgs:
        # If source has no goal constraint, and no inferred constraint from remote message, do not create a message !
        # It means, it solves a model tat was not needed to be solved... 
        msg_to_be_diffused = check_to_be_diffused(node, msg)
        if msg_to_be_diffused:
            targets = node.use_by(msg.source, msg.port) + node.provide_by(msg.source, msg.port)
            for target in targets:
                if target not in res.keys():
                    res[target] = set()
                message = ConstraintMessage(msg.source, target, msg.port, msg.status, msg.behavior, msg.passed_by, msg.final)
                res[target].add(message)
                out_messages.add(message)
    node.add_consequence_of_constraints(node.get_lastest_constraints(), out_messages)        
    return {k: list(v) for (k,v) in res.items()}


def cr_enrich(model: MultiCostRegular, messages: list[ConstraintMessage]):
    new_constraints = set()
    def __get_places(component, port):
        tmp_ports = reverse_dict(component.get_bindings())
        tmp_places = tmp_ports[port]
        result = []
        model_states = model.get_model(component.name).states
        for place in tmp_places:
            if place in model_states:
                result.append(place)
        return result
    node: CostRegularNode = model.get_node()
    for message in messages:
        msg_source = f"infer({message.source}_9_{message.target}_9_{message.port}_9_{message.status}_9_{message.behavior}_9_{message.final})"
        connected_ports = node.use_by_port(message.source, message.port, message.target) + node.provide_by_port(message.source, message.port, message.target)
        for connected_port in connected_ports:
            port_constraint = PortConstraint(connected_port, message.status, source=msg_source, final=message.final, goal=False)
            node.add_origin_of_constraint(port_constraint, message)
            model.add_constraint(message.target, port_constraint)
            new_constraints.add(port_constraint)
        # TODO in a future version, manage such a case a multiport constraint
        # multiport_constraint = MultiPortConstraint(connected_ports, message.status, source=message.source, final=message.final, goal=False)
        # model.add_constraint(message.target, multiport_constraint)
        if (message.behavior != "" and message.behavior != None):
            transition_name = f"wait_{message.source}_{message.behavior}"
            validating_states = set()
            for connected_port in connected_ports:
                component = node.components_from_str(message.target)
                if message.status == "enabled":
                    validating_states = validating_states | set(__get_places(component, connected_port))
                elif message.status == "disabled":
                    invalid_states = set(__get_places(component, connected_port))
                    for place in component.get_places():
                        if place not in invalid_states and place in model.get_model(component.name).states:
                            validating_states.add(place)
            for state in validating_states:
                model.add_transition(message.target, transition_name, state, state)
            wait_constraint = TransitionConstraint(transition_name, source=msg_source)
            node.add_origin_of_constraint(wait_constraint, message)
            model.add_constraint(message.target, wait_constraint) # remove message
            new_constraints.add(wait_constraint)
    node.set_lastest_constraints(list(new_constraints))
    return model

def cr_final_timed(cr_model: MultiCostRegular, write_file=False, iteration=0):
    def __format_wait(inst: str):
        cw = inst.split('_')
        return Wait('_'.join(cw[1:-1]), cw[-1])
    def __format_push(compname, inst: str):
        return PushB(compname, inst)
    cr_model.solve_timed(write_file=write_file, step="ffinal", iteration=iteration)
    plans = map(lambda comp_name: 
        Plan(comp_name, 
             list(map(lambda inst: __format_wait(inst) if inst[0:4] == "wait" else __format_push(comp_name, inst), 
                      cr_model.get_sequence(comp_name)))
             ), cr_model.get_components())
    return merge_plans(list(plans))

def cr_final(cr_model: MultiCostRegular, write_file=False):
    def __format_wait(inst: str):
        cw = inst.split('_')
        return Wait('_'.join(cw[1:-1]), cw[-1])
    def __format_push(compname, inst: str):
        return PushB(compname, inst)
    cr_model.solve(write_file=write_file)
    plans = map(lambda comp_name: 
        Plan(comp_name, 
             list(map(lambda inst: __format_wait(inst) if inst[0:4] == "wait" else __format_push(comp_name, inst), 
                      cr_model.get_sequence(comp_name)))
             ), cr_model.get_components())
    return merge_plans(list(plans))


def cr_ack_with_ack(node: CostRegularNode, ack:Acknowledgement):
    node.new_received_ack()
    result: dict[Node, Acknowledgement] = {}
    if isinstance(ack, AckFailure):
        fail_acks = [ack]
    elif isinstance(ack, list) and len(ack)!=0 and isinstance(ack[0], AckFailure):
        fail_acks = ack
    for fail_ack in fail_acks:
        message = fail_ack.constraint
        fail_ack.set_target(message.source)
        if message.source not in result.keys():
            result[message.source] = set()
        result[message.source].add(fail_ack)
    return result

def cr_ack_default(node: CostRegularNode):
    node.new_received_ack()
    result: dict[Node, Acknowledgement] = {}
    for component in node.components:
        comp_name = component.name
        all_out_messages_of_comp = set(node.get_out_message()[comp_name].keys())
        all_in_messages_of_comp = set(node.get_in_message()[comp_name].keys())
        there_are_accept_acks_to_send = True
        for message in all_out_messages_of_comp:
            got_ack_message = node.get_ack_out_message(comp_name, message)
            if got_ack_message == None or got_ack_message.is_failure():
                there_are_accept_acks_to_send = False
                if got_ack_message != None and got_ack_message.is_failure():
                    # get the origin_constraint who caused this message
                    origin_constraint = node.get_origin_constraint_of_a_message(message)
                    if origin_constraint != None:
                        # We don't go into this condition if no message led to this out message, that is it is initiated from root
                        # get the origin_message, if exists, who caused this origin_constraint. 
                        origin_message: ConstraintMessage = node.get_origin_of_constraint(origin_constraint)
                        # send AckFail to this message 
                        new_cause = got_ack_message.cause + f"/\\ trans({origin_constraint},on::{comp_name}) "# TODO prefix this cause by what,local transitive information,  
                        to_send_ack = AckFailure(comp_name, origin_message.source, origin_message, new_cause)
                        if to_send_ack.target not in result.keys():
                            result[to_send_ack.target] = set()
                        result[to_send_ack.target].add(to_send_ack) 
                        for in_message in all_in_messages_of_comp: #todo send ackfail all unacked in_message
                            additional_ack = AckFailure(comp_name, in_message.source, in_message, new_cause)
                            if additional_ack.target not in result.keys():
                                result[additional_ack.target] = set()
                            result[additional_ack.target].add(additional_ack) 
        if there_are_accept_acks_to_send:                
            for message in all_in_messages_of_comp:
                if node.get_ack_in_message(comp_name, message) == None:
                    to_send_ack = AckSuccess(comp_name, message.source, message)
                    if message.source not in result.keys():
                        result[message.source] = set()
                    result[message.source].add(to_send_ack)
        """Cyclic constraints ack management:
        If comp_name is waiting acks from A, and comp_name has to validate constraints from A
        then validate all messages received by comp_name from A
        """
        # 1. Get all targets in node.get_out_message()[comp_name].keys()
        waiting_ack_from_out_message = set() 
        for message in node.get_out_message()[comp_name].keys():
            waiting_ack_from_out_message.add(message.target)
        # 2. If one of these target is in node.passed_by, then validate all messages received from a source in passed_by
        for target in waiting_ack_from_out_message:
            if target in node.passed_by:
                messages_to_ack = []
                for message in node.get_in_message()[comp_name].keys():
                    if message.source in node.passed_by and node.get_in_message()[comp_name][message] == None:
                        messages_to_ack.append(message)
                # 3. Validate all these messages
                for message in messages_to_ack:                
                    to_send_ack = AckSuccess(comp_name, message.source, message)
                    if message.source not in result.keys():
                        result[message.source] = set()
                    result[message.source].add(to_send_ack)
    return result
    
    

def cr_ack(node: CostRegularNode, ack: Optional[Acknowledgement]=None):
    """
    node: the node which will send acks 
    ack: if we preivously received a AckFailure, then we must send an ackfailure too..  
    """
    if (ack != None):
        return cr_ack_with_ack(node, ack)
    else:
        return cr_ack_default(node)