from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Transformer(Component):
    def create(self):
        self.places = [
            'uninstalled',
            'installed',
            'configured',
            'running'
        ]

        self.transitions = {
            'install1': ('uninstalled', 'installed', 'install', 0, self.install1),
            'install2': ('installed', 'configured', 'install', 0, self.install2),
            'install3': ('configured', 'running', 'install', 0, self.install3),
            'update1': ('running', 'configured', 'update', 0, self.update1),
            'suspend1': ('running', 'installed', 'suspend', 0, self.suspend1),
            'stop1': ('running', 'uninstalled', 'stop', 0, self.stop1),
            'stop2': ('installed', 'uninstalled', 'stop', 0, self.stop2),
            'stop3': ('configured', 'uninstalled', 'stop', 0, self.stop3)
        }

        self.dependencies = {
            'configIn': (DepType.USE, ['installed', 'configured', 'running']),
            'configOut': (DepType.PROVIDE, ['configured', 'running']),
            'serviceIn': (DepType.USE, ['running']),
            'serviceOut': (DepType.PROVIDE, ['running'])
        }
        
        self.initial_place = "uninstalled"

    def install1(self):
        pass

    def install2(self):
        pass

    def install3(self):
        pass

    def update1(self):
        pass

    def suspend1(self):
        pass

    def stop1(self):
        pass

    def stop2(self):
        pass

    def stop3(self):
        pass