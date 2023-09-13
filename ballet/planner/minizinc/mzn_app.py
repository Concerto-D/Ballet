from minizinc import Instance, Model, Solver
from ballet.utils.mzn_utils import add_mzn_ext


class MiniZincApp:

    def __init__(self, filename: str) -> None:
        mzn_filename = add_mzn_ext(filename)
        self._model =  Model(mzn_filename)
        self._instance = None
        self._result = None

    def run(self, solver: str = "gecode"):
        if self._instance is None:
            self._instance = Instance(Solver.lookup(solver), self._model)
        self._result = self._instance.solve()
        return self

    def result(self):
        return self._result