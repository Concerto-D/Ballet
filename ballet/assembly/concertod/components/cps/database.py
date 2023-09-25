
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Database(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "configured",
            "bootstrapped",
            "deployed",
            "registered"
        ]
        
        self.transitions = {
            "deploy11": ("initiated", "configured", "deploy", 0, self.deploy11),
            "deploy12": ("initiated", "configured", "deploy", 0, self.deploy12),
            "deploy2": ("configured", "bootstrapped", "deploy", 0, self.deploy2),
            "deploy3": ("bootstrapped", "deployed", "deploy", 0, self.deploy3),
            "interrupt1": ("deployed", "registered", "interrupt", 0, self.interrupt1),
            "pause1": ("registered", "bootstrapped", "pause", 0, self.pause1),
            "update": ("registered", "configured", "update", 0, self.update),
            "uninstall1": ("registered", "initiated", "uninstall", 0, self.uninstall1)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"])
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

    def interrupt1(self):
        self.print_color("begin interrupt1")
        if "interrupt1" in self.trans_times:
            time.sleep(self.trans_times["interrupt1"])
        else:
            pass
        self.print_color("end interrupt1")

    def pause1(self):
        self.print_color("begin pause1")
        if "pause1" in self.trans_times:
            time.sleep(self.trans_times["pause1"])
        else:
            pass
        self.print_color("end pause1")

    def update(self):
        self.print_color("begin update")
        if "update" in self.trans_times:
            time.sleep(self.trans_times["update"])
        else:
            pass
        self.print_color("end update")

    def uninstall1(self):
        self.print_color("begin uninstall1")
        if "uninstall1" in self.trans_times:
            time.sleep(self.trans_times["uninstall1"])
        else:
            pass
        self.print_color("end uninstall1")
    