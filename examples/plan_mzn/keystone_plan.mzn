include "regular.mzn";
include "count.mzn";
enum STATE = {initiated, pulled, deployed};
enum BEHAVIOR = {deploy, stop, uninstall, skip};
enum STATUS = {enabled, disabled};
array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|deployed,<>,initiated,initiated
|deployed,pulled,<>,pulled
|deployed,pulled,initiated,deployed|];
array[1..10] of var BEHAVIOR: sequence;
array[1..10+1] of var STATE: states;
constraint forall (i in 1..10) (states[i + 1] = transitions[states[i], sequence[i]]);
array[1..10+1] of var STATUS : service_status;
constraint forall (i in 1..10+1) (service_status[i] = enabled <->  states[i] = deployed);
array[1..10+1] of var STATUS : mariadb_service_status;
constraint forall (i in 1..10+1) (mariadb_service_status[i] = enabled <->  states[i] = deployed \/  states[i] = pulled);
constraint states[1]=initiated;
constraint regular(sequence, transitions, initiated, {initiated,pulled,deployed});
constraint forall (i in 1..10 - 1) (sequence[i] = skip -> sequence[i+1] = skip);

constraint states[10 + 1] = deployed;
constraint count (v in states) (v = deployed) > 0;



array[1..10] of var int: cost;
constraint forall (i in 1..10) (cost[i] = fcost(states[i], sequence[i]));
function var int: fcost(var STATE: state, var BEHAVIOR: behavior) =
if state = initiated /\ behavior = deploy then
2
elseif state = pulled /\ behavior = deploy then
1
elseif state = deployed /\ behavior = stop then
1
elseif state = deployed /\ behavior = uninstall then
1
elseif state = initiated /\ behavior = skip then
0
elseif state = pulled /\ behavior = skip then
0
elseif state = deployed /\ behavior = skip then
0
else 
1000000
endif;

solve minimize sum(cost);