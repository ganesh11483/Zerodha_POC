from abc import ABC, abstractmethod
from typing import List
from models.trade import Trade

class ITradeStore(ABC):
    @abstractmethod
    def add(self, trade: Trade):
        pass
    
    @abstractmethod
    def get_open_trades(self) -> List[Trade]:
        pass
    
    @abstractmethod
    def get_all_trades(self) -> List[Trade]:
        pass
    
    @abstractmethod
    def update(self, trade: Trade):
        pass
    
    @abstractmethod
    def delete(self, trade_id: str):
        pass
