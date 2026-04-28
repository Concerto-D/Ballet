package gossip.json;

import com.fasterxml.jackson.annotation.JsonFormat;

import java.util.List;
import java.util.Map;

public class CostRegularModel {

    private List<String> states;
    private List<String> transitions;
    private Map<String, Map<String, String>> automata;
    private Map<String, Map<String, Integer>> costs;
    private String init_state;
    private Map<String, List<String>> ports;
    private Constraints constraints;

    // Getters and Setters
    public List<String> getStates() {
        return states;
    }

    public void setStates(List<String> states) {
        this.states = states;
    }

    public List<String> getTransitions() {
        return transitions;
    }

    public void setTransitions(List<String> transitions) {
        this.transitions = transitions;
    }

    public Map<String, Map<String, String>> getAutomata() {
        return automata;
    }

    public void setAutomata(Map<String, Map<String, String>> automata) {
        this.automata = automata;
    }

    public Map<String, Map<String, Integer>> getCosts() {
        return costs;
    }

    public void setCosts(Map<String, Map<String, Integer>> costs) {
        this.costs = costs;
    }

    public String getInit_state() {
        return init_state;
    }

    public void setInit_state(String init_state) {
        this.init_state = init_state;
    }

    public Map<String, List<String>> getPorts() {
        return ports;
    }

    public void setPorts(Map<String, List<String>> ports) {
        this.ports = ports;
    }

    public Constraints getConstraints() {
        return constraints;
    }

    public List<PortConstraint> getPortConstraints() {
        return constraints.getPort_constraint();
    }

    public List<ValueConstraint> getValueConstraints() {
        return constraints.getValue_constraint();
    }

    public List<BinConstraint> getBinConstraints() {
        return constraints.getBin_constraint();
    }

    public List<StateConstraint> getStateConstraints() {
        return constraints.getState_constraint();
    }

    public List<TransitionConstraint> getTransitionConstraints() {
        return constraints.getTransition_constraint();
    }

    public void setConstraints(Constraints constraints) {
        this.constraints = constraints;
    }

    @Override
    public String toString() {
        return "CostRegularModel{" +
                "states=" + states +
                ", transitions=" + transitions +
                ", automata=" + automata +
                ", costs=" + costs +
                ", init_state='" + init_state + '\'' +
                ", ports=" + ports +
                ", constraints=" + constraints +
                '}';
    }

    public static class Constraints {
        private List<StateConstraint> state_constraint;
        private List<PortConstraint> port_constraint;
        private List<MultiportConstraint> multiport_constraint;
        private List<TransitionConstraint> transition_constraint;
        private List<ValueConstraint> value_constraint;
        private List<BinConstraint> bin_constraint;

        public List<StateConstraint> getState_constraint() {
            return state_constraint;
        }

        public void setState_constraint(List<StateConstraint> state_constraint) {
            this.state_constraint = state_constraint;
        }

        public List<PortConstraint> getPort_constraint() {
            return port_constraint;
        }

        public void setPort_constraint(List<PortConstraint> port_constraint) {
            this.port_constraint = port_constraint;
        }

        public List<MultiportConstraint> getMultiport_constraint() {
            return multiport_constraint;
        }

        public void setMultiport_constraint(List<MultiportConstraint> multiport_constraint) {
            this.multiport_constraint = multiport_constraint;
        }

        public List<TransitionConstraint> getTransition_constraint() {
            return transition_constraint;
        }

        public void setTransition_constraint(List<TransitionConstraint> transition_constraint) {
            this.transition_constraint = transition_constraint;
        }

        public List<ValueConstraint> getValue_constraint() {
            return value_constraint;
        }

        public void setValue_constraint(List<ValueConstraint> value_constraint) {
            this.value_constraint = value_constraint;
        }

        public List<BinConstraint> getBin_constraint() {
            return bin_constraint;
        }

        public void setBin_constraint(List<BinConstraint> bin_constraint) {
            this.bin_constraint = bin_constraint;
        }

        @Override
        public String toString() {
            return "Constraints{" +
                    "state_constraint=" + state_constraint +
                    ", port_constraint=" + port_constraint +
                    ", multiport_constraint=" + multiport_constraint +
                    ", transition_constraint=" + transition_constraint +
                    ", value_constraint=" + value_constraint +
                    ", bin_constraint=" + bin_constraint +
                    '}';
        }
    }

    public static class StateConstraint {
        private String state;
        private int isFinal;
        private int goal;
        private String source;

        public String getSource(){ return source; }
        public void setSource(String source) { this.source = source; }

