include "count.mzn";
include "regular.mzn";
                            
int: seq_length = 12;

enum STATE = {uninstalled,configured,running};
enum BEHAVIOR = {deploy,uninstall,interrupt,skip}; 
enum STATUS = {enabled, disabled};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|running,uninstalled,<>,uninstalled
|running,uninstalled,configured,configured
|running,<>,configured,running|];

array[STATE, BEHAVIOR] of int: costs = 
[|2,100000,100000,0
|1,1,100000,0
|100000,100000,1,0|];

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
array[1..seq_length+1] of var STATUS : configIn_status;
constraint forall (i in 1..seq_length+1) (configIn_status[i] = enabled <-> states[i] = configured \/ states[i] = running);
array[1..seq_length+1] of var STATUS : configOut_status;
constraint forall (i in 1..seq_length+1) (configOut_status[i] = enabled <-> states[i] = configured \/ states[i] = running);
array[1..seq_length+1] of var STATUS : serviceIn_status;
constraint forall (i in 1..seq_length+1) (serviceIn_status[i] = enabled <-> states[i] = running);
array[1..seq_length+1] of var STATUS : serviceOut_status;
constraint forall (i in 1..seq_length+1) (serviceOut_status[i] = enabled <-> states[i] = running);

% Init state
constraint states[1]=running;
constraint regular(sequence, transitions, running, {uninstalled,configured,running});

% Reconfiguration goals as constraints
constraint serviceOut_status[seq_length+1] = enabled; % inferred
constraint count(serviceOut_status, enabled) > 0; % inferred
constraint serviceOut_status[seq_length+1] = enabled; % inferred
constraint count(serviceOut_status, enabled) > 0; % inferred
constraint configOut_status[seq_length+1] = enabled; % inferred
constraint count(configOut_status, enabled) > 0; % inferred
constraint configOut_status[seq_length+1] = enabled; % inferred
constraint count(configOut_status, enabled) > 0; % inferred


% Goal
var int: scost;
constraint scost = sum(cost);

% Side structure for exploration strategy
array[1..seq_length] of var int: reversed_cost = array1d(1..seq_length, [cost[seq_length - i + 1] | i in 1..seq_length]);


solve 
:: int_search(reversed_cost, first_fail, indomain_min)
minimize scost;

