from minizinc import Instance, Model as mznModel, Solver, Status
import subprocess, re
from ballet.utils.list_utils import flatmap, indexify
from gossip.gossip import Model

class FindMUSException(Exception):
    
    def __init__(self, message, out):            
        super().__init__(message)
        # Extracting MUS
        mus_match = re.search(r'MUS: (\d+)', out)
        # self.__mus_value = None
        self.__mus_value = int(mus_match.group(1))
        # Extracting Brief
        brief_match = re.search(r'Brief: (.+)', out)
        self.__brief_value = brief_match.group(1)
        # self.__brief_value = None
        # Extracting Traces
        traces_match = re.search(r'Traces:(.+?)%%%mzn-progress', out, re.DOTALL)
        # self.__traces_value = None
        self.__traces_value = traces_match.group(1).strip()
        # self.__lines_of_mzn = FindMUSException._extract_lines(self.__traces_value)
    
    # def _extract_lines(traces):
    #     splitted = traces.split(";")
    #     file = splitted[0]
    #     return splitted[1:]
        
    @property
    def mus(self):
        return self.__mus_value
    
    @property
    def lines(self):
        return self.__lines_of_mzn
    
    @property
    def brief(self):
        return self.__brief_value
    
    @property
    def traces(self):
        return self.__traces_value

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
    
    def __init__(self, state, final=False, goal=False):
        super().__init__(goal)
        self.__state = state
        self.__final = final
        
    def isStateConstraint(self):
        return True
        
    @property
    def final(self):
        return self.__final
        
    @property
    def state(self):
        return self.__state
        
        
class PortConstraint(CRConstraint):
    
    def __init__(self, port, status, final=False, goal=False):
        super().__init__(goal)
        assert status == "enabled" or status == "disabled"
        self.__port = port
        self.__status = status
        self.__final = final
        
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
    

class TransitionConstraint(CRConstraint):
    
    def __init__(self, transition, goal=False):
        super().__init__(goal)
        self.__transition = transition
    
    def isTransitionConstraint(self):
        return True
        
    @property
    def transition(self):
        return self.__transition


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
        self.__transitions.append("skip")
        self.__automata = automata
        self.__init_state = init_state
        for state in self.__states:
            self.__automata[state]["skip"] = state
        self.__costs = costs
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
                assert automata[source][label] in states # assert target is declared
        
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
        ll = '\n'.join(map(lambda l: f"\t{l}",lines))
        return '\n'.join(f"""
{ll}""".split('\n')[1:])
        
    def __make_mzn_costs_line(self, state):
        targets = []
        for transition in self.__transitions:
            if state in self.__costs.keys() and transition in self.__costs[state].keys(): # the transition has a cost
                targets.append(str(self.__costs[state][transition]))
        
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
        ll = '\n'.join(map(lambda l: f"\t{l}",lines))
        return '\n'.join(f"""
{ll}""".split('\n')[1:])
        
        
    def __make_mzn_port_line(self, port, places):
        decl = f"array[1..seq_length+1] of var STATUS : {port}_status;"
        disjunction = ' \/ '.join(map(lambda place: f"states[i] = {place}", places))
        constr = f"constraint forall (i in 1..seq_length+1) ({port}_status[i] = enabled <-> {disjunction});"
        return [decl, constr]
    
    def __make_mzn_ports_status_constraints(self):
        lines = flatmap(lambda port: self.__make_mzn_port_line(port, self.__ports[port]), self.__ports.keys())
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
    
    def __make_mzn_constraint_line(self, constraint):
        if constraint.isPortConstraint():
            return self.__make_mzn_port_constraint_line(constraint)
        if constraint.isStateConstraint():
            return self.__make_mzn_state_constraint_line(constraint)
        if constraint.isTransitionConstraint():
            return self.__make_mzn_transition_constraint_line(constraint)
    
    def __make_mzn_goal_constraints(self):
        lines = flatmap(lambda constraint: self.__make_mzn_constraint_line(constraint), self.__constraints)
        return '\n'.join(lines)
    
    
    def __make_choco_model(self):
        int_states = '\n'.join(map(lambda p: "    int " + str(p[0]) +" = "+ str(p[1])+" ;" , indexify(self.states)))
        int_behaviors = '\n'.join(map(lambda p: "    int " + str(p[0]) +" = "+ str(p[1])+" ;" , indexify(self.transitions)))
        content = f"""
import java.util.Arrays;
import java.util.List;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;

public class CRModel {{
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
    IntVar[] sequence = model.intVarArray("sequence", seq_length, 0, 4);
    IntVar[] states = model.intVarArray("states", seq_length + 1, 0, 2);
    IntVar[] cost = model.intVarArray("cost", seq_length, 0, 1000000);

    // Constraints
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
            command = f"minizinc --solver findMUS -a {modelfile}"
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            raise FindMUSException(result.stdout,result.stdout)
        else:
            return result
        
    def solve_choco(self,findmus=False, write_file=False, print_model=False):
        modelfile = "model.java"
        choco_str_model = self.__make_choco_model()
        if print_model:
            print(choco_str_model)
    
    def solve(self, mode="minizinc", findmus=False, write_file=False, print_model=False, solve_with="gecode"):
        if mode == "minizinc":
            self.solve_minizinc(findmus, write_file, print_model, solve_with)
        if mode == "choco":
            self.solve_choco(findmus=False, write_file=False, print_model=False)