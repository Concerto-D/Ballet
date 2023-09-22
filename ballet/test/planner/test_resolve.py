import unittest

from ballet.planner.resolve import diff_assembly


class TestResolve(unittest.TestCase):

    def test_diff_assembly(self):
        comp_in: dict[str, str] = {"c1":"t1", "c2":"t2"}
        conn_in: list[(str, str, str, str)] = [("c1","p1","c2","p2")]
        comp_out: dict[str, str] = {"c1":"t1", "c3":"t3"}
        conn_out: list[(str, str, str, str)] = [("c1","p1","c3","p3")]
        to_add, to_del, to_con, to_disc = diff_assembly(comp_in, conn_in, comp_out, conn_out)
        assert Add("c3", "t3") in to_add
        assert Add("c1", "t1") not in to_add
        assert Add("c2", "t2") not in to_add
        assert Delete("c2") in to_del
        assert Delete("c1") not in to_del
        assert Delete("c3") not in to_del
        assert Connect("c1", "p1", "c3", "p3") in to_con
        assert Connect("c1", "p1", "c2", "p2") not in to_con
        assert Disconnect("c1", "p1", "c2", "p2") in to_disc
        assert Disconnect("c1", "p1", "c3", "p3") not in to_disc

if __name__ == '__main__':
    unittest.main()
