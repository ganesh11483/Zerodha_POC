from abc import ABC, abstractmethod

class ITokenStore(ABC):
    @abstractmethod
    def set_token(self, token: str):
        pass
    
    @abstractmethod
    def get_token(self) -> str:
        pass
    
    @abstractmethod
    def clear_token(self):
        pass
