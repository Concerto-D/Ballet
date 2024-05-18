from ballet.assembly.simplified.assembly import ComponentInstance, Place
from ballet.planner.gossip.gossip import Node
from ballet.planner.gossip.cost_regular import CostRegular
from ballet.planner.goal import Goal
from ballet.planner.automata import matrix_from_component


# node: Node
# roots: list[Node],
# f_init: Callable[[Node], Model], 
# f_local: Callable[[Model], (list[Message], Optional[Acknowledgement])], 
# f_msg: Callable[[Node, list[Message]], dict[Node, list[Message]]],
# f_enrich: Callable[[Model, list[Message]], Model],
# f_ack: Callable[[Node, Acknowledgement], dict[Node, Acknowledgement]],
# f_final: Callable[[Model], Solution]

class ComponentNode(Node):
    
    def __init__(self, ci: ComponentInstance, active_place: Place, goals: set[Goal]):
        self._component = ci
        self._active = active_place
        self._goals = goals
        
    def constraints_from_goals(self):
        def __constraint_from_goal(goal: Goal):
            if goal.isBehaviorGoal():
                pass # TODO
            elif goal.isPlaceGoal():
                pass # TODO
            elif goal.isStateGoal():
                pass # TODO
            elif goal.isPortGoal:
                pass # TODO
        return set(map(lambda goal: __constraint_from_goal(goal), self._goals))

def cr_init(comp: ComponentNode):    
    places, behaviors, transitions, costs = matrix_from_component(comp._component)
    init_place = comp._active.name()
    ports = {port: list(map(lambda place: place.name, port.bound_places())) for port in comp._component.type().ports()}
    constraints = comp.constraints_from_goals()
    return CostRegular(places, behaviors, transitions, costs, init_place, ports, constraints)


# cr = CostRegular(["initiated","configured","deployed"], 
#                  ["deploy","stop","uninstall"], 
#                  {"initiated" : {"deploy":"deployed"},
#                   "configured": {"deploy":"deployed"},
#                   "deployed": {"stop":"configured", "uninstall":"initiated"}}, 
#                  {"initiated" : {"deploy":2},
#                   "configured": {"deploy":1},
#                   "deployed": {"stop":1, "uninstall":1}}, 
#                  "initiated",
#                  {"service":["deployed"], "facts_service":["configured", "deployed"]},
#                  {StateConstraint("deployed", final=True),
#                 #   PortConstraint("service", "enabled", final=True),
#                   PortConstraint("service", "disabled", final=True),
#                   TransitionConstraint("deploy")
#                   })
