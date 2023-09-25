
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Facts(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "deployed"
        ]
        
        self.transitions = {
            "deploy": ("initiated", "deployed", "deploy", 0, self.deploy),
            "uninstall": ("deployed", "initiated", "uninstall", 0, self.uninstall)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"])
        }
        
        self.initial_place = "initiated"

    def deploy(self):
        self.print_color("begin deploy")
        if "deploy" in self.trans_times:
            time.sleep(self.trans_times["deploy"])
        else:
            pass
        self.print_color("end deploy")

    def uninstall(self):
        self.print_color("begin uninstall")
        if "uninstall" in self.trans_times:
            time.sleep(self.trans_times["uninstall"])
        else:
            pass
        self.print_color("end uninstall")
    