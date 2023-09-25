from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType


class ParallelUser(Component):

    def __init__(self, n: int=1):
        super().__init__()
        self._dep = n

    def create(self):
        self.places = [
            'uninstalled',
            'allocated',
            'configured',
            'running'
        ]

        self.transitions = {
            'deploy1' : ('uninstalled', 'allocated', self.deploy1), # bhv deploy
            'deploy4' : ('configured', 'running', self.deploy4), # bhv deploy
            'stop1' : ('configured', 'uninstalled', self.stop1) # bhv stop
        }

        self.dependencies = {
            'config': (DepType.PROVIDE, ['configured', 'running']),
            'service': (DepType.PROVIDE, ['running'])
        }

        for i in range(self._dep):
            self.places.append(f'sconf{i}')
            self.places.append(f'suspended{i}')
            self.transitions[f'deploy2{i}'] = ('allocated',f'sconf{i}', lambda _: self.deploy2(i))
            self.transitions[f'deploy3{i}'] = (f'sconf{i}', f'configured', lambda _: self.deploy3(i))
            self.transitions[f'suspend1{i}'] = ('running', f'suspended{i}', lambda _: self.suspend1(i))
            self.transitions[f'suspend2{i}'] = (f'suspended{i}', 'configured', lambda _: self.suspend2(i))
            self.dependencies[f'service{i}'] = (DepType.USE, ['running', f'suspended{i}'])
            self.dependencies[f'config{i}'] = (DepType.USE, [f'sconf{i}', f'configured', 'running', f'suspended{i}'])

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