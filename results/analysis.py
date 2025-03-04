import csv


"""
Schema of data:

iteration
    component
        local time
    node
        name node
            waits
            total time
            messages

"""

class Entry:

    def __init__(self, id, key, iteration , value):
        self.id = id
        self.key = key
        self.iteration = int(iteration)  # Convert iteration to integer
        self.value = float(value) if '.' in value else int(value) 


def load_results(files):
    res = {}
    for file in files:
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
            print(f"On itration {iteration} -> Maximum value: {max_entry[1]}, found at: {max_entry[0]}")
        average = sum(max_entries) / len(max_entries) if max_entries else 0
        print(f"Average time for {filename} is {average} sec") 

if __name__ == "__main__":
    prefix = "/home/jolan/Documents/Projects/Ballet/results/"
    files = [prefix+"sat_circular_20.log"]
    results = load_results(files)
    build_analysis(results)