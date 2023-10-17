import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Python(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'vanilla',
            'full'
        ]

        self.transitions = {
            'install_python': ('uninstalled', 'vanilla', 'install', 0, self.install_python),
            'install_libs': ('vanilla', 'full', 'install', 0, self.install_libs)
        }
        
        self.groups = {
            'providing_python': ['vanilla', 'full']
        }

        self.dependencies = {
            'python': (DepType.PROVIDE, ['providing_python']),
            'python_full': (DepType.PROVIDE, ['full'])
        }
        
        self.initial_place = 'uninstalled'
        

    def install_python(self):
        time.sleep(24)

    def install_libs(self):
        time.sleep(16)

