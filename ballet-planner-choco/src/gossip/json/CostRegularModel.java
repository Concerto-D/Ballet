package gossip.json;

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
        private List<TransitionConstraint> transition_constraint;

        // Getters and Setters
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

        public List<TransitionConstraint> getTransition_constraint() {
            return transition_constraint;
        }

        public void setTransition_constraint(List<TransitionConstraint> transition_constraint) {
            this.transition_constraint = transition_constraint;
        }

        @Override
        public String toString() {
            return "Constraints{" +
                    "state_constraint=" + state_constraint +
                    ", port_constraint=" + port_constraint +
                    ", transition_constraint=" + transition_constraint +
                    '}';
        }
    }

    public static class StateConstraint {
        private String state;
        private int final_;
        private int goal;

        // Getters and Setters
        public String getState() {
            return state;
        }

        public void setState(String state) {
            this.state = state;
        }

        public int getFinal_() {
            return final_;
        }

        public void setFinal_(int final_) {
            this.final_ = final_;
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
                    ", final_=" + final_ +
                    ", goal=" + goal +
                    '}';
        }
    }

    public static class PortConstraint {
        private String port;
        private String status;
        private int final_;
        private int goal;

        // Getters and Setters
        public String getPort() {
            return port;
        }

        public void setPort(String port) {
            this.port = port;
        }

        public String getStatus() {
            return status;
        }

        public void setStatus(String status) {
            this.status = status;
        }

        public int getFinal_() {
            return final_;
        }

        public void setFinal_(int final_) {
            this.final_ = final_;
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
                    ", final_=" + final_ +
                    ", goal=" + goal +
                    '}';
        }
    }

    public static class TransitionConstraint {
        private String transition;
        private int goal;

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
