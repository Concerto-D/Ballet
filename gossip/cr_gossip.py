from gossip.gossip import Node
from ballet.planner.automata import matrix_from_concerto_component
from gossip.cost_regular import CostRegular, MultiCostRegular, MultiPortConstraint, TransitionConstraint
from ballet.assembly.concertod.component import Component
from ballet.planner.goal import Goal
from ballet.utils.list_utils import find
from ballet.utils.dict_utils import reverse_dict
from ballet.assembly.concertod.dependency import DepType

import abc

# f_enrich: Callable[[Model, list[Message]], Model],
# f_ack: Callable[[Node, Acknowledgement], dict[Node, Acknowledgement]],
# f_final: Callable[[Model], Solution]


class ConstraintMessage:
    
    def __init__(self, source, target, port, status, behavior, final=False):
        self._source = source
        self._target = target
        self._port = port
        self._status = status
        self._behavior = behavior
        self._final = final

    @property
    def source(self):
        return self._source

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
    
    def __str__(self):
        return f"(from:{self._source}, to:{self._target}, port:{self._port}, status:{self._status}, "+ (f"bhv:{self._behavior}, " if self._behavior else "") + f"final:{self._final})"


class AckMessage (abc.ABC):
    
    def __init__(self):
        pass
    
    
class AckFailure (AckMessage):
    
    def __init__(self, source, target, constraint, cause):
        self._source = source
        self._target = target
        self._constraint = constraint
        self._cause = cause
    
    @property
    def source(self):
        return self._soource
    
    @property
    def target(self):
        return self._target
    
    @property
    def constraint(self):
        return self._constraint
    
    @property
    def cause(self):
        return self._cause
    
     
class AckSuccess (AckMessage):
    
    def __init__(self, source, target, constraint):
        self._source = source
        self._target = target
        self._constraint = constraint
        
    @property
    def source(self):
        return self._soource
    
    @property
    def target(self):
        return self._target
    
    @property
    def constraint(self):
        return self._constraint
    

class GlobalAck(abc.ABC):
    
    def __init__(self):
        pass
    

class GlobalAckSuccess(GlobalAck):
    
    def __init__(self, source):
        self._source = source
    
    @property
    def source(self):
        return self._source
    
    
class GlobalAckFailure(GlobalAck):
    
    def __init__(self, source):
        self._source = source
    
    @property
    def source(self):
        return self._source


class CostRegularNode:
    
    def __init__(self, id: str, admin: str, connections: list[(str, str, str, str)], components: list[Component], active: dict[Component, str], goals: dict[Component, list[Goal]]):
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


def refine_status(sequence, port_status):
    curr_status = port_status[0]
    res = [(None, curr_status)]
    for i in range(len(sequence)):
        if port_status[i+1] != curr_status:
            res.append((sequence[i], port_status[i+1]))
            curr_status = port_status[i+1]
    return res
    
def make_messages(sequence, port_name, port_status, component: Component):
    result = set()
    port = find(lambda p: p[0] == port_name, component.get_ports())
    port_type = port[1]
    refined_port_status = refine_status(sequence, port_status)
    # ConstraintMessage(source, target, port, status, behavior, final)
    if port_type == DepType.PROVIDE:
        if port_status[-1] == "disabled":
            # at the end, the related use ports must be deactivated
            result.add(ConstraintMessage(component.get_name(), None, port_name, "disabled", None, final=True))
        for i in range(len(refined_port_status)-2):
            if refined_port_status[i][1] == "enabled" and refined_port_status[i+1][1] == "disabled" and refined_port_status[i+2][1] == "enabled":
                # at a moment, the provide port is deactivate by a behavior. It is activate then
                behavior = refined_port_status[i+1][0]
                result.add(ConstraintMessage(component.get_name(), None, port_name, "disabled", behavior, final=True))       
    elif port_type == DepType.USE:
        if port_status[-1] == "enabled":
            # at the end, the related provide ports must be activated
            result.add(ConstraintMessage(component.get_name(), None, port_name, "enabled", None, final=True))
        for i in range(len(refined_port_status)-2):
            if refined_port_status[i][1] == "disabled" and refined_port_status[i+1][1] == "enabled" and refined_port_status[i+2][1] == "disabled":
                # at a moment, the use port is activate by a behavior. It is activate then
                behavior = refined_port_status[i+1][0]
                result.add(ConstraintMessage(component.get_name(), None, port_name, "enabled", behavior, final=True))          
    return result
  
