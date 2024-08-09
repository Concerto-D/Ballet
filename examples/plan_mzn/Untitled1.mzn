enum STATE = {initiated, configured, deployed};
enum BEHAVIOR = {deploy, stop, uninstall, skip};
enum STATUS = {enabled, disabled};

array[STATE, BEHAVIOR] of opt STATE: transitions = 
[|deployed,<>,initiated,initiated
|deployed,configured,<>,configured
|deployed,configured,initiated,deployed|];

array[1..10] of var int: cost;

function var int: fcost(var STATE: state, var BEHAVIOR: behavior) =
  if state = initiated /\ behavior = deploy then
    2
  elseif state = configured /\ behavior = deploy then
    1
  elseif state = deployed /\ (behavior = stop \/ behavior = uninstall) then
    1
  else 
    0 % Default cost for skip
  endif;

array[1..10] of var BEHAVIOR: sequence;
array[1..10+1] of var STATE: states;
array[1..10+1] of var STATUS : service_status;
array[1..10+1] of var STATUS : facts_service_status;

constraint states[1]=initiated;
constraint forall (i in 1..10) (
  states[i + 1] = transitions[states[i], sequence[i]] /\
  service_status[i] = enabled <-> states[i] = deployed /\
  facts_service_status[i] = enabled <-> (states[i] = configured \/ states[i] = deployed) /\
  (sequence[i] != skip \/ sequence[i+1] = skip)
);

constraint states[10 + 1] = deployed;
constraint sum(i in 1..10+1)(bool2int(states[i] = deployed)) > 0;

constraint forall (i in 1..10) (
  cost[i] = fcost(states[i], sequence[i])
);

solve minimize sum(cost);
