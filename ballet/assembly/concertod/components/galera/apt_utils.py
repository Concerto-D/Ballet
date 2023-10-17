import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType


class AptUtils(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'installed'
        ]

        self.transitions = {
            'install': ('uninstalled', 'installed', 'install', 0, self.install)
        }

        self.dependencies = {
            'apt_utils': (DepType.PROVIDE, ['installed'])
        }
        
        self.initial_place = 'uninstalled'
        

    def install(self):
        time.sleep(12.5)

