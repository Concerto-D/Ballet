from gossip.cr_gossip import *

import gossip_pb2_grpc
import gossip_pb2
import grpc
import threading
import time
from concurrent import futures

import threading
    
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
        message = ConstraintMessage(request.component_source, target, request.port, 
                                    request.status, request.behavior, request.final)
        with self._lock_new_mailbox:
            if target not in self._mailbox.keys():
                self._mailbox[target] = set()
        with self._lock_add_message:
            self._mailbox.add(message)
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
        ack = AckSuccess(request.component_source, request.component_target, request.to_message)
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

    def add_ack_failure(self, request, context):
        target = request.component_target
        ack = AckFailure(request.component_source, request.component_target, request.to_message, request.cause)
        with self._lock_new_acks:
            if target not in self._acks.keys():
                self._acks[target] = set()
        with self._lock_add_ack:
            self._acks[target].add(ack)
        return gossip_pb2.Empty()


    def add_global_ack_sucess(self, request, context):
        source = request.component_source
        ack = GlobalAckSuccess(source)
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
        self.__wait_for_all()
        
    def stop(self):
        self._server.stop()
    
    def __ping(self, address):
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.MessagingStub(channel)
            msg = gossip_pb2.Empty()
            stub.ping(msg)

    def get_messages(self, component):
        return self._servicer.get_messages(component)
    
    def get_acks(self, component):
        return self._servicer.get_acks(component)
    
    def get_global_acks(self, component):
        return self._servicer.get_global_acks(component)

    def __wait_for_all(self):
        to_ping = set()
        for comp in self.__inventory.keys():
            comp_host = self.__inventory[comp]["address"]
            comp_port = self.__inventory[comp]["port_planner"]
            full_address = comp_host + ":" + str(comp_port)
            self._full_address[comp] = full_address
            to_ping.add(full_address)
        while len(to_ping) != 0:
            for address in to_ping:
                try:
                    self.__ping(address)
                    to_ping.remove(address)
                except:
                    pass
            time.sleep(1)
            
            
class CRClient:
    
    def __init__(self, inventory: dict[str, dict[str, str]]):
        self.__inventory = inventory
    
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
            to_send = gossip_pb2.SyncSpec(component_source=message.source, component_target=message.target, 
                                          port=message.port, status=message.status, behavior=message.behavior,
                                          final=message.final)
            stub.add_message(to_send)
    
    def __send_ack_success(self, ack: AckSuccess):
        address = self.__get_address(ack.target)
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            acked_message = gossip_pb2.SyncSpec(ack.constraint.source, ack.constraint.target, ack.constraint.port, 
                                                ack.constraint.status, ack.constraint.behavior, ack.constraint.final)
            to_send = gossip_pb2.AckSuccess(component_source = ack.source, component_target = ack.target, 
                                            to_message = acked_message)
            stub.add_global_ack_sucess(to_send)
            
    def __send_ack_failure(self, ack: AckFailure):
        address = self.__get_address(ack.target)
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            to_send = gossip_pb2.AckFailure(component_source = ack.source, component_target = ack.target, 
                                            to_message = ack.constraint, cause = ack.cause)
            stub.add_global_ack_failure(to_send)
    
    def send_ack(self, ack: AckMessage):
        if isinstance(ack, AckSuccess):
            self.__send_ack_success(ack)
        elif isinstance(ack, AckFailure):
            self.__send_ack_failure(ack)
            
    def __send_global_ack_success(self, address, ack: GlobalAckSuccess):
        with grpc.insecure_channel(address) as channel:
            stub = gossip_pb2_grpc.CostRegularGossipServiceStub(channel)
            to_send = gossip_pb2.GlobalAckSuccess(component_source=ack.source)
            stub.add_global_ack_sucess(to_send)      
    
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
        
    def send_global_ack(self, ack: GlobalAck):
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
        self._server.get_messages(component)
    
    def get_acks(self, component):
        self._server.get_acks(component)
    
    def get_global_acks(self, component):
        self._server.get_global_acks(component)
    
    