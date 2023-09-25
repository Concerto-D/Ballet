
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Keystone(Component):

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
            "pull": ("initiated", "pulled", "deploy", 0, self.pull),
            "deploy": ("pulled", "deployed", "deploy", 0, self.deploy),
            "stop": ("deployed", "pulled", "stop", 0, self.stop),
            "turnoff": ("deployed", "initiated", "uninstall", 0, self.turnoff)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "mariadb_service": (DepType.USE, ["deployed", "pulled"])
        }
        
        self.initial_place = "initiated"

    def pull(self):
        self.print_color("begin pull")
        if "pull" in self.trans_times:
            time.sleep(self.trans_times["pull"])
        else:
            pass
        self.print_color("end pull")

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
    