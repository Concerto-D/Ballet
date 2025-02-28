include "count.mzn";
include "regular.mzn";
                            
int: seq_length = 27;

enum STATE = {uninstalled,configured,running};
enum BEHAVIOR = {deploy,stop,suspend,skip,wait_provider10_update,wait_provider6_update,wait_provider12_update,wait_provider13_update,wait_provider0_update,wait_provider7_update,wait_provider4_update,wait_provider1_update,wait_provider9_update,wait_provider5_update,wait_provider3_update,wait_provider8_update,wait_provider11_update,wait_provider2_update,wait_provider14_update}; 
enum STATUS = {enabled, disabled};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|running,uninstalled,<>,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled,uninstalled
|running,uninstalled,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured,configured
|running,<>,configured,running,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>,<>|];

array[STATE, BEHAVIOR] of int: costs = 
[|3,100000,100000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
|1,1,100000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
|100000,100000,1,0,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000,100000|];

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
array[1..seq_length+1] of var STATUS : config_status;
constraint forall (i in 1..seq_length+1) (config_status[i] = enabled <-> states[i] = configured \/ states[i] = running);
array[1..seq_length+1] of var STATUS : service_status;
constraint forall (i in 1..seq_length+1) (service_status[i] = enabled <-> states[i] = running);

% Init state
constraint states[1]=running;
constraint regular(sequence, transitions, running, {uninstalled,configured,running});

% Reconfiguration goals as constraints
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider9_update) = 1; % inferred
constraint count(sequence, wait_provider12_update) = 1; % inferred
constraint count(sequence, wait_provider0_update) = 1; % inferred
constraint count(sequence, wait_provider1_update) = 1; % inferred
constraint count(sequence, wait_provider11_update) = 1; % inferred
constraint count(sequence, wait_provider14_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider8_update) = 1; % inferred
constraint count(sequence, wait_provider4_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider2_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider6_update) = 1; % inferred
constraint states[seq_length+1] = running; % goal
constraint count (states, running) > 0; % goal
constraint count(sequence, wait_provider7_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider10_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider5_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider3_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(sequence, wait_provider13_update) = 1; % inferred
constraint count(service_status, disabled) > 0; % inferred
constraint count(service_status, disabled) > 0; % inferred


% Goal
var int: scost;
constraint scost = sum(cost);

% Side structure for exploration strategy
array[1..seq_length] of var int: reversed_cost = array1d(1..seq_length, [cost[seq_length - i + 1] | i in 1..seq_length]);


solve 
:: int_search(reversed_cost, first_fail, indomain_min)
minimize scost;

