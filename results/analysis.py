import csv
import math

class Entry:

    def __init__(self, id, key, iteration , value):
        self.id = id
        self.key = key
        self.iteration = int(iteration)  # Convert iteration to integer
        self.value = float(value) if '.' in value else int(value) 


def load_results(files):
    res = {}
    for file in files:
        print(file)
        res[file] = load_result(file)
    return res


def load_result(file_log):
    entries = []
    with open(file_log, "r", newline="") as file:
        reader = csv.reader(file, delimiter="|")
        next(reader, None)  # Skip the header
        for row in reader:
            entries.append(Entry(row[0], row[1], row[2], row[3]))
    return entries


def build_analysis(input):
    results = {}
    for (filename, entries) in input.items():
        results[filename] = {}
        res = results[filename] 
        for entry in entries:
            if entry.iteration not in res.keys():
                res[entry.iteration] = []
            if "node_" in entry.id:
                if entry.key == "total_time":
                    res[entry.iteration].append((entry.id, entry.value) )
               
    for file in results.keys():
        max_entries = []
        for iteration in results[file].keys():
            max_entry = max(results[file][iteration], key=lambda x: x[1])
            max_entries.append(max_entry[1])
            print(f"On itration {iteration} of {file} -> Maximum value: {max_entry[1]}, found at: {max_entry[0]}")
        average = sum(max_entries) / len(max_entries) if max_entries else 0
        variance = sum((x - average) ** 2 for x in max_entries) / len(max_entries) if max_entries else 0
        std_deviation = math.sqrt(variance)
        print(f"Average time for {file} is {average} sec (V={variance}, σ={std_deviation})") 

if __name__ == "__main__":
    prefix = "results/"
    files = [prefix+"sat_circular_20.log", prefix+"sat_linear_20.log", prefix+"sat_cprovider_20.log", prefix+"sat_cuser_15.log"]
    files = files + [prefix+"unsat_circular_20.log", prefix+"unsat_linear_20.log", prefix+"unsat_cprovider_20.log", prefix+"unsat_cuser_15.log"]
    results = load_results(files)
    build_analysis(results)
