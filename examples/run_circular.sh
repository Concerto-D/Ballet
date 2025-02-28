#!/bin/bash

# Define the tests directory
tests_dir="examples/tests_gossip/circular"

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
    time_file="unsat_circular_$n.log"
    mzn_dir=mzn_unsat_circular_$n
else
    unsat_flag=""
    time_file="sat_circular_$n.log"
    mzn_dir=mzn_sat_circular_$n
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

cp "$tests_dir/run_circular_provider.py" .
cp "$tests_dir/run_circular_user.py" .
cp "$tests_dir/run_circular_transformer.py" .

# Start building the JSON structure using jq
inventory=$(jq -n --arg address "$ADDRESS" --argjson port_planner "$PROVIDER_PORT" \
  '{provider: {address: $address, port_planner: $port_planner}}')
inventory=$(echo "$inventory" | jq --arg address "$ADDRESS" --argjson port_planner "$ENDUSER_PORT" \
  '. + {user: {address: $address, port_planner: $port_planner}}')
# Loop to add users
for uid in $(seq 0 $((n-1))); do
    transformer_port=$((ENDUSER_PORT + 1 + uid))
    inventory=$(echo "$inventory" | jq --arg address "$ADDRESS" --argjson port_planner "$transformer_port" --arg uid "$uid" \
      '. + {("transformer" + $uid): {address: $address, port_planner: $port_planner}}')
done
# Write the inventory to a JSON file
echo "$inventory" > inventory.json


# rm "run_circular_provider.py" .
# rm "run_circular_user.py" .
# rm "run_circular_transformer.py" .

if $single; then
    [ -f $time_file ] && rm $time_file
    touch $time_file
    for ((ite=1; ite<=10; ite++)); do
        python run_circular_provider.py -n $n $unsat_flag -inventory inventory.json $timeflag -it $ite >> $time_file &
        python run_circular_user.py -n $n $unsat_flag -inventory inventory.json $timeflag -it $ite >> $time_file &
        if [ "$n" -ne 0 ]; then
            for ((i=1; i<=$n; i++)); do
                python run_circular_transformer.py -n $n -i $i $unsat_flag -inventory inventory.json $timeflag -it $ite >> $time_file &
            done
        fi
        wait
    done
    if [ -d results/$mzn_dir ]; then
    rm -rf results/$mzn_dir
    fi
    mkdir results/$mzn_dir
    mv *mzn results/$mzn_dir
    mv $time_file results/
else

    # Check if n is not equal to 0
    if [ "$n" -ne 0 ]; then
        for ((i=0; i<$n; i++)); do
            gnome-terminal -- bash -c "python $debugger_flag run_circular_transformer.py -n $n -i $i $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"
        done
    else
        echo "n is equal to 0, no chained user to run"
    fi

    # Run provider
    gnome-terminal -- bash -c "python $debugger_flag run_circular_provider.py -n $n $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"
    # Run end user
    gnome-terminal -- bash -c "python $debugger_flag run_circular_user.py -n $n $unsat_flag $verbose_flag -inventory inventory.json; echo ''; read -n 1; exec bash"

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

rm "run_circular_provider.py" .
rm "run_circular_user.py" .
rm "run_circular_transformer.py" .