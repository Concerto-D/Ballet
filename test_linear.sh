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
cp "$tests_dir/run_provider.py" .
cp "$tests_dir/run_transformer.py" .


# Check if n is not equal to 0
if [ "$n" -ne 0 ]; then
    for ((i=1; i<=$n; i++)); do
        # Execute the run_user.py script with the current value of i and unsat flag
        gnome-terminal -- bash -c "python3 run_transformer.py -n $n -i $i $unsat_flag; echo ""; read -n 1; exec bash"
    done
else
    echo "n is equal to 0, no chained transformer to run"
fi

# Run provider
gnome-terminal -- bash -c "python3 run_provider.py -n $n $unsat_flag; echo ""; read -n 1; exec bash"

echo "Press any key for cleaning local environement"; read -n 1 key;
rm "run_provider.py"
rm "run_transformer.py"

if [ "$key" = "x" ]; then
    rm *.mzn
else
    echo "Done"
fi