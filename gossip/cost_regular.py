from minizinc import Instance, Model as mznModel, Solver, Status
from ballet.utils.list_utils import flatmap, indexify, indexOf
from gossip.gossip import Model, Solution
from ballet.planner.goal import *
from ballet.assembly.concertod.component import Component
import subprocess, re, json

class FindMUSException(Exception):
    
    def __init__(self, message):            
        super().__init__(message)
        
        
class CRSolution(Solution):
    
    def __init__(self, result, sat=True):
        self.__result = result
        self.__is_sat = sat
    
    @property    
    def is_sat(self):
        return self.__is_sat
    
    @property
    def result(self):
        return self.__result
    
    def get(self, key):
        return getattr(self.__result, key)
            

class CRConstraint:
    
    def __init__(self, goal=False):
        self.__goal = goal
    
    def isGoal(self):
        return self.__goal
    
    def isStateConstraint(self):
        return False
    
    def isTransitionConstraint(self):
        return False
    
    def isPortConstraint(self):
        return False


class StateConstraint(CRConstraint):
    
    def __init__(self, state, source="NO SOURCE IS SPECIFIED", final=False, goal=False):
        super().__init__(goal)
        self.__state = state
        self.__final = final
        self.__source = source
        
    def isStateConstraint(self):
        return True
        
    @property
    def final(self):
        return self.__final
        
    @property
    def state(self):
        return self.__state
        
    @property
    def source(self):
        return self.__source
        
        
class PortConstraint(CRConstraint):
    
    def __init__(self, port, status, source="NO SOURCE IS SPECIFIED", final=False, goal=False):
        super().__init__(goal)
        assert status == "enabled" or status == "disabled"
        self.__port = port
        self.__status = status
        self.__final = final
        self.__source = source
        
    def isPortConstraint(self):
        return True
    
    @property
    def port(self):
        return self.__port
    
    @property
    def status(self):
        return self.__status
    
    @property
    def final(self):
        return self.__final
        
    @property
    def source(self):
        return self.__source
    

class TransitionConstraint(CRConstraint):
    
    def __init__(self, transition, source="NO SOURCE IS SPECIFIED", goal=False):
        super().__init__(goal)
        self.__transition = transition
        self.__source = source
    
    def isTransitionConstraint(self):
        return True
        
    @property
    def transition(self):
        return self.__transition
        
    @property
    def source(self):
        return self.__source

 
