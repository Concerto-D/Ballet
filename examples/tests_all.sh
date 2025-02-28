#!/bin/bash

# Export Minizinc
export MINIZINC_HOME=~/Software/MiniZincIDE-2.7.6-bundle-linux-x86_64; export PATH=$PATH:$MINIZINC_HOME/bin;

# Run sat cases
./examples/test_central_user.sh 1 sat single time 
./examples/test_central_provider.sh 2 sat single time 
./examples/test_linear.sh 2 sat single time 
./examples/test_circular.sh 2 sat single time 
./examples/test_stratified.sh 2 sat single time 
./examples/test_stratified.sh 20 sat single time 

echo "DONE !"
