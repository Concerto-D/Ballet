import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class MariaDB(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'mounted',
            'configured_pulled',
            'started',
            'ready'
        ]
        
        self.groups = {
        }

        self.transitions = {
            'mount': ('uninstalled', 'mounted', 'install', 0, self.mount),
            'config1': ('mounted', 'configured_pulled', 'install', 0, self.config1),
            'config2': ('mounted', 'configured_pulled', 'install', 0, self.config2),
            'pull': ('uninstalled', 'configured_pulled', 'install', 0, self.pull),
            'start': ('configured_pulled', 'started', 'install', 0, self.start),
            'go_ready': ('started', 'ready', 'install', 0, self.go_ready),
            'change_config': ('ready', 'ready', 'change_config', 0, self.change_config),
            'stop': ('ready', 'mounted', 'stop', 0, self.stop),
            'stop_uninstall': ('ready', 'mounted', 'uninstall', 0, self.stop),
            'uninstall': ('mounted', 'uninstalled', 'uninstall', 0, self.uninstall)
        }

        self.dependencies = {
            'config': (DepType.DATA_USE, ['config1', 'change_config']),
            'command': (DepType.DATA_USE, ['start']),
            'root_pw': (DepType.DATA_USE, ['start']),
            'python_full': (DepType.USE, ['start']),
            'docker': (DepType.USE, ['start']),
            'registry': (DepType.USE, ['start']),
            'mariadb': (DepType.PROVIDE, ['ready'])
        }
        
        self.initial_place = 'uninstalled'

    def __init__(self):
        self.pulled = False
        Component.__init__(self)
        
    def mount(self):
        time.sleep(0.8)
        
    def config1(self):
        time.sleep(1.3)
        
    def config2(self):
        time.sleep(1.3)
        
    def pull(self):
        if not self.pulled:
            self.print_color("Pulling image")
            time.sleep(6.5)
            self.pulled = True

    def start(self):
        time.sleep(1.4)

    def go_ready(self):
        time.sleep(5.8)

    def change_config(self):
        time.sleep(1) # TODO: check

    def stop(self):
        time.sleep(1.4)

    def uninstall(self):
        time.sleep(1.6)

    def clear_image(self):
        time.sleep(1) # TODO: check

