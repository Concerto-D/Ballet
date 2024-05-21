from gossip.cost_regular import CostRegular, StateConstraint, PortConstraint, TransitionConstraint, FindMUSException

cr = CostRegular(["initiated","configured","deployed"], 
                 ["deploy","stop","uninstall"], 
                 {"initiated" : {"deploy":"deployed"},
                  "configured": {"deploy":"deployed"},
                  "deployed": {"stop":"configured", "uninstall":"initiated"}}, 
                 {"initiated" : {"deploy":2},
                  "configured": {"deploy":1},
                  "deployed": {"stop":1, "uninstall":1}}, 
                 "initiated",
                 {"service":["deployed"], "facts_service":["configured", "deployed"]},
                 {StateConstraint("deployed", final=True),
                  PortConstraint("service", "disabled", final=True),
                  TransitionConstraint("deploy")
                  })


cr.solve_choco(print_model=True)

# try:
#     res = cr.solve(mode="minizinc", print_model=False, write_file=True)
#     print("states = ", res.solution.states)
#     print("sequence = ", res.solution.sequence)
#     print("service = ", res.solution.service_status)
#     print("facts_service = ", res.solution.facts_service_status)
# except FindMUSException as e:
#     # print(e)
#     print("MUS:",e.mus)
#     print("Brief:",e.brief)
#     print('\n'.join(e.traces.split(";")))
