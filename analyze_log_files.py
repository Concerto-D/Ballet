import pandas as pd
from glob import glob

def analyze_log_files():
    log_files = glob('*.log')  # Get all .log files in the current directory
    results = []
    
    global_max_times_per_iteration = []
    global_min_times_per_iteration = []

    for log_file in log_files:
        # Read the log file into a pandas DataFrame
        df = pd.read_csv(log_file, sep='|')

        # Filter by computation time keys (funsat, flocal, ffinal)
        comp_df = df[df['key'].isin(['funsat', 'flocal', 'ffinal'])]

        # Group by id and iteration, summing computation times
        comp_times = comp_df.groupby(['id', 'iteration'])['value'].sum().reset_index()

        # Group by iteration to find the max and min times per iteration
        max_times = comp_times.groupby('iteration')['value'].max()
        min_times = comp_times.groupby('iteration')['value'].min()

        # Store max and min times for the current log file
        mean_max_time = max_times.mean()
        mean_min_time = min_times.mean()

        # Store global max and min times for later averaging across all log files
        global_max_times_per_iteration.extend(max_times)
        global_min_times_per_iteration.extend(min_times)

        # Process messages for each iteration
        msg_df = df[df['key'] == 'messages']
        msg_sums = msg_df.groupby('iteration')['value'].sum()

        # Find the min_constraint and max_constraint for each iteration
        min_constraints = df[df['key'] == 'min_constraint'].groupby('iteration')['value'].min().reset_index()
        max_constraints = df[df['key'] == 'max_constraint'].groupby('iteration')['value'].max().reset_index()

        # Store the results for this log file
        results.append({
            'file': log_file,
            'mean_max_time': mean_max_time,
            'mean_min_time': mean_min_time,
            'messages_per_iteration': msg_sums,
            'min_constraints': min_constraints,
            'max_constraints': max_constraints
        })

    # Calculate the global mean of all max and min values across all iterations
    global_mean_max_time = sum(global_max_times_per_iteration) / len(global_max_times_per_iteration)
    global_mean_min_time = sum(global_min_times_per_iteration) / len(global_min_times_per_iteration)

    # Display the results for each log file
    for result in results:
        print(f"File: {result['file']}")
        print(f"Mean max computation time for this file: {result['mean_max_time']}")
        print(f"Mean min computation time for this file: {result['mean_min_time']}")
        print("Messages per iteration:")
        print(result['messages_per_iteration'])
        print("Min constraints per iteration:")
        print(result['min_constraints'])
        print("Max constraints per iteration:")
        print(result['max_constraints'])
        print("-" * 40)

    # Display the global mean values across all log files
    print(f"Global mean of all max computation times: {global_mean_max_time}")
    print(f"Global mean of all min computation times: {global_mean_min_time}")

if __name__ == "__main__":
    analyze_log_files()
