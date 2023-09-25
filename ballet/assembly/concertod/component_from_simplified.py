from ballet.assembly.simplified.assembly import ComponentType
from ballet.assembly.simplified.type.cps import *
from ballet.utils import io_utils


def generate(input: ComponentType, package: str):
    test = io_utils.makeDir(f"components/{package}")
    if test:
        io_utils.touch(f"components/{package}/__init__.py")
    classname = input.name().replace("_", " ").title().replace(" ", "")
    places = map(lambda p: "            " + "\"" + p.name() + "\"", input.places())
    transitions = []
    func_to_make = []
    for behavior in input.behaviors():
        for (name, transition) in behavior.transitions_has_dict().items():
            func_to_make.append(name)
            transitions.append(f"            \"{name}\": (\"{transition.source().name()}\", "
                               f"\"{transition.destination()[0].name()}\", \"{behavior.name()}\", "
                               f"{transition.destination()[1]}, self.{name})")
    groups = []
    dependencies = []
    for port in input.ports():
        bounded_places = ", ".join(map(lambda p: f"\"{p.name()}\"", port.bound_places()))
        type_port = "DepType.PROVIDE" if port.is_provide_port() else "DepType.USE"
        dependencies.append(f"            \"{port.name()}\": ({type_port}, [{bounded_places}])")

    functions = []
    for foo in func_to_make:
        functions.append(f"""
    def {foo}(self):
        self.print_color(\"begin {foo}\")
        if \"{foo}\" in self.trans_times:
            time.sleep(self.trans_times[\"{foo}\"])
        else:
            pass
        self.print_color(\"end {foo}\")""")
    str_places = ',\n'.join(places)
    str_transitions = ',\n'.join(transitions)
    str_dependencies = ',\n'.join(dependencies)
    str_functions = '\n'.join(functions)
    res = f"""
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class {classname}(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
{str_places}
        ]
        
        self.transitions = {{
{str_transitions}
        }}
        
        self.dependencies = {{
{str_dependencies}
        }}
        
        self.initial_place = "{input.initial_place().name()}"
{str_functions}
    """
    filename = input.name().lower().replace(" ", "_")
    io_utils.write(f"components/{package}/{filename}.py", res)
    return res


if __name__ == "__main__":
    from ballet.assembly.simplified.type.openstack import *
    tt = [system_type(), listener_type(), sensor_type(), database_type()]
    for mytype in tt:
        generate(mytype, "cps")



