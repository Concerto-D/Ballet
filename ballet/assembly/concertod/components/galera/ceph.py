import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType
from ballet.utils.executor_utils import empty_transition


class Ceph(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'installed',
            'configured',
            'running',
            'rdb_map_pl'
        ]

        self.transitions = {
            'install': ('uninstalled', 'installed', 'install', 0, self.install),
            'configure_conf': ('installed', 'configured', 'install', 0, self.configure_conf),
            'configure': ('installed', 'configured', 'install', 0, self.configure),
            'run': ('configured', 'running', 'install', 0, self.run),
            'add_rdb_mapping': ('running', 'running', 'add_rdb_mapping', 0, self.add_rdb_mapping),
            'get_rdb_mapping': ('running', 'rdb_map_pl', 'get_rdb_mapping', 0, self.get_rdb_mapping),
            'get_rdb_mapping2': ('rdb_map_pl', 'running', 'get_rdb_mapping', 0, empty_transition)
        }

        self.dependencies = {
            'config': (DepType.DATA_USE, ['configure_conf']),
            'rdb': (DepType.DATA_USE, ['add_rdb_mapping']),
            'id': (DepType.DATA_USE, ['add_rdb_mapping', 'get_rdb_mapping']),
            'rdb_map': (DepType.DATA_PROVIDE, ['rdb_map_pl']),
            'ceph': (DepType.PROVIDE, ['running'])
        }
        
        self.initial_place = 'uninstalled'
        

    def install(self):
        time.sleep(20.6)

    def configure_conf(self):
        self.print_color("Using config:\n%s"%self.read('config'))
        time.sleep(1.2)

    def configure(self):
        time.sleep(1.1)

    def run(self):
        time.sleep(0.8)

    def add_rdb_mapping(self):
        self.print_color("Adding rdb mapping (id: %s): %s"%(self.read('id'),self.read('rdb')))
        time.sleep(0.8)

    def get_rdb_mapping(self):
        rdb_map = "PLACEHOLDER"
        self.print_color("Writing rdb map (id: %s) to output port: %s"%(self.read('id'),rdb_map))
        self.write("rdb_map",rdb_map)
        time.sleep(0.7)