        // Getters and Setters
        public String getState() {
            return state;
        }

        public void setState(String state) {
            this.state = state;
        }

        public boolean isFinal() {
            return isFinal == 1;
        }

        public int getIsFinal() {
            return isFinal;
        }

        public void setIsFinal(int isFinal) {
            this.isFinal = isFinal;
        }

        public int getGoal() {
            return goal;
        }

        public void setGoal(int goal) {
            this.goal = goal;
        }

        @Override
        public String toString() {
            return "StateConstraint{" +
                    "state='" + state + '\'' +
                    ", final_=" + isFinal +
                    ", goal=" + goal +
                    '}';
        }
    }

    public static class PortConstraint {
        private String port;
        private String status;
        private int isFinal;
        private int goal;
        private String source;

        public String getSource(){ return source; }
        public void setSource(String source) { this.source = source; }

        // Getters and Setters
        public String getPort() { return port; }

        public void setPort(String port) {
            this.port = port;
        }

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }

        public int getIsFinal() {
            return isFinal;
        }

        public boolean isFinal() {
            return isFinal == 1;
        }


        public void setIsFinal(int isFinal) {
            this.isFinal = isFinal;
        }

        public int getGoal() {
            return goal;
        }

        public void setGoal(int goal) {
            this.goal = goal;
        }

        @Override
        public String toString() {
            return "PortConstraint{" +
                    "port='" + port + '\'' +
                    ", status='" + status + '\'' +
                    ", final=" + isFinal +
                    ", goal=" + goal +
                    '}';
        }
    }

    public static class MultiportConstraint {
        private List<String> ports;
        private String status;
        private int isFinal;
        private int goal;
        private String source;

        public String getSource(){ return source; }
        public void setSource(String source) { this.source = source; }

        // Getters and Setters
        public List<String> getPorts() { return ports; }

        public void setPort(List<String> new_ports) {
            this.ports = new_ports;
        }

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }

        public int getIsFinal() {
            return isFinal;
        }

        public boolean isFinal() {
            return isFinal == 1;
        }


        public void setIsFinal(int isFinal) {
            this.isFinal = isFinal;
        }

        public int getGoal() {
            return goal;
        }

        public void setGoal(int goal) {
            this.goal = goal;
        }

        @Override
        public String toString() {
            return "PortConstraint{" +
                    "ports='" + ports + '\'' +
                    ", status='" + status + '\'' +
                    ", final=" + isFinal +
                    ", goal=" + goal +
                    '}';
        }
    }

    public static class ValueConstraint {
        private String name;
        private int value;

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public int getValue() {
            return value;
        }

        public void setValue(int value) {
            this.value = value;
        }

        @Override
        public String toString() {
            return "ValueConstraint{" +
                    "name='" + name + '\'' +
                    ", value=" + value +
                    '}';
        }
    }

    public static class BinConstraint{
        private String left;
        private String right;
        private String comparator;
        private String transition_source;
        private String transition_behavior;

        public String getLeft() {
            return left;
        }

        public void setLeft(String left) {
            this.left = left;
        }

        public String getRight() {
            return right;
        }

        public void setRight(String right) {
            this.right = right;
        }

        public String getComparator() {
            return comparator;
        }

        public void setComparator(String comparator) {
            this.comparator = comparator;
        }

        public String getTransition_source() {
            return transition_source;
        }

        public void setTransition_source(String transition_source) {
            this.transition_source = transition_source;
        }

        public String getTransition_behavior() {
            return transition_behavior;
        }

        public void setTransition_behavior(String transition_behavior) {
            this.transition_behavior = transition_behavior;
        }

        @Override
        public String toString() {
            return "BinConstraint{" +
                    "left='" + left + '\'' +
                    ", right='" + right + '\'' +
                    ", comparator='" + comparator + '\'' +
                    ", transition_source='" + transition_source + '\'' +
                    ", transition_behavior='" + transition_behavior + '\'' +
                    '}';
        }
    }

    public static class TransitionConstraint {
        private String transition;
        private int goal;
        private String source;

        public String getSource(){ return source; }
        public void setSource(String source) { this.source = source; }

        // Getters and Setters
        public String getTransition() {
            return transition;
        }

        public void setTransition(String transition) {
            this.transition = transition;
        }

        public int getGoal() {
            return goal;
        }

        public void setGoal(int goal) {
            this.goal = goal;
        }

        @Override
        public String toString() {
            return "TransitionConstraint{" +
                    "transition='" + transition + '\'' +
                    ", goal=" + goal +
                    '}';
        }
    }
}
