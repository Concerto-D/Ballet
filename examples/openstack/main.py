import argparse

from ballet.choerography import choerography

if __name__ == "__main__":
    # Setup arguments
    parser = argparse.ArgumentParser(prog='Ballet',
                                     description='',
                                     epilog='')
    parser.add_argument('-hs', '--host', default="localhost")
    parser.add_argument('-pf', '--port_front', type=int, default=5000)
    parser.add_argument('-pp', '--port_planner', type=int, default=5001)
    parser.add_argument('-pe', '--port_executor', type=int, default=5002)
    parser.add_argument('-ain', '-a', '--assembly_in', default=None)
    parser.add_argument('-aout', '--assembly_out', default=None)
    parser.add_argument('-i', '--inventory', default=None)
    parser.add_argument('-g', '--goal', default=None)

    args = parser.parse_args()
    host = args.host
    ports = (args.port_front, args.port_planner, args.port_executor)
    assembly_in = args.assembly_in
    assembly_out = args.assembly_out
    if assembly_out is None:
        assembly_out = assembly_in
    inventory = args.inventory
    goal = args.goal

    choerography(host, ports, assembly_in, assembly_out, inventory, goal)