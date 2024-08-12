
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Common(Component):

    def __init__(self, trans_time={}, versions=[]):
        Component.__init__(self)
        self.trans_times = trans_time
        self.versions = versions
    
    def create(self):
        self.places = [
            "initiated",
            "configured"
        ]
        if self.versions == []:
            self.places.append("deployed")
        else:
            for version in self.versions:
                self.places.append(f"deployedv{version}")
        
        self.transitions = {
            "configure": ("initiated", "configured", "deploy", 0, self.configure),
            "stop": ("deployed", "configured", "stop", 0, self.stop),
        }
        if self.versions == []:
            self.transitions["deploy"] = ("configured", "deployed", "deploy", 0, self.deploy)
            self.transitions["uninstall"] = ("deployed", "initiated", "uninstall", 0, self.uninstall)
        else:
            for version in self.versions:
                self.transitions[f"deployv{version}"] = ("configured", f"deployedv{version}", f"deployv{version}", 0, lambda _: self.deploy(version))
                self.transitions[f"uninstallv{version}"] = (f"deployedv{version}", "initiated", "uninstall", 0, self.uninstall)
            
        self.dependencies = {
            "factsservice": (DepType.USE, ["deployed", "configured"])
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

    def configure(self):
        self.print_color("begin configure")
        if "configure" in self.trans_times:
            time.sleep(self.trans_times["configure"])
        else:
            pass
        self.print_color("end configure")

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

    def uninstall(self):
        self.print_color("begin uninstall")
        if "uninstall" in self.trans_times:
            time.sleep(self.trans_times["uninstall"])
        else:
            pass
        self.print_color("end uninstall")
    