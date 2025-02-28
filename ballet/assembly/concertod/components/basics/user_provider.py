from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class UserProvider (Component):
    
    def create(self):
        self.places = ["uninstalled", "configured", "running"]
        self.transitions = {
            'config' : ('uninstalled', 'configured', 'deploy', 0, self.config), # bhv deploy
            'deploy' : ('configured', 'running', 'deploy', 0, self.deploy), # bhv deploy
            'interrupt' : ('running', 'configured', 'interrupt', 0, self.interrupt),
            'uninstall' : ('configured', 'uninstalled', 'uninstall', 0, self.uninstall)
        }
        
        self.dependencies = {
            'configIn': (DepType.USE, ['configured']),
            'configOut': (DepType.PROVIDE, ['configured']),
            'serviceIn': (DepType.USE, ['running']),
            'serviceOut': (DepType.PROVIDE, ['running'])
            }
        
        self.initial_place = "uninstalled"
        self.running_place = "running"
        
    def config(self):
        pass
        
    def deploy(self):
        pass
        
    def interrupt(self):
        pass
        
    def uninstall(self):
        pass