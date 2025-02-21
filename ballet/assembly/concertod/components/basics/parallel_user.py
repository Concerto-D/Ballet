from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType


class ParallelUser(Component):

    def __init__(self, n: int=1):
        self._dep = n
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
            'deploy4' : ('configured', 'running', 'deploy', 0, self.deploy4), # bhv deploy
            'stop1' : ('configured', 'uninstalled', 'stop', 0, self.stop1) # bhv stop
        }

        self.dependencies = {
            'config': (DepType.PROVIDE, ['configured', 'running']),
            'service': (DepType.PROVIDE, ['running'])
        }

        if self._dep == 0:
            self.transitions['deploy2'] = ('allocated','configured', 'deploy', 0, lambda _: self.deploy2(-1))
            self.transitions['suspend1'] = ('running','configured', 'suspend', 0, lambda _: self.suspend1(-1))
        
        for i in range(self._dep):
            self.places.append(f'sconf{i}')
            self.places.append(f'suspended{i}')
            self.transitions[f'deploy2{i}'] = ('allocated',f'sconf{i}', 'deploy', 0, lambda _: self.deploy2(i))
            self.transitions[f'deploy3{i}'] = (f'sconf{i}', f'configured', 'deploy', 0, lambda _: self.deploy3(i))
            self.transitions[f'suspend1{i}'] = ('running', f'suspended{i}', 'suspend', 0, lambda _: self.suspend1(i))
            self.transitions[f'suspend2{i}'] = (f'suspended{i}', 'configured', 'suspend', 0, lambda _: self.suspend2(i))
            # self.dependencies[f'service{i}'] = (DepType.USE, ['running', f'suspended{i}'])
            # self.dependencies[f'config{i}'] = (DepType.USE, [f'sconf{i}', f'configured', 'running', f'suspended{i}'])
        
        self.initial_place = "uninstalled"
        

    def deploy1(self):
        pass

    def deploy2(self, i: int):
        pass

    def deploy3(self, i: int):
        pass

    def suspend1(self, i: int):
        pass

    def suspend2(self, i: int):
        pass

    def deploy4(self):
        pass

    def stop1(self):
        pass