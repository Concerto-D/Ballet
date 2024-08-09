int: seq_length = 12;

enum STATE = {initiated,configured,deployed};
enum BEHAVIOR = {deploy,stop,uninstall,skip}; 
enum STATUS = {enabled, disabled};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|deployed,<>,<>,initiated
|deployed,<>,<>,configured
|<>,configured,initiated,deployed|];

array[STATE, BEHAVIOR] of int: costs = 
[|2,1000000,1000000,0
|1,1000000,1000000,0
|1000000,1,1,0|];

% Captured variables
array[1..seq_length] of var BEHAVIOR: sequence;
array[1..seq_length+1] of var STATE: states;
array[1..seq_length] of var int: cost;

constraint forall (i in 1..seq_length) (states[i + 1] = transitions[states[i], sequence[i]]);
constraint forall (i in 1..seq_length-1) (sequence[i] = skip -> sequence[i+1] = skip);
constraint forall (i in 1..seq_length) (cost[i] = costs[states[i],sequence[i]]);

% Ports' statuses
array[1..seq_length+1] of var STATUS : service_status;
constraint forall (i in 1..seq_length+1) (service_status[i] = enabled <-> states[i] = deployed);
array[1..seq_length+1] of var STATUS : facts_service_status;
constraint forall (i in 1..seq_length+1) (facts_service_status[i] = enabled <-> states[i] = configured \/ states[i] = deployed);

% Init state
constraint states[1]=initiated;

% Reconfiguration goals as constraints
var int: count_deploy;
constraint count_deploy = sum(b in sequence) (b = deploy);
constraint count_deploy > 0;
constraint states[seq_length+1] = deployed;
var int: count_deployed;
constraint count_deployed = sum(s in states) (s = deployed);
constraint count_deployed > 0;
constraint service_status[seq_length+1] = disabled;
var int: count_service_status_disabled;
constraint count_service_status_disabled = sum(s in service_status) (s = disabled);
constraint count_service_status_disabled > 0;

% Goal
var int: scost;
constraint scost = sum(cost);
solve minimize scost;

