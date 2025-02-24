#!/bin/bash

# Define the tests directory
tests_dir="examples/tests_gossip/stratified"

ADDRESS="localhost"
PROVIDER_PORT=3000
ENDUSER_PORT=3001

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

# Check for the third argument (-s) equal to "debug"
if [ "$3" = "debug" ] || [ "$4" = "debug" ] || [ "$5" = "debug" ]; then
    debugger_flag="-m ipdb"
else
    debugger_flag=""
fi

if [ "$3" = "verbose" ] || [ "$4" = "verbose" ] || [ "$5" = "verbose" ]; then
    verbose_flag="--verbose"
else
    verbose_flag=""
fi

if [ "$3" = "single" ] || [ "$4" = "single" ] || [ "$5" = "single" ]; then
    single=true
else
    single=false
fi

cp "$tests_dir/run_provider.py" .
cp "$tests_dir/run_end_user.py" .
cp "$tests_dir/run_parallel_user.py" .

# Start building the JSON structure using jq
inventory=$(jq -n --arg address "$ADDRESS" --argjson port_planner "$PROVIDER_PORT" \
  '{provider: {address: $address, port_planner: $port_planner}}')
inventory=$(echo "$inventory" | jq --arg address "$ADDRESS" --argjson port_planner "$ENDUSER_PORT" \
  '. + {enduser: {address: $address, port_planner: $port_planner}}')
# Loop to add users
for uid in $(seq 0 $((n-1))); do
    user_port=$((ENDUSER_PORT + 1 + uid))
    inventory=$(echo "$inventory" | jq --arg address "$ADDRESS" --argjson port_planner "$user_port" --arg uid "$uid" \
      '. + {("user" + $uid): {address: $address, port_planner: $port_planner}}')
done
# Write the inventory to a JSON file
echo "$inventory" > inventory.json



if $single; then
    [ -f $time_file ] && rm $time_file
    touch $time_file
    for ((ite=1; ite<=30; ite++)); do
        python3.11 run_provider.py -n $n $unsat_flag -inventory inventory.json --time &
        python3.11 run_end_user.py -n $n $unsat_flag -inventory inventory.json --time &
        if [ "$n" -ne 0 ]; then
            for ((i=1; i<=$n; i++)); do
                python3.11 run_parallel_user.py -n $n -i $i $unsat_flag -inventory inventory.json --time &
            done
        fi
        wait
    done
else

    # Check if n is not equal to 0
    if [ "$n" -ne 0 ]; then
        for ((i=0; i<$n; i++)); do
            # Execute the run_parallel_user.py script with the current value of i and unsat flag
            # if [ "$i" -ne 0 ]; then
            gnome-terminal -- bash -c "python3.11 $debugger_flag run_parallel_user.py -n $n -i $i $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"
            # fi
        done
    else
        echo "n is equal to 0, no chained user to run"
    fi

    # Run provider
    gnome-terminal -- bash -c "python3.11 $debugger_flag run_provider.py -n $n $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"
    # Run end user
    gnome-terminal -- bash -c "python3.11 $debugger_flag run_end_user.py -n $n $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"

    echo "Press any key for cleaning local environment"; read -n 1 key

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
rm "run_parallel_user.py"
rm "run_end_user.py"