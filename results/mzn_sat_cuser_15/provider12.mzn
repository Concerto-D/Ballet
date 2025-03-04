include "count.mzn";
include "regular.mzn";
                            
int: seq_length = 12;

enum STATE = {uninstalled,installed,running};
enum BEHAVIOR = {install,stop,update,skip}; 
enum STATUS = {enabled, disabled};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|running,uninstalled,<>,uninstalled
|running,uninstalled,installed,installed
|running,uninstalled,installed,running|];

array[STATE, BEHAVIOR] of int: costs = 
[|2,100000,100000,0
|1,1,100000,0
|100000,1,1,0|];

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
array[1..seq_length+1] of var STATUS : config_status;
constraint forall (i in 1..seq_length+1) (config_status[i] = enabled <-> states[i] = installed \/ states[i] = running);
array[1..seq_length+1] of var STATUS : service_status;
constraint forall (i in 1..seq_length+1) (service_status[i] = enabled <-> states[i] = running);

% Init state
constraint states[1]=running;
constraint regular(sequence, transitions, running, {uninstalled,installed,running});

% Reconfiguration goals as constraints
constraint service_status[seq_length+1] = enabled; % inferred
constraint count(service_status, enabled) > 0; % inferred
constraint count(sequence, update) > 0; % goal
constraint states[seq_length+1] = running; % goal
constraint count (states, running) > 0; % goal
constraint config_status[seq_length+1] = enabled; % inferred
constraint count(config_status, enabled) > 0; % inferred


% Goal
var int: scost;
constraint scost = sum(cost);

% Side structure for exploration strategy
array[1..seq_length] of var int: reversed_cost = array1d(1..seq_length, [cost[seq_length - i + 1] | i in 1..seq_length]);


solve 
:: int_search(reversed_cost, first_fail, indomain_min)
minimize scost;

