
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Listener(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "running",
            "configured",
            "paused",
            "off"
        ]
        
        self.transitions = {
            "deploy1": ("off", "paused", "deploy", 0, self.deploy1),
            "deploy2": ("paused", "configured", "deploy", 0, self.deploy2),
            "deploy3": ("configured", "running", "deploy", 0, self.deploy3),
            "update1": ("running", "paused", "update", 0, self.update1),
            "destroy1": ("paused", "off", "destroy", 0, self.destroy1)
        }
        
        self.dependencies = {
            "rcv": (DepType.PROVIDE, ["running"]),
            "config": (DepType.PROVIDE, ["running", "configured"]),
            "sys_service": (DepType.USE, ["running", "configured"])
        }
        
        self.initial_place = "off"

    def deploy1(self):
        self.print_color("begin deploy1")
        if "deploy1" in self.trans_times:
            time.sleep(self.trans_times["deploy1"])
        else:
            pass
        self.print_color("end deploy1")

    def deploy2(self):
        self.print_color("begin deploy2")
        if "deploy2" in self.trans_times:
            time.sleep(self.trans_times["deploy2"])
        else:
            pass
        self.print_color("end deploy2")

    def deploy3(self):
        self.print_color("begin deploy3")
        if "deploy3" in self.trans_times:
            time.sleep(self.trans_times["deploy3"])
        else:
            pass
        self.print_color("end deploy3")

    def update1(self):
        self.print_color("begin update1")
        if "update1" in self.trans_times:
            time.sleep(self.trans_times["update1"])
        else:
            pass
        self.print_color("end update1")

    def destroy1(self):
        self.print_color("begin destroy1")
        if "destroy1" in self.trans_times:
            time.sleep(self.trans_times["destroy1"])
        else:
            pass
        self.print_color("end destroy1")
    