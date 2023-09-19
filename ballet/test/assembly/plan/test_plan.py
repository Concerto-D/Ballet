import unittest

from ballet.assembly.plan.plan import Plan, Wait, PushB, merge_plans
from ballet.utils import list_utils


class TestPlan(unittest.TestCase):

    def test_plan(self):
        pl1 = [PushB("comp1", "i1"), PushB("comp1", "i2"), PushB("comp1", "i3"), Wait("comp2", "j2"), Wait("comp2", "j3"), PushB("comp1", "i4")]
        pl2 = [PushB("comp2", "j1"), PushB("comp2", "j2"), PushB("comp2", "j3"), Wait("comp1", "i4")]
        pl3 = [PushB("comp3", "k1"), PushB("comp3", "k2"), Wait("comp1", "i2"), Wait("comp2", "j2"), PushB("comp3", "k3")]
        plan1 = Plan("comp1", pl1)
        plan2 = Plan("comp2", pl2)
        plan3 = Plan("comp3", pl3)
        input = [plan1, plan2, plan3]
        res = merge_plans(input).instructions()
        def idx(instr):
            return list_utils.indexOf(instr, res)
        for plan in input:  # Check partial orders
            pl = plan.instructions()
            for i in range(0, len(pl) - 1):
                assert idx(pl1[i]) < idx(pl1[i+1])
            for instr in pl:
                if instr.isWait():
                    wait: Wait = instr
                    assert idx(wait) > idx(PushB(wait.component(), wait.behavior()))


if __name__ == '__main__':
    unittest.main()