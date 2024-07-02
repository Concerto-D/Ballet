from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Provider(Component):
    def create(self):
        self.places = [
            'uninstalled',
            'installed',
            'running'
        ]
        
        # self.behaviors = ['install', 'update', 'stop']

        self.transitions = {
            'install1': ('uninstalled', 'installed', 'install', 0, self.install1),
            'install2': ('installed', 'running', 'install', 0, self.install2),
            'update1': ('running', 'installed', 'update', 0, self.update1),
            'stop1': ('running', 'uninstalled', 'stop', 0, self.stop1),
            'stop2': ('installed', 'uninstalled','stop',  0, self.stop2)
        }

        self.dependencies = {
            'config': (DepType.PROVIDE, ['installed', 'running']),
            'service': (DepType.PROVIDE, ['running'])
        }
        
        self.initial_place = "uninstalled"

    def install1(self):
        pass

    def install2(self):
        pass

    def update1(self):
        pass

    def stop1(self):
        pass

    def stop2(self):
        pass
