package gossip;

import gossip.json.CostRegularModel;
import gossip.json.JSON2Model;
import gossip.json.Model2Choco;
import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.IntVar;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class TestJsonModel {

    public static void main(String[] args) {
        String filepath = "resources/model.json";
        CostRegularModel cr_model = JSON2Model.readJsonFile(filepath);
        Model choco_model = Model2Choco.toChocoModel(cr_model);

        IntVar scost = (IntVar) choco_model.getHook("objective");
        Solver solver = choco_model.getSolver();
        Solution best = solver.findOptimalSolution(scost, false);

        if (best != null) {
            solver.printShortStatistics();
            System.out.println(solver.defaultSolution().toString());
        } else {
            solver.reset();
            List<Constraint> mus = solver.findMinimumConflictingSet(Arrays.asList(choco_model.getCstrs()));
            System.out.println("Minimum Conflicting Set of Constraints:");
            Map<Object, List<String>> tracker = (Map<Object, List<String>>) choco_model.getHook("tracker");
            mus.forEach(c -> {
                if (tracker.containsKey(c)) {
                    System.out.println(tracker.get(c));
                }
            });
        }
    }
}

