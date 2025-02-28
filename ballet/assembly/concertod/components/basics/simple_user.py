from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType


class SimpleUser(Component):

    def __init__(self):
        super().__init__()

    def create(self):
        self.places = [
            'uninstalled',
            'allocated',
            'configured',
            'running'
        ]

        # self.behaviors = ['deploy', 'suspend', 'stop']
        
        self.transitions = {
            'deploy1' : ('uninstalled', 'allocated', 'deploy', 0, self.deploy1), # bhv deploy
            'deploy2' : ('allocated','configured', 'deploy', 0, self.deploy2),
            'deploy3' : ('configured', 'running', 'deploy', 0, self.deploy3), # bhv deploy
            'stop1' : ('configured', 'uninstalled', 'stop', 0, self.stop1), # bhv stop
            'suspend1' : ('running','configured', 'suspend', 0,self.suspend1)
        }

        self.dependencies = {
            'config': (DepType.USE, ['configured', 'running']),
            'service': (DepType.USE, ['running'])
        }
        
        self.initial_place = "uninstalled"
        self.running_place = "running"
        

    def deploy1(self):
        pass

    def deploy2(self):
        pass

    def deploy3(self):
        pass

    def suspend1(self):
        pass

    def suspend2(self):
        pass

    def deploy4(self):
        pass

    def stop1(self):
        pass