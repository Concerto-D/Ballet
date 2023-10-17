import time

from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType
from ballet.utils.executor_utils import empty_transition

class SysbenchMaster(Component):

    def create(self):
        self.places = [
            'uninstalled',
            'uninstalled_mysql',
            'user',
            'database',
            'suspended'
        ]
        
        self.groups = {
            'using_mysql': ['uninstalled_mysql', 'user', 'database']
        }

        self.transitions = {
            'use_mysql': ('uninstalled', 'uninstalled_mysql', 'install', 0, empty_transition),
            'to_user': ('uninstalled_mysql', 'user', 'install', 0, self.to_user),
            'to_database': ('user', 'database', 'install', 0, self.to_database),
            'suspend': ('database', 'suspended', 'suspend', 0, self.suspend),
            'restart': ('suspended', 'database', 'install', 1, self.restart)
        }

        self.dependencies = {
            'mysql': (DepType.USE, ['using_mysql']),
            'my_ip': (DepType.DATA_USE, ['to_user','to_database']),
            'user_credentials': (DepType.DATA_USE, ['to_user']),
            'db_credentials': (DepType.DATA_USE, ['to_user']),
            'sysbench_db': (DepType.PROVIDE, ['database'])
        }
        
        self.initial_place = 'uninstalled'
        
    def to_user(self):
        my_ip = self.read('my_ip')
        user_credentials = self.read('user_credentials')
        db_credentials = self.read('db_credentials')
        self.print_color("Going to user with ip \'%s\', user credentials \'%s\' and DB credentials \'%s\'"%(my_ip, user_credentials, db_credentials))
        time.sleep(0.9)

    def to_database(self):
        my_ip = self.read('my_ip')
        self.print_color("Going to database with ip \'%s\'"%my_ip)
        time.sleep(0.9)

    def suspend(self):
        time.sleep(0)

    def restart(self):
        time.sleep(0)
