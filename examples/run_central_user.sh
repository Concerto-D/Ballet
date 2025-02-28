#!/bin/bash

# Define the tests directory
tests_dir="examples/tests_gossip/central_user"

ADDRESS='localhost'
USER_PORT=3000


# Usage: ./test_central_user 5 sat single --time

# Check for the first argument (-n)
if [ -z "$1" ]; then
    n=0  # Default value
else
    n=$1
fi
# Check for the second argument (-s) equal to "unsat"
if [ "$2" = "unsat" ]; then
    unsat_flag="--unsat"
    time_file="unsat_cuser_$n.log"
else
    unsat_flag=""
    time_file="sat_cuser_$n.log"
fi
# Check if we want debug mode
if [ "$3" = "debug" ] || [ "$4" = "debug" ] || [ "$5" = "debug" ] || [ "$6" = "debug" ]; then
    debugger_flag="-m ipdb"
else
    debugger_flag=""
fi
# Check if we want verbosity
if [ "$3" = "verbose" ] || [ "$4" = "verbose" ] || [ "$5" = "verbose" ] || [ "$6" = "verbose" ]; then
    verbose_flag="--verbose"
else
    verbose_flag=""
fi
# Check if we want to run all programs in a single terminal
if [ "$3" = "single" ] || [ "$4" = "single" ] || [ "$5" = "single" ] || [ "$6" = "single" ]; then
    single=true
else
    single=false
fi
# Check if we want to record time of calculation
if [ "$3" = "time" ] || [ "$4" = "time" ] || [ "$5" = "time" ] || [ "$6" = "time" ]; then
    timeflag="--time"
else
    timeflag=""
fi

cp "$tests_dir/run_provider.py" .
cp "$tests_dir/run_user.py" .


# Start building the JSON structure using jq
inventory=$(jq -n --arg address "$ADDRESS" --argjson port_planner "$USER_PORT" \
  '{user: {address: $address, port_planner: $port_planner}}')
# Loop to add users
for pid in $(seq 0 $((n-1))); do
    provider_port=$((USER_PORT + 1 + pid))
    inventory=$(echo "$inventory" | jq --arg address "$ADDRESS" --argjson port_planner "$provider_port" --arg pid "$pid" \
      '. + {("provider" + $pid): {address: $address, port_planner: $port_planner}}')
done
# Write the inventory to a JSON file
echo "$inventory" > inventory.json


if $single; then
    [ -f $time_file ] && rm $time_file
    touch $time_file
    echo "id|key|iteration|value" >> $time_file
    for ((ite=1; ite<=10; ite++)); do
        python run_user.py -n $n $unsat_flag -inventory inventory.json $timeflag -it $ite >> $time_file &
        if [ "$n" -ne 0 ]; then
            for ((i=1; i<=$n; i++)); do
                python run_provider.py -n $n -i $i $unsat_flag -inventory inventory.json $timeflag -it $ite >> $time_file &
            done
        fi
        wait
    done
    mzn_dir=mzn_sat_cuser_$n
    if [ -d results/$mzn_dir ]; then
    rm -rf results/$mzn_dir
    fi
    mkdir results/$mzn_dir
    mv *mzn results/$mzn_dir
    mv $time_file results/
else
    # Run provider
    gnome-terminal -- bash -c "python $debugger_flag run_user.py $verbose_flag -n $n $unsat_flag -inventory inventory.json; echo ""; read -n 1; exec bash"

    # Check if n is not equal to 0
    if [ "$n" -ne 0 ]; then
        for ((i=1; i<=$n; i++)); do
            # Execute the run_user.py script with the current value of i and unsat flag
            gnome-terminal -- bash -c "python $debugger_flag run_provider.py $verbose_flag -n $n -i $i $unsat_flag -inventory inventory.json; echo ""; read -n 1; exec bash"
        done
    else
        echo "n is equal to 0, no parallel user to run"
    fi

    echo "Press any key for cleaning local environement"; read -n 1 key;


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
fi

rm "run_provider.py"
rm "run_user.py"
