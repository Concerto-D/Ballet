
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Neutron(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "pulled",
            "deployed"
        ]
        
        self.transitions = {
            "pull0": ("initiated", "pulled", "deploy", 0, self.pull0),
            "pull1": ("initiated", "pulled", "deploy", 0, self.pull1),
            "pull2": ("initiated", "pulled", "deploy", 0, self.pull2),
            "deploy": ("pulled", "deployed", "deploy", 0, self.deploy),
            "stop": ("deployed", "pulled", "stop", 0, self.stop),
            "turnoff": ("deployed", "initiated", "uninstall", 0, self.turnoff)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "mariadb_service": (DepType.USE, ["deployed", "pulled"]),
            "keystone_service": (DepType.USE, ["deployed", "pulled"])
        }
        
        self.initial_place = "initiated"

    def pull0(self):
        self.print_color("begin pull0")
        if "pull0" in self.trans_times:
            time.sleep(self.trans_times["pull0"])
        else:
            pass
        self.print_color("end pull0")

    def pull1(self):
        self.print_color("begin pull1")
        if "pull1" in self.trans_times:
            time.sleep(self.trans_times["pull1"])
        else:
            pass
        self.print_color("end pull1")

    def pull2(self):
        self.print_color("begin pull2")
        if "pull2" in self.trans_times:
            time.sleep(self.trans_times["pull2"])
        else:
            pass
        self.print_color("end pull2")

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

    def turnoff(self):
        self.print_color("begin turnoff")
        if "turnoff" in self.trans_times:
            time.sleep(self.trans_times["turnoff"])
        else:
            pass
        self.print_color("end turnoff")
    