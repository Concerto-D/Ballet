package gossip.json;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.File;
import java.io.IOException;

public class Json2Model {

    public static CostRegularModel readJsonFile(String filePath) {
        ObjectMapper objectMapper = new ObjectMapper();
        CostRegularModel model = null;

        try {
            model = objectMapper.readValue(new File(filePath), CostRegularModel.class);
        } catch (IOException e) {
            e.printStackTrace();
        }

        return model;
    }


}