def cr_init(cr_node : CostRegularNode): 
    models = {}
    for component in cr_node.components:
        states, beahviors, matrix, costs = matrix_from_concerto_component(component)
        init_state = cr_node.active[component]
        tmp_ports = reverse_dict(component.get_bindings())
        ports = {port_name : list(filter(lambda pl: pl in states, places)) for (port_name, places) in tmp_ports.items()}
        constraints = set(
            map(lambda goal: CostRegular.constraint_from_goal(goal, cause=f"goal submitted by {cr_node.admin}", active=init_state, component=component), 
                cr_node.goals[component]))
        models[component.name] = CostRegular(states, beahviors, matrix, costs, init_state, ports, constraints)
    return MultiCostRegular(models, cr_node)


def cr_local(cr_model: MultiCostRegular):
    out_messages = set()
    opt_ack = None
    results = cr_model.solve()
    for (comp_name, result) in results.items():
        if result.is_sat:
            sequence = cr_model.get_sequence(comp_name)
            print(f"{comp_name}:")
            print("\tstates = ", cr_model.get_states(comp_name))
            print("\tsequence = ", sequence)
            for (port, _) in cr_model.get_port_statuses(comp_name).items():
                print(f"\t{port}: {cr_model.get_port_status(comp_name, port)}")
                node = cr_model.get_node()
                component = node.components_from_str(comp_name)
                port_name = port
                port_status = cr_model.get_port_status(comp_name, port)
                msgs = make_messages(sequence, port_name, port_status, component)
                out_messages = out_messages | msgs
            print("\n")
        else:
            constraint = None # TODO find what constraints that are not goals makes it unsat, and list them.
            opt_ack = AckFailure(comp_name, target=None, constraint=constraint, cause=result.result)
            print(f"Plan for {comp_name} is unsat:")
            print(f"{result.result}")

    return out_messages, opt_ack


def cr_msg(node: CostRegularNode, msgs: list[ConstraintMessage]): #-> dict[str, list[Message]]
    res = {}
    for msg in msgs:
        targets = node.use_by(msg.source, msg.port) + node.provide_by(msg.source, msg.port)
        for target in targets:
            if target not in res.keys():
                res[target] = set()
            res[target].add(ConstraintMessage(msg.source, target, msg.port, msg.status, msg.behavior, msg.final))
    return {k: list(v) for (k,v) in res.items()}


def cr_enrich(model: MultiCostRegular, messages: list[ConstraintMessage]):
    def __get_places(component, port):
        tmp_ports = reverse_dict(component.get_bindings())
        return tmp_ports[port]
    node: CostRegularNode = model.get_node()
    for message in messages:
        connected_ports = node.use_by_port(message.source, message.port, message.target) + node.provide_by(message.source, message.port, message.target)
        multiport_constraint = MultiPortConstraint(connected_ports, message.status, source=message.source, final=message.final, goal=False)
        model.add_constraint(message.target, multiport_constraint)
        if (message.behavior != "" and message.behavior != None):
            transition_name = f"wait_{message.source}_{message.behavior}"
            validating_states = set()
            for connected_port in connected_ports:
                component = node.components_from_str(message.target)
                if message.status == "enabled":
                    validating_states = validating_states | __get_places(component, connected_port)
                elif message.status == "disabled":
                    invalid_states = __get_places(component, connected_port)
                    for place in component.get_places():
                        if place not in invalid_states:
                            validating_states.add(place)
            for state in validating_states:
                model.add_transition(message.target, state, state, transition_name)
            wait_constraint = TransitionConstraint(transition_name, source=message.source)
            model.add_constraint(message.target, wait_constraint)
    return model