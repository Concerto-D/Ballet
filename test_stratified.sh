#!/bin/bash

# Define the tests directory
tests_dir="tests_gossip/stratified"

# Check for the first argument (-n)
if [ -z "$1" ]; then
    n=0  # Default value
else
    n=$1
fi

# Check for the second argument (-s) equal to "unsat"
if [ "$2" = "unsat" ]; then
    unsat_flag="--unsat"
else
    unsat_flag=""
fi

# Check for the third argument (-s) equal to "debug"
if [ "$3" = "debug" ]; then
    debugger_flag="-m ipdb"
else
    debugger_flag=""
fi

cp "$tests_dir/run_provider.py" .
cp "$tests_dir/run_end_user.py" .
cp "$tests_dir/run_parallel_user.py" .

# Check if n is not equal to 0
if [ "$n" -ne 0 ]; then
    for ((i=0; i<$n; i++)); do
        # Execute the run_parallel_user.py script with the current value of i and unsat flag
        # if [ "$i" -ne 0 ]; then
        gnome-terminal -- bash -c "python3 $debugger_flag run_parallel_user.py -n $n -i $i $unsat_flag; echo ''; read -n 1; exec bash"
        # fi
    done
else
    echo "n is equal to 0, no chained user to run"
fi

# Run provider
gnome-terminal -- bash -c "python3 $debugger_flag run_provider.py -n $n $unsat_flag; echo ''; read -n 1; exec bash"
# Run end user
gnome-terminal -- bash -c "python3 $debugger_flag run_end_user.py -n $n $unsat_flag; echo ''; read -n 1; exec bash"

echo "Press any key for cleaning local environment"; read -n 1 key
rm "run_provider.py"
rm "run_parallel_user.py"
rm "run_end_user.py"

if [ "$key" = "x" ] || [ "$key" = "c" ]; then
    echo "You pressed 'x'. Cleaning local environment."
    rm *.mzn
    rm *.json
    # Close all gnome-terminal instances except the current one
    current_pid=$$
    parent_pid=$(ps -o ppid= -p $current_pid)
    gnome_terminal_pids=$(pgrep -f gnome-terminal)
    for pid in $gnome_terminal_pids; do
        if [ "$pid" != "$parent_pid" ] && [ "$pid" != "$current_pid" ]; then
            kill -9 $pid
        fi
    done
else
    echo "Done"
fi
