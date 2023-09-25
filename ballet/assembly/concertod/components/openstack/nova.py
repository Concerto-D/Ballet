
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Nova(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs
    
    def create(self):
        self.places = [
            "initiated",
            "pulled",
            "ready",
            "restarted",
            "deployed",
            "interrupted"
        ]
        
        self.transitions = {
            "pull0": ("initiated", "pulled", "deploy", 0, self.pull0),
            "pull1": ("initiated", "pulled", "deploy", 0, self.pull1),
            "pull2": ("initiated", "pulled", "deploy", 0, self.pull2),
            "ready0": ("pulled", "ready", "deploy", 0, self.ready0),
            "ready1": ("pulled", "ready", "deploy", 0, self.ready1),
            "start": ("ready", "restarted", "deploy", 0, self.start),
            "deploy": ("restarted", "deployed", "deploy", 0, self.deploy),
            "cell_setup": ("pulled", "deployed", "deploy", 0, self.cell_setup),
            "interrupt": ("deployed", "interrupted", "interrupt", 0, self.interrupt),
            "pause": ("interrupted", "ready", "pause", 0, self.pause),
            "unpull": ("interrupted", "pulled", "update", 0, self.unpull),
            "uninstall": ("interrupted", "initiated", "uninstall", 0, self.uninstall)
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "mariadb_service": (DepType.USE, ["restarted", "ready", "pulled", "deployed"]),
            "keystone_service": (DepType.USE, ["restarted", "ready", "interrupted", "deployed"])
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

    def ready0(self):
        self.print_color("begin ready0")
        if "ready0" in self.trans_times:
            time.sleep(self.trans_times["ready0"])
        else:
            pass
        self.print_color("end ready0")

    def ready1(self):
        self.print_color("begin ready1")
        if "ready1" in self.trans_times:
            time.sleep(self.trans_times["ready1"])
        else:
            pass
        self.print_color("end ready1")

    def start(self):
        self.print_color("begin start")
        if "start" in self.trans_times:
            time.sleep(self.trans_times["start"])
        else:
            pass
        self.print_color("end start")

    def deploy(self):
        self.print_color("begin deploy")
        if "deploy" in self.trans_times:
            time.sleep(self.trans_times["deploy"])
        else:
            pass
        self.print_color("end deploy")

    def cell_setup(self):
        self.print_color("begin cell_setup")
        if "cell_setup" in self.trans_times:
            time.sleep(self.trans_times["cell_setup"])
        else:
            pass
        self.print_color("end cell_setup")

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

    def unpull(self):
        self.print_color("begin unpull")
        if "unpull" in self.trans_times:
            time.sleep(self.trans_times["unpull"])
        else:
            pass
        self.print_color("end unpull")

    def uninstall(self):
        self.print_color("begin uninstall")
        if "uninstall" in self.trans_times:
            time.sleep(self.trans_times["uninstall"])
        else:
            pass
        self.print_color("end uninstall")
    