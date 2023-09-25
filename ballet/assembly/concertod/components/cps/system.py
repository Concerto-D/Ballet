
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class System(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "deployed",
            "configured",
            "initiated"
        ]
        
        self.transitions = {
            "deploy11": ("initiated", "configured", "deploy", 0, self.deploy11),
            "deploy12": ("initiated", "configured", "deploy", 0, self.deploy12),
            "deploy13": ("initiated", "configured", "deploy", 0, self.deploy13),
            "deploy2": ("configured", "deployed", "deploy", 0, self.deploy2),
            "interrupt1": ("deployed", "configured", "interrupt", 0, self.interrupt1),
            "stop1": ("deployed", "initiated", "stop", 0, self.stop1)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "db_service": (DepType.USE, ["configured", "deployed"])
        }
        
        self.initial_place = "initiated"

    def deploy11(self):
        self.print_color("begin deploy11")
        if "deploy11" in self.trans_times:
            time.sleep(self.trans_times["deploy11"])
        else:
            pass
        self.print_color("end deploy11")

    def deploy12(self):
        self.print_color("begin deploy12")
        if "deploy12" in self.trans_times:
            time.sleep(self.trans_times["deploy12"])
        else:
            pass
        self.print_color("end deploy12")

    def deploy13(self):
        self.print_color("begin deploy13")
        if "deploy13" in self.trans_times:
            time.sleep(self.trans_times["deploy13"])
        else:
            pass
        self.print_color("end deploy13")

    def deploy2(self):
        self.print_color("begin deploy2")
        if "deploy2" in self.trans_times:
            time.sleep(self.trans_times["deploy2"])
        else:
            pass
        self.print_color("end deploy2")

    def interrupt1(self):
        self.print_color("begin interrupt1")
        if "interrupt1" in self.trans_times:
            time.sleep(self.trans_times["interrupt1"])
        else:
            pass
        self.print_color("end interrupt1")

    def stop1(self):
        self.print_color("begin stop1")
        if "stop1" in self.trans_times:
            time.sleep(self.trans_times["stop1"])
        else:
            pass
        self.print_color("end stop1")
    