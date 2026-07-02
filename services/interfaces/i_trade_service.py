from abc import ABC, abstractmethod
from typing import List
from models.trade import Trade
from models.trade_signal import TradeSignal

class ITradeService(ABC):
    @abstractmethod
    def place_trade_with_gtt(self, symbol: str, qty: int):
        pass
    
    @abstractmethod
    def execute_trades_in_parallel(self, signals: List[TradeSignal]):
        pass
    
    @abstractmethod
    def place_trade_with_protection(self, symbol: str, qty: int, sl_percent: float, target_percent: float):
        pass
    
    @abstractmethod
    def execute_dynamic_trades(self):
        pass
    
    @abstractmethod
    def sync_trades_with_positions(self):
        pass
    
    @abstractmethod
    def sync_trades_with_gtt(self):
        pass
    
    @abstractmethod
    def cancel_trade_gtt(self, trade: Trade):
        pass
    
    @abstractmethod
    def close_expired_trades(self):
        pass
