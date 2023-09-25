from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Provider(Component):
    def create(self):
        self.places = [
            'uninstalled',
            'installed',
            'running'
        ]

        self.transitions = {
            'install1': ('uninstalled', 'installed', self.install1),
            'install2': ('installed', 'running', self.install2),
            'update1': ('running', 'installed', self.update1),
            'stop1': ('running', 'uninstalled', self.stop1),
            'stop2': ('installed', 'uninstalled', self.stop2)
        }

        self.dependencies = {
            'config': (DepType.PROVIDE, ['installed', 'running']),
            'service': (DepType.PROVIDE, ['running'])
        }

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
