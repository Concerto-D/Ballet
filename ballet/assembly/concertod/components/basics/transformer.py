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
            'install1': ('uninstalled', 'installed', self.install1),
            'install2': ('installed', 'configured', self.install2),
            'install3': ('configured', 'running', self.install3),
            'update1': ('running', 'configured', self.update1),
            'suspend1': ('running', 'installed', self.suspend1),
            'stop1': ('running', 'uninstalled', self.stop1),
            'stop2': ('installed', 'uninstalled', self.stop2),
            'stop3': ('configured', 'uninstalled', self.stop3)
        }

        self.dependencies = {
            'config_in': (DepType.USE, ['installed', 'configured', 'running']),
            'config_out': (DepType.PROVIDE, ['configured', 'running']),
            'service_in': (DepType.USE, ['running']),
            'service_out': (DepType.PROVIDE, ['running'])
        }

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