
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Sensor(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "running",
            "configured",
            "installed",
            "provisioned",
            "off"
        ]
        
        self.transitions = {
            "deploy11": ("off", "provisioned", "deploy", 0, self.deploy11),
            "deploy12": ("off", "provisioned", "deploy", 0, self.deploy12),
            "deploy13": ("off", "provisioned", "deploy", 0, self.deploy13),
            "deploy2": ("provisioned", "installed", "deploy", 0, self.deploy2),
            "deploy3": ("installed", "configured", "deploy", 0, self.deploy3),
            "deploy4": ("configured", "running", "deploy", 0, self.deploy4),
            "pause1": ("running", "provisioned", "pause", 0, self.pause1),
            "stop1": ("provisioned", "off", "stop", 0, self.stop1)
        }
        
        self.dependencies = {
            "rcv_service": (DepType.USE, ["running", "configured"]),
            "config_service": (DepType.USE, ["running", "installed", "configured"])
        }
        
        self.initial_place = "off"

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

    def deploy3(self):
        self.print_color("begin deploy3")
        if "deploy3" in self.trans_times:
            time.sleep(self.trans_times["deploy3"])
        else:
            pass
        self.print_color("end deploy3")

    def deploy4(self):
        self.print_color("begin deploy4")
        if "deploy4" in self.trans_times:
            time.sleep(self.trans_times["deploy4"])
        else:
            pass
        self.print_color("end deploy4")

    def pause1(self):
        self.print_color("begin pause1")
        if "pause1" in self.trans_times:
            time.sleep(self.trans_times["pause1"])
        else:
            pass
        self.print_color("end pause1")

    def stop1(self):
        self.print_color("begin stop1")
        if "stop1" in self.trans_times:
            time.sleep(self.trans_times["stop1"])
        else:
            pass
        self.print_color("end stop1")
    