class CostRegular(Model):
    
    def __init__(self, states: list[str], transitions: list[str], 
                 automata: dict[str,dict[str,str]], costs: dict[str,dict[str,int]], init_state: str, 
                 ports: dict[str,list[str]], constraints: set[CRConstraint]):
        CostRegular.__assert_conform_automata(states, transitions, automata)
        CostRegular.__assert_conform_costs(states, transitions, costs, automata)
        CostRegular.__assert_conform_ports(states, ports)
        CostRegular.__assert_conform_constraints(states, transitions, ports, constraints)
        assert init_state in states
        self.__states = states
        self.__transitions = transitions
        added_skip = False
        if "skip" not in self.__transitions:
            added_skip = True
            self.__transitions.append("skip")
        self.__automata = automata
        self.__init_state = init_state
        if added_skip:
            for state in self.__states:
                self.__automata[state]["skip"] = state
        self.__costs = costs
        if added_skip:
            for state in self.__states:
                self.__costs[state]["skip"] = 0
        self.__constraints = constraints
        self.__ports = ports
        self.__seq_length = len(states) * len(transitions)
        
    def __assert_conform_automata(states: list[str], transitions: list[str], automata: dict[str,dict[str,str]]):
        for source in automata.keys():
            assert source in states # assert source is declared
            for label in automata[source].keys():
                assert label in transitions # assert the label of transition is declared
                assert automata[source][label] in states or automata[source][label] == "<>" # assert target is declared, or the transition does not exist
        
    def __assert_conform_costs(states: list[str], transitions: list[str], costs: dict[str,dict[str,int]], automata:dict[str,dict[str,str]]):
        for source in costs.keys():
            assert source in states # assert source is declared
            for label in costs[source].keys():
                assert label in transitions # assert the label of transition is declared
                assert automata[source][label] # assert the transition exists in the automata
        
    def __assert_conform_ports(states: list[str], ports:dict[str,list[str]]):
        for (_, places) in ports.items():
            for place in places:
                assert place in states
                
    def __assert_conform_constraints(states: list[str],  transitions: list[str], ports:dict[str,list[str]], constraints: set[CRConstraint]):
        for constraint in constraints:
            if constraint.isPortConstraint():
                assert constraint.port in ports.keys()
            if constraint.isTransitionConstraint():
                assert constraint.transition in transitions
            if constraint.isStateConstraint():
                assert constraint.state in states
    
    @staticmethod
    def constraint_from_goal(goal: Goal, cause="goal", component:Component=None, active=None):
        if goal.isBehaviorGoal():
            return TransitionConstraint(transition = goal.behavior(), source=cause, goal=True)
        elif goal.isPlaceGoal():
            return StateConstraint(state=goal.place(), source=cause, final=goal.final(), goal=True)
        elif goal.isPortGoal():
            return PortConstraint(port=goal.port(), status="enabled" if goal.isEnable() else "disabled", source=cause, final=goal.final(), goal=True) # TODO status ????
        elif goal.isStateGoal():
            if goal.state() == "deployed" or goal.state() == "running":
                to_reach = component.get_places[-1] # TODO add this concept to Component definition
            elif goal.state() == "destroyed":
                to_reach = component.get_places[0] # TODO add this concept to Component definition
            else:
                to_reach = active
            return StateConstraint(state=to_reach, source=cause, final=goal.final(), goal=True)    
    
    @property
    def states(self):
        return self.__states
    
    @property
    def init_state(self):
        return self.__init_state
        
    @property
    def transitions(self):
        return self.__transitions
        
    @property
    def automata(self):
        return self.__automata
        
    @property
    def costs(self):
        return self.__costs
      
    @property
    def constraints(self):
        return self.__constraints
      
    @property
    def add_constraints(self, constraint):
        self.__constraints.add(constraint)
      
    @property
    def add_transition(self, label, source, target, cost):
        if label not in self.__transitions:
            self.__transitions.append(label)
        self.__automata[source][label] = target
        self.__costs[source][label][target] = cost
        self.__seq_length = len(self.__states) * len(self.__transitions)
        
    @property
    def ports(self):
        return self.__ports
        
    @property
    def port_names(self):
        return list(self.__ports.keys())
        
    def __make_mzn_transitions_line(self, state):
        targets = []
        for transition in self.__transitions:
            if state in self.__automata.keys() and transition in self.__automata[state].keys(): # the transition exists
                targets.append(self.__automata[state][transition])
            else:
                targets.append("<>")
        return '|' + ','.join(targets)
        
    def __make_choco_transitions_line(self, state):
        targets = []
        for transition in self.__transitions:
            if state in self.__automata.keys() and transition in self.__automata[state].keys(): # the transition exists
                targets.append(self.__automata[state][transition])
            else:
                targets.append("any")
        return '{' + ','.join(targets) + '}'

    def __make_mzn_transitions_matrix(self):
        lines = map(lambda state: self.__make_mzn_transitions_line(state), self.__states)
        ll = '\n'.join(lines)
        return '\n'.join(f"""
[{ll}|]""".split('\n')[1:])
        
    def __make_choco_transitions_matrix(self):
        lines = map(lambda state: self.__make_choco_transitions_line(state), self.__states)
        ll = '\n'.join(map(lambda l: f"\t\t{l}",lines))
        return ',\n'.join(f"""
{ll}""".split('\n')[1:])
        
    def __make_mzn_costs_line(self, state):
        targets = []
        for transition in self.__transitions:
            if state in self.__costs.keys() and transition in self.__costs[state].keys(): # the transition has a cost
                targets.append(str(self.__costs[state][transition]))
            else:
                targets.append(str(1000000))
        return "|" + ','.join(targets)  

        
    def __make_choco_costs_line(self, state):
        targets = []
        for transition in self.__transitions:
            if state in self.__costs.keys() and transition in self.__costs[state].keys(): # the transition has a cost
                targets.append(str(self.__costs[state][transition]))
            else:
                targets.append(str(1000000))
        return "{" + ','.join(targets) + "}" 

    def __make_mzn_costs_matrix(self):
        lines = map(lambda state: self.__make_mzn_costs_line(state), self.__states)
        ll = '\n'.join(lines)
        return '\n'.join(f"""
[{ll}|]""".split('\n')[1:])

    def __make_choco_costs_matrix(self):        
        lines = map(lambda state: self.__make_choco_costs_line(state), self.__states)
        ll = ',\n'.join(map(lambda l: f"\t\t{l}",lines))
        return '\n'.join(f"""
{ll}""".split('\n')[1:])
        
        
    def __make_mzn_port_line(self, port, places):
        decl = f"array[1..seq_length+1] of var STATUS : {port}_status;"
        disjunction = ' \/ '.join(map(lambda place: f"states[i] = {place}", places))
        constr = f"constraint forall (i in 1..seq_length+1) ({port}_status[i] = enabled <-> {disjunction});"
        return [decl, constr]
        
    def __make_choco_port_line(self, port, places):
        decl = f"\t\tIntVar[] {port}_status = model.intVarArray(\"{port}_status\", seq_length + 1, 0, 1);"
        forloop = "\t\tfor(int i = 0; i < seq_length + 1; i++) {"
        bool_b0 = f"\t\t\tBoolVar b0 = model.arithm({port}_status[i], \"=\", enabled).reify();"
        res = [decl, forloop, bool_b0]
        bool_var_names = []
        for place in places:
            bool_var_name = f"b_{port}_{place}"
            bool_var_names.append(bool_var_name)
            res.append(f"\t\t\tBoolVar {bool_var_name} = model.arithm(states[i], \"=\", {place}).reify();")
        bool_clause = f"\t\t\tmodel.addClausesBoolOrArrayEqVar(new BoolVar[]{{{','.join(bool_var_names)}}}, b0);"
        endfor = "\t\t}"
        return res + [bool_clause, endfor]
    
    def __make_mzn_ports_status_constraints(self):
        lines = flatmap(lambda port: self.__make_mzn_port_line(port, self.__ports[port]), self.__ports.keys())
        return '\n'.join(lines)
    
    def __make_choco_ports_status_constraints(self):
        lines = flatmap(lambda port: self.__make_choco_port_line(port, self.__ports[port]), self.__ports.keys())
        return '\n'.join(lines)
    
    def __make_mzn_port_constraint_line(self, constraint: PortConstraint):
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        if constraint.final:
            res.append(f"constraint {constraint.port}_status[seq_length+1] = {constraint.status}; {suffix}")
        res.append(f"var int: count_{constraint.port}_status_{constraint.status}; {suffix}")
        res.append(f"constraint count_{constraint.port}_status_{constraint.status} = sum(s in {constraint.port}_status) (s = {constraint.status}); {suffix}")
        res.append(f"constraint count_{constraint.port}_status_{constraint.status} > 0; {suffix}")
        return res
    
    def __make_mzn_transition_constraint_line(self, constraint: TransitionConstraint):
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        decl1 = f"var int: count_{constraint.transition}; {suffix}"
        decl2 = f"constraint count_{constraint.transition} = sum(b in sequence) (b = {constraint.transition}); {suffix}"
        cstr = f"constraint count_{constraint.transition} > 0; {suffix}"
        return [decl1, decl2, cstr]
    
    def __make_mzn_state_constraint_line(self, constraint: StateConstraint):
        suffix = "% goal" if constraint.isGoal() else "% inferred"
        res = []
        if constraint.final:
            res.append(f"constraint states[seq_length+1] = {constraint.state}; {suffix}") 
        res.append(f"var int: count_{constraint.state}; {suffix}")
        res.append(f"constraint count_{constraint.state} = sum(s in states) (s = {constraint.state}); {suffix}")
        res.append(f"constraint count_{constraint.state} > 0; {suffix}")
        return res
    
    def __make_choco_port_constraint_line(self, constraint: PortConstraint):
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        res = []
        if constraint.final:
            res.append(f"\t\tmodel.arithm({constraint.port}_status[seq_length], \"=\", {constraint.status}).post(); {suffix}")
        res.append(f"\t\tIntVar count_{constraint.port}_{constraint.status} = model.intVar(\"count_{constraint.port}_{constraint.status}\", 0, seq_length); {suffix}")
        res.append(f"\t\tmodel.sum(Arrays.stream({constraint.port}_status).map(s -> s.eq({constraint.status}).boolVar()).toArray(BoolVar[]::new), \"=\", count_{constraint.port}_{constraint.status}).post(); {suffix}")
        res.append(f"\t\tmodel.arithm(count_{constraint.port}_{constraint.status}, \">\", 0).post(); {suffix}")
        
        
        res.append("\n")
        return res
    
    def __make_choco_transition_constraint_line(self, constraint: TransitionConstraint):
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        decl = f"\t\tIntVar count_{constraint.transition} = model.intVar(\"count_{constraint.transition}\", 0, seq_length); {suffix}"
        model_sum = f"\t\tmodel.sum(Arrays.stream(sequence).map(s -> s.eq({constraint.transition}).boolVar()).toArray(BoolVar[]::new), \"=\", count_{constraint.transition}).post(); {suffix}"
        model_arith = f"\t\tmodel.arithm(count_{constraint.transition}, \">\", 0).post(); {suffix}"         
        return [decl, model_sum, model_arith,"\n"]
    
    def __make_choco_state_constraint_line(self, constraint: StateConstraint):
        suffix = "// goal" if constraint.isGoal() else "// inferred"
        res = []
        if constraint.final:
            res.append(f"\t\tmodel.arithm(states[seq_length], \"=\", {constraint.state}).post(); {suffix}") 
        res.append(f"\t\tIntVar count_{constraint.state} = model.intVar(\"count_{constraint.state}\", 0, seq_length); {suffix}")
        res.append(f"\t\tmodel.sum(Arrays.stream(states).map(s -> s.eq({constraint.state}).boolVar()).toArray(BoolVar[]::new), \"=\", count_{constraint.state}).post(); {suffix}")
        res.append(f"\t\tmodel.arithm(count_{constraint.state}, \">\", 0).post(); {suffix}")
        res.append("\n")
        return res
    
    def __make_mzn_constraint_line(self, constraint):
        if constraint.isPortConstraint():
            return self.__make_mzn_port_constraint_line(constraint)
        if constraint.isStateConstraint():
            return self.__make_mzn_state_constraint_line(constraint)
        if constraint.isTransitionConstraint():
            return self.__make_mzn_transition_constraint_line(constraint)
    
    def __make_choco_constraint_line(self, constraint):
        if constraint.isPortConstraint():
            return self.__make_choco_port_constraint_line(constraint)
        if constraint.isStateConstraint():
            return self.__make_choco_state_constraint_line(constraint)
        if constraint.isTransitionConstraint():
            return self.__make_choco_transition_constraint_line(constraint)
    
    def __make_mzn_goal_constraints(self):
        lines = flatmap(lambda constraint: self.__make_mzn_constraint_line(constraint), self.__constraints)
        return '\n'.join(lines)
    
    def __make_choco_goal_constraints(self):
        lines = flatmap(lambda constraint: self.__make_choco_constraint_line(constraint), self.__constraints)
        return '\n'.join(lines)
    
    def make_json_model(self, print_model=True, write_file=True, filepath="model.json"):
        bool2int = lambda b: 1 if b else 0
        # State constraints format
        state_constraints = filter(lambda c: c.isStateConstraint() , self.constraints)
        json_state_constraints = list(map(lambda constraint: {"state": constraint.state, "isFinal": bool2int(constraint.final), "goal": bool2int(constraint.isGoal()), "source": constraint.source}, state_constraints))    
        # Port constraints format
        port_constraints = filter(lambda c: c.isPortConstraint() , self.constraints)
        json_port_constraints = list(map(lambda constraint: {"port": constraint.port, "status": constraint.status,"isFinal": bool2int(constraint.final), "goal": bool2int(constraint.isGoal()), "source": constraint.source}, port_constraints))    
        
        # Transition constraints format
        transition_constraints = filter(lambda c: c.isTransitionConstraint() , self.constraints)
        json_transition_constraints = list(map(lambda constraint: {"transition": constraint.transition, "goal": bool2int(constraint.isGoal()), "source": constraint.source}, transition_constraints))  
        
        content = {
            "states": self.states,
            "transitions": self.transitions,
            "automata": self.automata,
            "costs": self.costs,
            "init_state": self.init_state,
            "ports": self.ports,
            "constraints":
                {
                    "state_constraint": json_state_constraints,
                    "port_constraint": json_port_constraints,
                    "transition_constraint": json_transition_constraints
                }
        }
        json_content = json.dumps(content)
        if print_model:
            print(json_content)
        if write_file:
            with open(filepath, 'w') as f:
                json.dump(content, f)

    
    def __make_choco_model(self, classname="TestModel"):
        int_states = '\n'.join(map(lambda p: "        int " + str(p[0]) +" = "+ str(p[1])+" ;" , indexify(self.states)))
        int_behaviors = '\n'.join(map(lambda p: "        int " + str(p[0]) +" = "+ str(p[1])+" ;" , indexify(self.transitions)))
        content = f"""
package gossip;        

import java.util.Arrays;
import java.util.List;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;

public class {classname} {{
    
    public static void main(String[] args) {{

        Model model = new Model();
        int seq_length = {self.__seq_length};
        // STATE
{int_states}
        int any = -1;
        // BEHAVIOR
{int_behaviors}
        // STATUS
        int enabled = 0;
        int disabled = 1;
        
        // TRANSITIONS
        int[][] transitions = {{
{self.__make_choco_transitions_matrix()}
        }};

        // COSTS
        int[][] costs =  {{
{self.__make_choco_costs_matrix()}
        }};  


        // Captured variables
        IntVar[] sequence = model.intVarArray("sequence", seq_length, 0, {len(self.__transitions) - 1});
        IntVar[] states = model.intVarArray("states", seq_length + 1, 0, {len(self.__states) - 1});
        IntVar[] cost = model.intVarArray("cost", seq_length, 0, 1000000);

        for (int i = 0; i < seq_length; i++) {{
            model.element(states[i + 1], transitions, states[i], 0, sequence[i], 0);
        }}
        for (int i = 0; i < seq_length - 1; i++) {{
            BoolVar bi = model.arithm(sequence[i], "=", skip).reify();
            BoolVar bi1 = model.arithm(sequence[i+1], "=", skip).reify();
            bi.imp(bi1).post();;
        }}
        for (int i = 0; i < seq_length; i++) {{
            model.element(cost[i], costs, states[i], 0, sequence[i], 0);
        }}
        
        // Ports' statuses
{self.__make_choco_ports_status_constraints()}
    
        // Init state
        model.arithm(states[0], "=", {self.__init_state}).post();
        
        // Reconfiguration goals as constraints
{self.__make_choco_goal_constraints()}

        // Goal
        IntVar scost = model.intVar("scost", 0, 1000000);
        model.sum(cost, "=", scost).post();

        Solver solver = model.getSolver();
        Solution best = solver.findOptimalSolution(scost, false);
        if(best != null) {{
            solver.printShortStatistics();
        }} else {{
            solver.reset();
            List<Constraint> mus = solver.findMinimumConflictingSet(Arrays.asList(model.getCstrs()));
            System.out.println(mus);
        }}
    }}
}}




"""
        return content
    
    def __make_mzn_model(self):
        content = '\n'.join(f"""
int: seq_length = {self.__seq_length};

enum STATE = {{{','.join(self.states)}}};
enum BEHAVIOR = {{{','.join(self.transitions)}}}; 
enum STATUS = {{enabled, disabled}};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
{self.__make_mzn_transitions_matrix()};

array[STATE, BEHAVIOR] of int: costs = 
{self.__make_mzn_costs_matrix()};

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
{self.__make_mzn_ports_status_constraints()}

% Init state
constraint states[1]={self.__init_state};

% Reconfiguration goals as constraints
{self.__make_mzn_goal_constraints()}

% Goal
var int: scost;
constraint scost = sum(cost);
solve minimize scost;

""".split('\n')[1:])
        return content
    
    
    def solve_minizinc(self, findmus=False, write_file=False, print_model=False, solve_with="gecode"):
        wf = write_file if not findmus else True
        modelfile = "model.mzn"
        model = mznModel()
        mzn_str_model = self.__make_mzn_model()
        if print_model:
            print(mzn_str_model)
        if wf:
            with open(modelfile, 'w') as f:
                f.write(mzn_str_model)
                f.close()
            model.add_file(modelfile)
        else:
            model.add_string(mzn_str_model)
        solver = Solver.lookup(solve_with)
        instance = Instance(solver, model)
        result = instance.solve()
        if result.status == Status.UNSATISFIABLE or findmus:
            raise FindMUSException("UNSAT model")
        else:
            r = result.solution
            return CRSolution(r, sat=True)
        
    def solve_choco(self,findmus=False, write_file=False, print_model=False):
        if findmus:
            self.make_json_model(print_model=False, write_file=True, filepath="model.json")
            try:
                cmd = "java -jar ballet-planner-mus-1.0-SNAPSHOT-shaded.jar model.json"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                return CRSolution(result.stdout, sat=False)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred: {e}")
                print("Output:\n", e.stdout)
                print("Error:\n", e.stderr)
        else:
            wf = write_file
            modelfile = "TestModel.java"
            choco_str_model = self.__make_choco_model(classname="TestModel")
            if print_model:
                print(choco_str_model)
            if wf:
                with open(modelfile, 'w') as f:
                    f.write(choco_str_model)
                    f.close()
            return None, None
    
    def solve(self, mode="minizinc", findmus=False, write_file=False, print_model=False, solve_with="gecode"):
        if mode == "minizinc":
            return self.solve_minizinc(findmus, write_file, print_model, solve_with)
        if mode == "choco":
            return self.solve_choco(findmus, write_file, print_model)
        
        
