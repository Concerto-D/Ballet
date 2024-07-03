
import time
    
from ballet.assembly.concertod.component import Component
from ballet.assembly.concertod.dependency import DepType

class Sensor(Component):

    def __init__(self, **kwargs):
        Component.__init__(self)
    
    def create(self):
        self.places = [
            "running",
            "charged",
            "waitingU", # Waiting update
            "waitingL", # Waiting complete loading
            "off",
            # Backup states for retrieving paused states
            "paused-running",
            "paused-running",
            "paused-charged",
            "paused-waitingU",
            "paused-waitingL"
        ]
        
        self.transitions = {
            # Deploy behavior
            "deploy1": ("off", "waitingL", "deploy", 0, self.deploy1),
            "deploy2": ("waitingL", "charged", "deploy", 0, self.deploy2),
            "deploy3": ("charged", "running", "deploy", 0, self.deploy3),
            # Interrupt behavior prior to Update behavior
            "interrupt1": ("running", "waitingU", "interrupt", 0, self.interupt1),
            "update1": ("waitingU", "charged", "update", 0, self.update1),
            # Destroy behavior
            "destroy1": ("running", "waitingL", "destroy", 0, self.destroy1),
            # Stop behavior
            "stop1": ("waitingU", "off", "stop", 0, self.stop1),
            "stop2": ("waitingL", "off", "stop", 0, self.stop2),
            # Pause behavior for harvesting 
            "pause1": ("running", "paused-running", "pause", 0, self.pause1),
            "pause2": ("charged", "paused-charged", "pause", 0, self.pause2),
            "pause3": ("waitingU", "paused-waitingU", "pause", 0, self.pause3),
            "pause4": ("waitingL", "paused-waitingL", "pause", 0, self.pause4),
            # Restore behavior
            "restore1": ("paused-running","running", "restore", 0, self.restore1),
            "restore2": ("paused-charged", "charged", "restore", 0, self.restore2),
            "restore3": ("paused-waitingU", "waitingU", "restore", 0, self.restore3),
            "restore4": ("paused-waitingL", "waitingL", "restore", 0, self.restore4),
        }
        
        self.dependencies = {
            "service": (DepType.PROVIDE, ["running"]),
            "config": (DepType.USE, ["waitingU", "waitingL", "charged"])
        }
        
        self.initial_place = "off"

    def deploy1(self):
        """
        Initialize the application
        """
        pass

    def deploy2(self):
        """
        Charge full application from received data sent by gateway.
        """
        pass

    def deploy3(self):
        """
        Start the application since all the content has been charged
        """
        pass

    def interrupt1(self):
        """
        Pause the application, in order to receive new content for updating the current app
        """
        pass

    def update1(self):
        """
        Charge partial application/data for updating current application
        """
        pass

    def destroy1(self):
        """
        Remove all the application, keeping only the bootloader on the current CPS
        """
        pass

    def stop1(self):
        """
        Turn off the application after interruption.
        Interrupt being less costly than Destroy, 
        it might be prefered if we do not mind fully cleaning CPS content before switching off
        """
        pass
    
    def stop2(self):
        """
        Turn off the application after Destroy
        """
        pass
    
    def pause1(self):
        """
        Pause the application from running state
        """
        pass
    
    def pause2(self):
        """
        Pause the application from charged state
        """
        pass
    
    def pause3(self):
        """
        Pause the application from waitingU state
        """
        pass
    
    def pause4(self):
        """
        Pause the application from waitingL state
        """
        pass
    
    def restore1(self):
        """
        Harvest energy until it has enough to move back to running state
        """
        pass
    
    def restore2(self):
        """
        Harvest energy until it has enough to move back to charged state
        """
        pass
    
    def restore3(self):
        """
        Harvest energy until it has enough to move back to waitingU state
        """
        pass
    
    def restore4(self):
        """
        Harvest energy until it has enough to move back to waitingL state
        """
        pass
