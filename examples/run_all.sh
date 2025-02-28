#!/bin/bash

# Export Minizinc
export MINIZINC_HOME=~/Software/MiniZincIDE-2.7.6-bundle-linux-x86_64; export PATH=$PATH:$MINIZINC_HOME/bin; minizinc --help

# Run sat cases
./examples/test_central_user.sh 15 sat single time 
./examples/test_central_provider.sh 20 sat single time 
./examples/test_linear.sh 20 sat single time 
./examples/test_circular.sh 20 sat single time 
./examples/test_stratified.sh 20 sat single time 

# Run unsat cases
./examples/test_central_user.sh 15 unsat single time 
./examples/test_central_provider.sh 20 unsat single time 
./examples/test_linear.sh 20 unsat single time 
./examples/test_circular.sh 20 unsat single time 
./examples/test_stratified.sh 20 unsat single time 

# Git 
# git add results/ 
# git commit -m "Results for ICSME on topological cases"
# git push