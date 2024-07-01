package gossip;

import gossip.json.CostRegularModel;
import gossip.json.Json2Model;
import gossip.json.Model2Choco;
import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.constraints.Constraint;
import org.chocosolver.solver.variables.IntVar;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class Main {

    public static void main(String[] args) {
        String filepath;
        if (args.length == 0) {
            throw new IllegalArgumentException("No filepath argument provided.");
        } else {
            filepath = args[0];
        }

        CostRegularModel cr_model = Json2Model.readJsonFile(filepath);
        Model choco_model = Model2Choco.toChocoModel(cr_model);


        Solver solver = choco_model.getSolver();
            solver.reset();
            List<Constraint> mus = solver.findMinimumConflictingSet(Arrays.asList(choco_model.getCstrs()));
            Map<Object, List<String>> tracker = (Map<Object, List<String>>) choco_model.getHook("tracker");
            mus.forEach(c -> {
                if (tracker.containsKey(c)) {
                    System.out.println(tracker.get(c));
                }
            });
//        }
    }
}