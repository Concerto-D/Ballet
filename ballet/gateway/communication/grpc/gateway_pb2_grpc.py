# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import ballet.gateway.communication.grpc.gateway_pb2 as gateway__pb2


class MessagingStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ping = channel.unary_unary(
                '/Messaging/ping',
                request_serializer=gateway__pb2.Empty.SerializeToString,
                response_deserializer=gateway__pb2.Pong.FromString,
                )
        self.addPortGoals = channel.stream_unary(
                '/Messaging/addPortGoals',
                request_serializer=gateway__pb2.PortGoal.SerializeToString,
                response_deserializer=gateway__pb2.Empty.FromString,
                )
        self.addBehaviorGoals = channel.stream_unary(
                '/Messaging/addBehaviorGoals',
                request_serializer=gateway__pb2.BehaviorGoal.SerializeToString,
                response_deserializer=gateway__pb2.Empty.FromString,
                )
        self.validate = channel.unary_unary(
                '/Messaging/validate',
                request_serializer=gateway__pb2.Done.SerializeToString,
                response_deserializer=gateway__pb2.Empty.FromString,
                )


class MessagingServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ping(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def addPortGoals(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def addBehaviorGoals(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def validate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_MessagingServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ping': grpc.unary_unary_rpc_method_handler(
                    servicer.ping,
                    request_deserializer=gateway__pb2.Empty.FromString,
                    response_serializer=gateway__pb2.Pong.SerializeToString,
            ),
            'addPortGoals': grpc.stream_unary_rpc_method_handler(
                    servicer.addPortGoals,
                    request_deserializer=gateway__pb2.PortGoal.FromString,
                    response_serializer=gateway__pb2.Empty.SerializeToString,
            ),
            'addBehaviorGoals': grpc.stream_unary_rpc_method_handler(
                    servicer.addBehaviorGoals,
                    request_deserializer=gateway__pb2.BehaviorGoal.FromString,
                    response_serializer=gateway__pb2.Empty.SerializeToString,
            ),
            'validate': grpc.unary_unary_rpc_method_handler(
                    servicer.validate,
                    request_deserializer=gateway__pb2.Done.FromString,
                    response_serializer=gateway__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Messaging', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Messaging(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ping(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Messaging/ping',
            gateway__pb2.Empty.SerializeToString,
            gateway__pb2.Pong.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def addPortGoals(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(request_iterator, target, '/Messaging/addPortGoals',
            gateway__pb2.PortGoal.SerializeToString,
            gateway__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def addBehaviorGoals(request_iterator,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.stream_unary(request_iterator, target, '/Messaging/addBehaviorGoals',
            gateway__pb2.BehaviorGoal.SerializeToString,
            gateway__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def validate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Messaging/validate',
            gateway__pb2.Done.SerializeToString,
            gateway__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)