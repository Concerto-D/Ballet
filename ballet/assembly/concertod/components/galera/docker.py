import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType
from ballet.utils.executor_utils import empty_transition

class Docker(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'uninstalled_apt_utils',
            'repo_key',
            'repo',
            'installed'
        ]
        
        self.groups = {
            'using_apt_utils': ['uninstalled_apt_utils', 'repo_key', 'repo', 'installed']
        }

        self.transitions = {
            'use_apt_utils': ('uninstalled', 'uninstalled_apt_utils', 'install', 0, empty_transition),
            'to_repo_key': ('uninstalled_apt_utils', 'repo_key', 'install', 0, self.to_repo_key),
            'to_repo': ('repo_key', 'repo', 'install', 0, self.to_repo),
            'to_installed': ('repo', 'installed', 'install', 0, self.to_installed),
            'change_config': ('installed', 'installed', 'change_config', 0, self.change_config)
        }

        self.dependencies = {
            'config': (DepType.DATA_USE, ['change_config']),
            'apt_utils': (DepType.USE, ['using_apt_utils']),
            'docker': (DepType.PROVIDE, ['installed'])
        }
        
        self.initial_place = 'uninstalled'
        
    def to_repo_key(self):
        time.sleep(3)

    def to_repo(self):
        time.sleep(3.2)

    def to_installed(self):
        time.sleep(24)

    def change_config(self):
        self.print_color("Changing config to:\n%s"%self.read('config'))
        time.sleep(3)

