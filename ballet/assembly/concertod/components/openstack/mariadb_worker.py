
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class MariadbWorker(Component):

    def __init__(self, trans_time={}, versions=[]):
        self.trans_times = trans_time
        self.versions = versions
        super().__init__()
    
    def create(self):
        self.places = [
            "initiated",
            "configured",
            "bootstrapped",
            "restarted",
            "registered",
            "interrupted"
        ]
        if self.versions == []:
            self.places.append("deployed")
        else:
            for version in self.versions:
                self.places.append(f"deployedv{version}")
        
        self.transitions = {
            "configure0": ("initiated", "configured", "deploy", 0, self.configure0),
            "configure1": ("initiated", "configured", "deploy", 0, self.configure1),
            "bootstrap": ("configured", "bootstrapped", "deploy", 0, self.bootstrap),
            "start": ("bootstrapped", "restarted", "deploy", 0, self.start),
            "register": ("restarted", "registered", "deploy", 0, self.register),
            "pause": ("interrupted", "bootstrapped", "pause", 0, self.pause),
            "update": ("interrupted", "configured", "update", 0, self.update),
            "uninstall": ("interrupted", "initiated", "uninstall", 0, self.uninstall)
        }
        if self.versions == []:
            self.transitions["deploy"] = ("registered", "deployed", "deploy", 0, self.deploy)
            self.transitions["interrupt"] = ("deployed", "interrupted", "interrupt", 0, self.interrupt)
        else:
            for version in self.versions:
                self.transitions[f"deployv{version}"] = ("registered", f"deployedv{version}", f"deployv{version}", 0, lambda _: self.deploy(version))
                self.transitions[f"interruptv{version}"] = (f"deployedv{version}", "interrupted", "interrupt", 0, self.interrupt)
        
        
        self.dependencies = {
            "haproxyservice": (DepType.USE, ["restarted", "bootstrapped"]),
        }
        if self.versions == []:
            self.dependencies["service"] = (DepType.PROVIDE, ["deployed"])
            self.dependencies["commonservice"] = (DepType.USE, ["registered", "restarted", "interrupted", "deployed"])
            self.dependencies["masterservice"] = (DepType.USE, ["registered", "bootstrapped", "deployed", "restarted", "interrupted"])
        else:
            deployed_states = []
            for version in self.versions:
                deployed_states.append(f"deployedv{version}")
                self.dependencies[f"servicev{version}"] = (DepType.PROVIDE, [f"deployedv{version}"])
                self.dependencies[f"commonservicev{version}"] = (DepType.USE, [f"deployedv{version}", "interrupted", "restarted", "registered"])
                self.dependencies[f"masterservicev{version}"] = (DepType.USE, [f"deployedv{version}", "bootstrapped", "interrupted", "restarted", "registered"])
            self.dependencies["service"] = (DepType.PROVIDE, deployed_states)
            self.dependencies["commonservice"] = (DepType.USE, deployed_states + ["registered", "restarted", "interrupted"])
            self.dependencies["masterservice"] = (DepType.USE, deployed_states + ["registered", "bootstrapped", "restarted", "interrupted"])
        
        self.initial_place = "initiated"

    def configure0(self):
        self.print_color("begin configure0")
        if "configure0" in self.trans_times:
            time.sleep(self.trans_times["configure0"])
        else:
            pass
        self.print_color("end configure0")

    def configure1(self):
        self.print_color("begin configure1")
        if "configure1" in self.trans_times:
            time.sleep(self.trans_times["configure1"])
        else:
            pass
        self.print_color("end configure1")

    def bootstrap(self):
        self.print_color("begin bootstrap")
        if "bootstrap" in self.trans_times:
            time.sleep(self.trans_times["bootstrap"])
        else:
            pass
        self.print_color("end bootstrap")

    def start(self):
        self.print_color("begin start")
        if "start" in self.trans_times:
            time.sleep(self.trans_times["start"])
        else:
            pass
        self.print_color("end start")

    def register(self):
        self.print_color("begin register")
        if "register" in self.trans_times:
            time.sleep(self.trans_times["register"])
        else:
            pass
        self.print_color("end register")

    def deploy(self, version=None):
        self.print_color("begin deploy")
        if "deploy" in self.trans_times:
            time.sleep(self.trans_times["deploy"])
        else:
            pass
        self.print_color("end deploy")

    def interrupt(self):
        self.print_color("begin interrupt")
        if "interrupt" in self.trans_times:
            time.sleep(self.trans_times["interrupt"])
        else:
            pass
        self.print_color("end interrupt")

    def pause(self):
        self.print_color("begin pause")
        if "pause" in self.trans_times:
            time.sleep(self.trans_times["pause"])
        else:
            pass
        self.print_color("end pause")

    def update(self):
        self.print_color("begin update")
        if "update" in self.trans_times:
            time.sleep(self.trans_times["update"])
        else:
            pass
        self.print_color("end update")

    def uninstall(self):
        self.print_color("begin uninstall")
        if "uninstall" in self.trans_times:
            time.sleep(self.trans_times["uninstall"])
        else:
            pass
        self.print_color("end uninstall")
    