
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Common(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "configured",
            "deployed"
        ]
        
        self.transitions = {
            "configure": ("initiated", "configured", "deploy", 0, self.configure),
            "deploy": ("configured", "deployed", "deploy", 0, self.deploy),
            "stop": ("deployed", "configured", "stop", 0, self.stop),
            "uninstall": ("deployed", "initiated", "uninstall", 0, self.uninstall)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "facts_service": (DepType.USE, ["deployed", "configured"])
        }
        
        self.initial_place = "initiated"

    def configure(self):
        self.print_color("begin configure")
        if "configure" in self.trans_times:
            time.sleep(self.trans_times["configure"])
        else:
            pass
        self.print_color("end configure")

    def deploy(self):
        self.print_color("begin deploy")
        if "deploy" in self.trans_times:
            time.sleep(self.trans_times["deploy"])
        else:
            pass
        self.print_color("end deploy")

    def stop(self):
        self.print_color("begin stop")
        if "stop" in self.trans_times:
            time.sleep(self.trans_times["stop"])
        else:
            pass
        self.print_color("end stop")

    def uninstall(self):
        self.print_color("begin uninstall")
        if "uninstall" in self.trans_times:
            time.sleep(self.trans_times["uninstall"])
        else:
            pass
        self.print_color("end uninstall")
    