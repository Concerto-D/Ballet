include "regular.mzn";
include "count.mzn";
enum STATE = {initiated, configured, bootstrapped, deployed, interrupted};
enum BEHAVIOR = {deploy, interrupt, pause, update, uninstall, skip};
enum STATUS = {enabled, disabled};
array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|deployed,<>,<>,<>,initiated,initiated
|deployed,<>,<>,configured,<>,configured
|deployed,<>,bootstrapped,<>,<>,bootstrapped
|deployed,interrupted,<>,<>,<>,deployed
|<>,interrupted,bootstrapped,configured,initiated,interrupted|];
array[1..10] of var BEHAVIOR: sequence;
array[1..10+1] of var STATE: states;
constraint forall (i in 1..10) (states[i + 1] = transitions[states[i], sequence[i]]);
array[1..10+1] of var STATUS : service_status;
constraint forall (i in 1..10+1) (service_status[i] = enabled <->  states[i] = deployed);
array[1..10+1] of var STATUS : haproxy_service_status;
constraint forall (i in 1..10+1) (haproxy_service_status[i] = enabled <->  states[i] = bootstrapped);
array[1..10+1] of var STATUS : common_service_status;
constraint forall (i in 1..10+1) (common_service_status[i] = enabled <->  states[i] = interrupted \/  states[i] = deployed);
constraint states[1]=initiated;
constraint regular(sequence, transitions, initiated, {initiated,configured,bootstrapped,deployed,interrupted});
constraint forall (i in 1..10 - 1) (sequence[i] = skip -> sequence[i+1] = skip);

constraint states[10 + 1] = deployed;
constraint count (v in states) (v = deployed) > 0;



array[1..10] of var int: cost;
constraint forall (i in 1..10) (cost[i] = fcost(states[i], sequence[i]));
function var int: fcost(var STATE: state, var BEHAVIOR: behavior) =
if state = initiated /\ behavior = deploy then
60
elseif state = configured /\ behavior = deploy then
55
elseif state = bootstrapped /\ behavior = deploy then
29
elseif state = deployed /\ behavior = interrupt then
1
elseif state = interrupted /\ behavior = pause then
1
elseif state = interrupted /\ behavior = update then
2
elseif state = interrupted /\ behavior = uninstall then
5
elseif state = initiated /\ behavior = skip then
0
elseif state = configured /\ behavior = skip then
0
elseif state = bootstrapped /\ behavior = skip then
0
elseif state = deployed /\ behavior = skip then
0
elseif state = interrupted /\ behavior = skip then
0
else 
1000000
endif;

solve minimize sum(cost);