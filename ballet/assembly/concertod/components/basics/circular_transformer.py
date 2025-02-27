from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class CircularTransformer (Component):
    def __init__(self, n: int=1):
        self._dep = n
        super().__init__()

    def create(self):
        self.places = [
            'uninstalled',
            'configured',
            'running'
        ]

        # self.behaviors = ['deploy', 'suspend', 'stop']
        
        self.transitions = {
            'deploy1' : ('uninstalled', 'configured', 'deploy', 0, self.deploy1), # bhv deploy
            'deploy2' : ('configured', 'running', 'deploy', 0, self.deploy2), # bhv deploy
            'suspend1' : ('running', 'configured', 'suspend', 0, self.suspend1), # bhv suspend
            'stop1' : ('configured', 'uninstalled', 'stop', 0, self.stop1) # bhv stop
        }

        self.dependencies = {
            'configIn': (DepType.USE, ['configured']),
            'configOut': (DepType.PROVIDE, ['configured']),
            'serviceIn': (DepType.USE, ['running']),
            'serviceOut': (DepType.PROVIDE, ['running'])
        }
        
        self.initial_place = "uninstalled"

    def deploy1(self):
        pass

    def deploy2(self):
        pass

    def suspend1(self):
        pass

    def stop1(self):
        pass