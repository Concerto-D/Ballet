package gossip.json;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;

public class Model2Choco {

    private static final int maxInt = 1000000;

    private static int[] makeline_automata(CostRegularModel cr_model,
                                           String state, Map<String, String> transitions,
                                           Map<String, Integer> states_as_int) {
        List<String> transitions_with_skip = new ArrayList<>(cr_model.getTransitions());
        // replace '<>' by 'any'
        for (Map.Entry<String, String> entry : transitions.entrySet()) {
            if ("<>".equals(entry.getValue())) {
                entry.setValue("any");
            }
        }
        int[] result = transitions_with_skip.stream().map(
                transition -> {
                    if (transition.equals("skip")) {
                        return states_as_int.get(state);
                    } else return states_as_int.get(transitions.getOrDefault(transition, "any"));
                }
        ).collect(Collectors.toList()).stream().mapToInt(Integer::intValue).toArray();;

        return result;
    }

    private static int[][] make_automata(CostRegularModel cr_model,
                                         Map<String, Map<String, String>> automata,
                                         Map<String, Integer> states_as_int) {
        return cr_model.getStates().stream()
                .map(state -> makeline_automata(cr_model, state, automata.get(state), states_as_int)).toArray(int[][]::new);
    }

    private static int[] makeline_cost(CostRegularModel cr_model,
                                       Map<String, Integer> costs) {
        List<String> transitions_with_skip = new ArrayList<>(cr_model.getTransitions());
        transitions_with_skip.add("skip");

        return transitions_with_skip.stream().map(
                transition -> {
                    if (transition.equals("skip")) {
                        return 0;
                    } else return costs.getOrDefault(transition, maxInt);
                }
        ).collect(Collectors.toList()).stream().mapToInt(Integer::intValue).toArray();
    }

    private static int[][] make_cost(CostRegularModel cr_model,
                                     Map<String, Map<String, Integer>> costs) {
        return cr_model.getStates().stream()
                .map(state -> makeline_cost(cr_model, costs.get(state))).toArray(int[][]::new);
    }

    private static void addTracker(Object cstr, String cause, Map<Object, String> tracker) {
        tracker.put(cstr, cause);
    }

