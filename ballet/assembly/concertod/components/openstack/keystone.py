
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Keystone(Component):

    def __init__(self, trans_time={}, versions=[]):
        self.trans_times = trans_time
        self.versions = versions
        super().__init__()
    
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
            "pull": ("initiated", "pulled", "deploy", 0, self.pull)
        }
        if self.versions == []:
            self.transitions["deploy"] = ("pulled", "deployed", "deploy", 0, self.deploy)
            self.transitions["stop"] = ("deployed", "pulled", "stop", 0, self.stop)
            self.transitions["turnoff"] = ("deployed", "initiated", "uninstall", 0, self.turnoff)
        else:
            for version in self.versions:
                self.transitions[f"deployv{version}"] = ("pulled", f"deployedv{version}", f"deployv{version}", 0, lambda _: self.deploy(version))
                self.transitions[f"stopv{version}"] = (f"deployedv{version}", "pulled", "stop", 0, self.stop)
                self.transitions[f"turnoffv{version}"] = (f"deployedv{version}", "initiated", "uninstall", 0, self.turnoff)
        
        
        self.dependencies = {}
        if self.versions == []:
            self.dependencies["service"] = (DepType.PROVIDE, ["deployed"])
            self.dependencies["mariadbservice"] = (DepType.USE, ["deployed", "pulled"])
        else:
            all_deployed_states = []
            for version in self.versions:
                all_deployed_states.append(f"deployedv{version}")
                self.dependencies[f"servicev{version}"] = (DepType.PROVIDE, [f"deployedv{version}"])
                self.dependencies[f"mariadbservicev{version}"] = (DepType.USE, [f"deployedv{version}", "pulled"])
            self.dependencies["service"] = (DepType.PROVIDE, all_deployed_states)
            self.dependencies["mariadbservice"] = (DepType.USE, all_deployed_states + ["pulled"])
        
        self.initial_place = "initiated"

    def pull(self):
        self.print_color("begin pull")
        if "pull" in self.trans_times:
            time.sleep(self.trans_times["pull"])
        else:
            pass
        self.print_color("end pull")

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
    