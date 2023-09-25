
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class MariadbMaster(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "configured",
            "bootstrapped",
            "restarted",
            "registered",
            "deployed",
            "interrupted"
        ]
        
        self.transitions = {
            "configure0": ("initiated", "configured", "deploy", 0, self.configure0),
            "configure1": ("initiated", "configured", "deploy", 0, self.configure1),
            "bootstrap": ("configured", "bootstrapped", "deploy", 0, self.bootstrap),
            "start": ("bootstrapped", "restarted", "deploy", 0, self.start),
            "register": ("restarted", "registered", "deploy", 0, self.register),
            "deploy": ("registered", "deployed", "deploy", 0, self.deploy),
            "interrupt": ("deployed", "interrupted", "interrupt", 0, self.interrupt),
            "pause": ("interrupted", "bootstrapped", "pause", 0, self.pause),
            "update": ("interrupted", "configured", "update", 0, self.update),
            "uninstall": ("interrupted", "initiated", "uninstall", 0, self.uninstall)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "haproxy_service": (DepType.USE, ["bootstrapped", "restarted"]),
            "common_service": (DepType.USE, ["interrupted", "deployed", "restarted", "registered"])
        }
        
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

    def deploy(self):
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
    