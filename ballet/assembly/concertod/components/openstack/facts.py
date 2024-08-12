
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Facts(Component):

    def __init__(self, trans_time={}, versions=[]):
        Component.__init__(self)
        self.trans_times = trans_time
        self.versions = versions
    
    def create(self):
        self.places = [
            "initiated"
        ]
        if self.versions == []:
            self.places.append("deployed")
        else:
            for version in self.versions:
                self.places.append(f"deployedv{version}")
        
        self.transitions = {}
        if self.versions == []:
            self.transitions = {
                "uninstall": ("deployed", "initiated", "uninstall", 0, self.uninstall),
                "deploy": ("initiated", "deployed", "deploy", 0, self.deploy)
            }
        else:
            for version in self.versions:
                self.transitions[f"deployv{version}"] = ("initiated", f"deployedv{version}", f"deployv{version}", 0, lambda _: self.deploy(version))
                self.transitions[f"uninstallv{version}"] = (f"deployedv{version}", "initiated", "uninstall", 0, lambda _: self.uninstall)
        
        self.dependencies = {}
        if self.versions == []:
            self.dependencies["service"] = (DepType.PROVIDE, ["deployed"])
        else:
            deployed_states = []
            for version in self.versions:
                deployed_states.append(f"deployedv{version}")
                self.dependencies[f"servicev{version}"] = (DepType.PROVIDE, [f"deployedv{version}"])
            self.dependencies["service"] = (DepType.PROVIDE, deployed_states)
        
        
        self.initial_place = "initiated"

    def deploy(self, version=None):
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
    