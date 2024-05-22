package gossip;
import java.util.Arrays;
import java.util.List;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;

public class TestModel {

    public static void main(String[]args){
    Model model = new Model();
    int seq_length = 12;
    // STATE
    int initiated = 0 ;
    int configured = 1 ;
    int deployed = 2 ;
    int any = -1;
    // BEHAVIOR
    int deploy = 0 ;
    int stop = 1 ;
    int uninstall = 2 ;
    int skip = 3 ;
    // STATUS
    int enabled = 0;
    int disabled = 1;

    // TRANSITIONS
    int[][] transitions = {
            {deployed, any, any, initiated},
            {deployed, any, any, configured},
            {any, configured, initiated, deployed}
    };

    // COSTS
    int[][] costs = {
            {2, 1000000, 1000000, 0},
            {1, 1000000, 1000000, 0},
            {1000000, 1, 1, 0}
    };

    // Captured variables
    IntVar[] sequence = model.intVarArray("sequence", seq_length, 0, 4);
    IntVar[] states = model.intVarArray("states", seq_length + 1, 0, 2);
    IntVar[] cost = model.intVarArray("cost", seq_length, 0, 1000000);

    for (int i = 0; i < seq_length; i++) {
        model.element(states[i + 1], transitions, states[i], 0, sequence[i], 0);
    }
    for (int i = 0; i < seq_length - 1; i++) {
        BoolVar bi = model.arithm(sequence[i], "=", skip).reify();
        BoolVar bi1 = model.arithm(sequence[i+1], "=", skip).reify();
        bi.imp(bi1).post();
    }
    for (int i = 0; i < seq_length; i++) {
        model.element(cost[i], costs, states[i], 0, sequence[i], 0);
    }

    // Ports' statuses
    IntVar[] service_status = model.intVarArray("service_status", seq_length + 1, 0, 1);
        for(int i = 0; i < seq_length + 1; i++) {
        BoolVar b0 = model.arithm(service_status[i], "=", enabled).reify();
        BoolVar b_service_deployed = model.arithm(states[i], "=", deployed).reify();
        model.addClausesBoolOrArrayEqVar(new BoolVar[]{b_service_deployed}, b0);
    }
    IntVar[] facts_service_status = model.intVarArray("facts_service_status", seq_length + 1, 0, 1);
        for(int i = 0; i < seq_length + 1; i++) {
        BoolVar b0 = model.arithm(facts_service_status[i], "=", enabled).reify();
        BoolVar b_facts_service_configured = model.arithm(states[i], "=", configured).reify();
        BoolVar b_facts_service_deployed = model.arithm(states[i], "=", deployed).reify();
        model.addClausesBoolOrArrayEqVar(new BoolVar[]{b_facts_service_configured,b_facts_service_deployed}, b0);
    }

    // Init state
    model.arithm(states[0], "=", initiated).post();

    // Reconfiguration goals as constraints
    IntVar count_deploy = model.intVar("count_deploy", 0, seq_length); // inferred
        model.sum(Arrays.stream(sequence).map(s -> s.eq(deploy).boolVar()).toArray(BoolVar[]::new), "=", count_deploy).post(); // inferred
        model.arithm(count_deploy, ">", 0).post(); // inferred


        model.arithm(states[seq_length], "=", deployed).post(); // inferred
    IntVar count_deployed = model.intVar("count_deployed", 0, seq_length); // inferred
        model.sum(Arrays.stream(states).map(s -> s.eq(deployed).boolVar()).toArray(BoolVar[]::new), "=", count_deployed).post(); // inferred
        model.arithm(count_deployed, ">", 0).post(); // inferred



    // Goal
    IntVar scost = model.intVar("scost", 0, 1000000);
    model.sum(cost, "=", scost).post();

    Solver solver = model.getSolver();
    Solution best = solver.findOptimalSolution(scost, false);
    if(best != null) {
        solver.printShortStatistics();
    } else {
        solver.reset();
        List<Constraint> mus = solver.findMinimumConflictingSet(Arrays.asList(model.getCstrs()));
        System.out.println(mus);
    }

}}