class MultiCostRegular(Model):
    
    def __init__(self, models: dict[str, CostRegular], node):
        self._models = models
        self._node = node
        self._solutions = {k: None for k in models.keys()}
        self._port_status = {k: None for k in models.keys()}
        self.__first_skip = {k: -1 for k in models.keys()}
        
    def solve(self, mode="minizinc", print_model=False, write_file=False):
        for (key, model) in self._models.items():
            try:
                solution =  model.solve(mode, print_model, write_file)
                self._solutions[key] = solution
                self._port_status[key] = {port_name : solution.get(f"{port_name}_status") for port_name in model.ports.keys()}
                self.__first_skip[key] = indexOf('skip', solution.get("sequence"))
            except FindMUSException:
                self._solutions[key] = model.solve(mode="choco", findmus=True, print_model=False, write_file=False)
        return self._solutions

    def get_node(self):
        return self._node

    def get_components(self):
        return list(self._solutions.keys())

    def get_solution(self, key):
        return self._solutions[key]
    
    def get_port_status(self, component, port):
        return self._port_status[component][port][:self.__first_skip[component]+1]
    
    def get_port_statuses(self, component):
        result = {}
        for port in self._port_status[component].keys():
            result[port] = self._port_status[component][port][:self.__first_skip[component]+1]
        return result
    
    def get_sequence(self, component):
        return self._solutions[component].get("sequence")[:self.__first_skip[component]]
    
    def get_states(self, component):
        return self._solutions[component].get("states")[:self.__first_skip[component]+1]