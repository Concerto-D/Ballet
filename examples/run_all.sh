#!/bin/bash

# Export Minizinc
export MINIZINC_HOME=~/Software/MiniZincIDE-2.7.6-bundle-linux-x86_64; export PATH=$PATH:$MINIZINC_HOME/bin

mkdir results 

# Run sat cases
./examples/run_central_user.sh 15 sat single time 
./examples/run_central_provider.sh 20 sat single time 
./examples/run_linear.sh 20 sat single time 
./examples/run_circular.sh 20 sat single time 
# ./examples/run_stratified.sh 20 sat single time 

# Git 
# git add results/ 
# git commit -m "Results for ICSME on topological sat cases"
# git push

# Run unsat cases
./examples/run_central_user.sh 15 unsat single time 
./examples/run_central_provider.sh 20 unsat single time 
./examples/run_linear.sh 20 unsat single time 
./examples/run_circular.sh 20 unsat single time 
# ./examples/run_stratified.sh 20 unsat single time 

# Git 
# git add results/ 
# git commit -m "Results for ICSME on topological unsat cases"
# git push