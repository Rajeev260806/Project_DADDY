from abc import ABC,abstractmethod
from loguru import logger

class BaseAgent(ABC):

    def __init__(self,name:str):
        self.name = name
        logger.info(f"Agent initialised: {self.name}")
    
    @abstractmethod
    def handle(self,command:str)->str:
        pass
    
    def safe_run(self,command:str)->str:
        try:
            return self.handle(command)
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            return f"Sorry, something went wrong while handling that: {e}"
