from ballet.assembly.assembly import ComponentInstance, ComponentType, Port, CInstance, IAssembly
from typing import Dict, Iterable, Tuple, Set, Union


class DecentralizedComponentInstance (CInstance):

    def __init__(self, identifier: str, t: ComponentType):
        self._id: str = identifier
        self._type: ComponentType = t
        self._connections_use_port: Dict[Port, Set[Tuple[str, str]]]  = {p: set() for p in self._type.use_ports()}
        self._connections_provide_port: Dict[Port, Set[Tuple[str, str]]]  = {p: set() for p in self._type.provide_ports()}
        self._external_port_connections: Dict[(str, str), Port] = {}

    def id(self) -> str:
        return self._id

    def type(self) -> ComponentType:
        return self._type

    def connections(self, p: Port) -> Iterable[Tuple[str, str]]:
        if p.is_use_port():
            assert p in self._connections_use_port
            return self._connections_use_port[p]
        else:
            assert p in self._connections_provide_port
            return self._connections_provide_port[p]

    def is_connected(self, p: str) -> bool:
        assert p in self._type.ports()
        return len(self._connections_provide_port[p]) + len(self._connections_use_port[p]) > 0

    def connect_provide_port(self, provide_port: Union[Port, str], user: Union[CInstance, str], use_port: Union[Port, str]):
        port = provide_port if type(provide_port) == Port else self.type().get_port(provide_port)
        assert port in self._type.provide_ports()
        username = user if type(user) == str else user.id()
        portname = use_port if type(use_port) == str else use_port.name()
        self._connections_provide_port[port].add((username, portname))
        self._external_port_connections[(username, portname)] = port

    def connect_use_port(self, use_port: Union[Port, str], provider: Union[CInstance, str], provide_port: Union[Port, str]):
        port = use_port if type(use_port) == Port else self.type().get_port(use_port)
        assert port in self._type.use_ports()
        # a use port should only be connected to one provider
        assert not self._connections_use_port[port]
        providername = provider if type(provider) == str else provider.id()
        portname = provide_port if type(provide_port) == str else provide_port.name()
        self._connections_use_port[port].add((providername, portname))
        self._external_port_connections[(providername, portname)] = port

    def isDecentralized(self) -> bool:
        return True

    def neighbors(self) -> Set[str]:
        res = set()
        for connections in self._connections_use_port.values():
            res = res | set(map(lambda t: t[0], connections))
        for connections in self._connections_provide_port.values():
            res = res | set(map(lambda t: t[0], connections))
        return res

    def external_port_connection(self, comp: Union[CInstance, str], port: Union[Port, str]) -> str:
        ext_portname = port.name() if isinstance(port, Port) else port
        ext_compname = comp.id() if isinstance(comp, CInstance) else comp
        if (ext_compname, ext_portname) in self._external_port_connections.keys():
            return self._external_port_connections[(ext_compname, ext_portname)].name()
        else:
            print(f"{self.id()} has no port connected to {(ext_compname, ext_portname)}")
            return None

    def __eq__(self, other):
        if not isinstance(other, DecentralizedComponentInstance):
            return False
        else:
            return self.id() == other.id() and self.type() == other.type()

    def __hash__(self):
        return hash(self._id) + hash(self._type)


class DecentralizedAssembly(IAssembly):

    def __init__(self):
        self._instances: Dict[str, DecentralizedComponentInstance] = {}

    def add_instance(self, instance_id: str, t: ComponentType) -> ComponentInstance:
        assert instance_id not in self._instances
        c = DecentralizedComponentInstance(instance_id, t)
        self._instances[instance_id] = c
        return c

    def connect_instances(self,
                          provider: DecentralizedComponentInstance,
                          provide_port: Port,
                          user: DecentralizedComponentInstance,
                          use_port: Port) -> None:
        assert provider in self._instances.values()
        assert provide_port.is_provide_port()
        assert user in self._instances.values()
        assert use_port.is_use_port()
        provider.connect_provide_port(provide_port, user.id(), use_port.name())
        user.connect_use_port(use_port, provider.id(), provide_port.name())

    def connect_instances_id(self,
                             provider_id: str,
                             provide_port_name: str,
                             user_id: str,
                             use_port_name: str) -> None:
        provider = self.get_instance(provider_id)
        user = self.get_instance(user_id)
        provide_port = provider.type().get_provide_port(provide_port_name)
        use_port = user.type().get_use_port(use_port_name)
        self.connect_instances(provider, provide_port, user, use_port)

    def get_instance(self, identifier: str) -> DecentralizedComponentInstance:
        assert identifier in self._instances
        return self._instances[identifier]

    def instances(self) -> Iterable[DecentralizedComponentInstance]:
        return self._instances.values()