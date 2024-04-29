from abc import ABC, abstractmethod

class Acknowledgement(ABC):
    
    def __int__(self):
        pass
    
    @abstractmethod
    def accept(): 
        pass
    
    
class AckAccept(Acknowledgement):
    
    def __int__(self):
        pass
    
    def accept(): 
        return True
    
    
class AckRefuse(Acknowledgement):
    
    def __int__(self, message: str):
        self.__message = message
    
    @property
    def message(self):
        return self.__message
    
    def accept(): 
        return False
    
    
