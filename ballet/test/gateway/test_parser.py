import unittest

from ballet.assembly.simplified.assembly_d import DecentralizedComponentInstance
from ballet.assembly.simplified.type import openstack
from ballet.gateway.parser import GoalParser, InventoryParser, AssemblyParser
from ballet.planner.goal import BehaviorReconfigurationGoal, PortReconfigurationGoal


class TestParser(unittest.TestCase):

    def test_inventory_parser(self):
        parser = InventoryParser()
        res = parser.parse("inventory.yaml")
        assert("mdbmaster" in res)
        assert(res["mdbmaster"]["address"] == "gros-15.nancy.grid5000.fr")
        assert(res["mdbmaster"]["port_front"] == 5000)
        assert(res["mdbmaster"]["port_planner"] == 5001)
        assert(res["mdbmaster"]["port_executor"] == 5002)
        assert("mdbworker0" in res)
        assert(res["mdbworker0"]["address"] == "gros-16.nancy.grid5000.fr")
        assert(res["mdbworker0"]["port_front"] == 5006)
        assert(res["mdbworker0"]["port_planner"] == 5003)
        assert(res["mdbworker0"]["port_executor"] == 5004)
        assert("kst0" in res)
        assert(res["kst0"]["address"] == "gros-42.nancy.grid5000.fr")
        assert(res["kst0"]["port_front"] == 5008)
        assert(res["kst0"]["port_planner"] == 5005)
        assert(res["kst0"]["port_executor"] == 5006)
        assert("glance0" in res)
        assert(res["glance0"]["address"] == "gros-42.nancy.grid5000.fr")
        assert(res["glance0"]["port_front"] == 5008)
        assert(res["glance0"]["port_planner"] == 5005)
        assert(res["glance0"]["port_executor"] == 5006)

    def test_assembly_parser(self):
        parser = AssemblyParser()
        res, active, _, _ = parser.parse("assembly.yaml")
        master = DecentralizedComponentInstance("mdbmaster", openstack.mariadb_master_type())
        worker = DecentralizedComponentInstance("mdbworker0", openstack.mariadb_worker_type())
        glance = DecentralizedComponentInstance("glance0", openstack.glance_type())
        keystone = DecentralizedComponentInstance("kst0", openstack.keystone_type())
        master.connect_provide_port("service", "mdbworker0", "master_service")
        worker.connect_use_port("master_service", "mdbmaster", "service")
        worker.connect_provide_port("service", "keystone0", "mariadb_service")
        keystone.connect_use_port("mariadb_service", "mdbworker0", "service")
        worker.connect_provide_port("service", "glance0", "mariadb_service")
        glance.connect_use_port("mariadb_service", "mdbworker0", "service")
        keystone.connect_provide_port("service","glance0","keystone_service")
        glance.connect_use_port("keystone_service","keystone0","service")

        exp = set()
        exp.add(master)
        exp.add(worker)
        exp.add(glance)
        exp.add(keystone)
        assert (res == exp)

    def test_goal_parser(self):
        assembly, active, _, _ = AssemblyParser().parse("assembly.yaml")

        parser = GoalParser(assembly, active)
        res_goals, res_goals_state = parser.parse("goal.yaml")

        exp = []
        exp.append(("mdbmaster",BehaviorReconfigurationGoal("deploy")))
        exp.append(("mdbmaster",PortReconfigurationGoal("service", False, final=True)))
        exp.append(("mdbmaster", PortReconfigurationGoal("haproxy_service", True, final=True)))
        exp.append(("mdbmaster", PortReconfigurationGoal("common_service", True, final=True)))
        for (id, obj) in exp:
            assert res_goals[id].__contains__(obj), f"{id} has no {obj}"
        assert not res_goals["mdbmaster"].__contains__(PortReconfigurationGoal("service", True))

if __name__ == '__main__':
    unittest.main()