    public static Model toChocoModel(CostRegularModel cr_model) {

        Model model = new Model();
        Map<Object, String> tracker = new HashMap<>();
        // STATE
        int seq_length = cr_model.getStates().size() * cr_model.getTransitions().size();
        Map<String, Integer> states_as_int = new HashMap<>();
        int it_n_state = 0;
        for (String state : cr_model.getStates()){
            states_as_int.put(state, it_n_state);
            it_n_state++;
        }
        states_as_int.put("any", -1);

        // BEHAVIOR
        Map<String, Integer> behaviors_as_int = new HashMap<>();
        int it_n_behavior = 0;
        for (String transition : cr_model.getTransitions()){
            behaviors_as_int.put(transition, it_n_behavior);
            it_n_behavior++;
        }
        behaviors_as_int.put("skip", it_n_behavior);

        // STATUS
        Map<String, Integer> status_as_int = new HashMap<>();
        int enabled = 1;
        int disabled = 0;
        status_as_int.put("disabled", disabled);
        status_as_int.put("enabled", enabled);

        // TRANSITION
        int[][] transitions = make_automata(cr_model, cr_model.getAutomata(), states_as_int);
        // COSTS
        int[][] costs = make_cost(cr_model, cr_model.getCosts());

        // Captured variables
        IntVar[] sequence = model.intVarArray("sequence", seq_length, 0, it_n_behavior-1);
        IntVar[] states = model.intVarArray("states", seq_length + 1, 0, it_n_state-1);
        IntVar[] cost = model.intVarArray("cost", seq_length, 0, maxInt);
        for (int i = 0; i < seq_length; i++) {
            model.element(states[i + 1], transitions, states[i], 0, sequence[i], 0);
        }
        for (int i = 0; i < seq_length - 1; i++) {
            BoolVar bi = model.arithm(sequence[i], "=", behaviors_as_int.get("skip")).reify();
            BoolVar bi1 = model.arithm(sequence[i+1], "=", behaviors_as_int.get("skip")).reify();
            bi.imp(bi1).post();
        }
        for (int i = 0; i < seq_length; i++) {
            model.element(cost[i], costs, states[i], 0, sequence[i], 0);
        }

        // Ports' statuses
        cr_model.getPorts().keySet().forEach(port -> {
            String name_var = port+"_status";
            BoolVar[] status_var = model.boolVarArray(name_var, seq_length + 1);
            for(int i = 0; i < seq_length + 1; i++) {
                BoolVar port_boolvar = model.arithm(status_var[i], "=", enabled).reify();
                List<BoolVar> tmp_list = new ArrayList<>();
                for (String place: cr_model.getPorts().get(port)) {
                    BoolVar port_place_boolvar = model.arithm(states[i], "=", states_as_int.get(place)).reify();
                    tmp_list.add(port_place_boolvar);
                }
                BoolVar[] states_bool_var = tmp_list.toArray(new BoolVar[tmp_list.size()]);
                // Charle's style to add this clause:  model.addClausesBoolOrArrayEqVar(states_bool_var, port_boolvar);
                BoolVar orVar = model.or(states_bool_var).reify();
                Constraint c = model.arithm(orVar, "=", port_boolvar);
                // String at = (i == seq_length) ? "the end of the reconfiguration" : "i="+i;
                String places = String.join("%", cr_model.getPorts().get(port)); // TODO make a list
                String c_tracker = "model("+port+","+places+")";
                addTracker(c,  c_tracker, tracker);
                c.post();
            }
            model.addHook(name_var, status_var);
        });

        // Init State
        model.arithm(states[0], "=", states_as_int.get(cr_model.getInit_state())).post();

        // Reconfiguration as constraints
        for (CostRegularModel.PortConstraint constraint: cr_model.getPortConstraints()) {
            String tracker_constraint = "port("+constraint.getPort()+","+constraint.getStatus()+","+constraint.isFinal()+","+constraint.getGoal()+","+constraint.getSource()+")";
            String intvar_name = "count_"+constraint.getPort()+"_"+constraint.getStatus();
            IntVar count_status_port = model.intVar(intvar_name, 0, seq_length);
            model.sum((BoolVar[]) model.getHook(constraint.getPort() +"_status"),
                    "=", count_status_port).post();
            Constraint c0 = model.arithm(count_status_port, ">", 0);
            addTracker(c0, tracker_constraint, tracker);
            c0.post();
            if (constraint.isFinal()) {
                Constraint c1 = model.arithm(((BoolVar[])model.getHook(constraint.getPort() +"_status"))[seq_length],
                        "=", status_as_int.get(constraint.getStatus()));
                addTracker(c1, tracker_constraint, tracker);
                c1.post();
            }
        }

        for (CostRegularModel.StateConstraint constraint: cr_model.getStateConstraints()) {
            String tracker_constraint = "state("+constraint.getState()+","+constraint.isFinal()+","+constraint.getGoal()+","+constraint.getSource()+")";
            String intvar_name = "count_" + constraint.getState();
            IntVar count_state = model.intVar(intvar_name, 0, seq_length);
            model.sum(
                    Arrays.stream(states).map(s -> s.eq(states_as_int.get(constraint.getState())).boolVar())
                            .toArray(BoolVar[]::new), "=", count_state).post();
            Constraint c0 = model.arithm(count_state, ">", 0);
            addTracker(c0, tracker_constraint, tracker);
            c0.post();
            if (constraint.isFinal()) {
                Constraint c1 = model.arithm(states[seq_length], "=", states_as_int.get(constraint.getState()));
                addTracker(c1, tracker_constraint, tracker);
                c1.post();
            }
        }

        for (CostRegularModel.TransitionConstraint constraint: cr_model.getTransitionConstraints()) {
            String tracker_constraint = "transition("+constraint.getTransition()+","+constraint.getGoal()+","+constraint.getSource()+")";
            IntVar count_transition = model.intVar("count_"+constraint.getTransition(), 0, seq_length);
            Constraint c0 = model.sum(
                    Arrays.stream(sequence).map(s -> s.eq(behaviors_as_int.get(constraint.getTransition())).boolVar())
                            .toArray(BoolVar[]::new), "=", count_transition);
            addTracker(c0, tracker_constraint, tracker);
            c0.post();
            Constraint c1 = model.arithm(count_transition, ">", 0);
            addTracker(c1, tracker_constraint, tracker);
            c1.post();
        }

        for (CostRegularModel.MultiportConstraint constraint: cr_model.getMultiPortConstraints()){
            String str_ports = "["+String.join("%", constraint.getPorts())+"]" ;
            String tracker_constraint = "multiport("+str_ports+","+constraint.getStatus()+","+constraint.isFinal()+","+constraint.getGoal()+","+constraint.getSource()+")";
            String name_intvar = "count_" + String.join("_", constraint.getPorts()) + "_" + constraint.getStatus();
            IntVar count_multiport = model.intVar(name_intvar, 0, seq_length+1);

            IntVar[] count_wanted_status = new IntVar[seq_length];
            int wanted_status = status_as_int.get(constraint.getStatus());
            for (int i = 0; i < seq_length; i++) {
                String name_count_wanted = "count_" + String.join("_", constraint.getPorts()) + "_" + constraint.getStatus() + "i";
                List<BoolVar> tmp_list = new ArrayList<>();
                for (String port: constraint.getPorts()){
                    BoolVar[] port_status = (BoolVar[]) model.getHook(port +"_status");
                    tmp_list.add(port_status[i]);
                }
                // tmp_list at this point is a view of each port_status for a given i
                count_wanted_status[i] = model.intVar(name_count_wanted, 0, tmp_list.size());
                Constraint c0 = model.count(wanted_status, tmp_list.toArray(new IntVar[0]), count_wanted_status[i] );
                addTracker(c0, tracker_constraint, tracker);
                c0.post();
            }
            // count_multiport : number of times count_wanted_status respects "all equals to wanted_status"
            Constraint c1 = model.count(constraint.getPorts().size(), count_wanted_status, count_multiport);
            addTracker(c1, tracker_constraint, tracker);
            c1.post();
            Constraint c2 = model.arithm(count_multiport, ">", 0);
            addTracker(c2, tracker_constraint, tracker);
            c2.post();
        }

        IntVar scost = model.intVar("scost", 0, maxInt);
        model.sum(cost, "=", scost).post();
        // Hooks
        model.addHook("objective", scost);
        model.addHook("places", states);
        model.addHook("sequence", sequence);
        model.addHook("tracker", tracker);
        return model;
    }
}
