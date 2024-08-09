#!/bin/bash

# Define the tests directory
tests_dir="tests_gossip/linear"

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
cp "$tests_dir/run_transformer.py" .

# Check if n is not equal to 0
if [ "$n" -ne 0 ]; then
    for ((i=1; i<=$n; i++)); do
        # Execute the run_user.py script with the current value of i and unsat flag
        gnome-terminal -- bash -c "python3 $debugger_flag run_transformer.py -n $n -i $i $unsat_flag; echo ''; read -n 1; exec bash"
    done
else
    echo "n is equal to 0, no chained transformer to run"
fi

# Run provider
gnome-terminal -- bash -c "python3 $debugger_flag run_provider.py -n $n $unsat_flag; echo ''; read -n 1; exec bash"

echo "Press any key for cleaning local environment"; read -n 1 key
rm "run_provider.py"
rm "run_transformer.py"

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
