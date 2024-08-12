
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Neutron(Component):

    def __init__(self, trans_time={}, versions=[]):
        Component.__init__(self)
        self.trans_times = trans_time
        self.versions = versions
    
    def create(self):
        self.places = [
            "initiated",
            "pulled"
        ]
        if self.versions == []:
            self.places.append("deployed")
        else:
            for version in self.versions:
                self.places.append(f"deployedv{version}")
        
        self.transitions = {
            "pull0": ("initiated", "pulled", "deploy", 0, self.pull0),
            "pull1": ("initiated", "pulled", "deploy", 0, self.pull1),
            "pull2": ("initiated", "pulled", "deploy", 0, self.pull2)
        }
        
        if self.versions == []:
            self.transitions["deploy"] = ("pulled", "deployed", "deploy", 0, self.deploy)
            self.transitions["stop"] = ("deployed", "pulled", "stop", 0, self.stop),
            self.transitions["turnoff"] = ("deployed", "initiated", "uninstall", 0, self.turnoff)
        else:
            for version in self.versions:
                self.transitions[f"deployv{version}"] = ("pulled", f"deployedv{version}", f"deployv{version}", 0, lambda _: self.deploy(version))
                self.transitions[f"stopv{version}"] = (f"deployedv{version}", "pulled", "stop", 0, self.stop),
                self.transitions[f"turnoffv{version}"] = (f"deployedv{version}", "initiated", "uninstall", 0, self.turnoff)
        
        
        
        self.dependencies = {
            "mariadbservice": (DepType.USE, ["deployed", "pulled"]),
            "keystoneservice": (DepType.USE, ["deployed", "pulled"])
        }
        if self.versions == []:
            self.dependencies["service"] = (DepType.PROVIDE, ["deployed"])
        else:
            deployed_states = []
            for version in self.versions:
                deployed_states.append(f"deployedv{version}")
                self.dependencies[f"servicev{version}"] = (DepType.PROVIDE, [f"deployedv{version}"])
            self.dependencies["service"] = (DepType.PROVIDE, deployed_states)
        
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

    def deploy(self, version=None):
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
    