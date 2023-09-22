from ballet.assembly.plan import Plan
from ballet.utils.io_utils import makeDir


def add_concertod_ext(x: str) -> str:
    if x[-10:] != ".concertod":
        return x + ".concertod"
    else:
        return x


def savePlan(plan: Plan, dir: str):
    if len(plan.instructions()) != 0:
        content = '\n'.join(map(lambda instr: str(instr), plan.instructions()))
        makeDir(dir)
        filename = dir + "/" + add_concertod_ext(plan.name())
        with open(filename, 'w') as f:
            f.write(content)
            f.close()


def add_metrics_ext(x):
    if x[-4:] != ".txt":
        return x + ".csv"
    else:
        return x


def saveMetrics(metrics: str, dir: str):
    makeDir(dir)
    filename = dir + "/" + add_metrics_ext("metrics")
    with open(filename, 'a') as f:
        f.write(metrics + "\n")
        f.close()
