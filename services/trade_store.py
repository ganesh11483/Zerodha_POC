from typing import List
from services.interfaces.i_trade_store import ITradeStore
from models.trade import Trade

class TradeStore(ITradeStore):
    def __init__(self):
        self._trades: List[Trade] = []
    
    def add(self, trade: Trade):
        self._trades.append(trade)
    
    def get_open_trades(self) -> List[Trade]:
        return [t for t in self._trades if t.is_open]
    
    def get_all_trades(self) -> List[Trade]:
        return self._trades
    
    def update(self, trade: Trade):
        for i, t in enumerate(self._trades):
            if t.trade_id == trade.trade_id:
                self._trades[i] = trade
                break
    
    def delete(self, trade_id: str):
        self._trades = [t for t in self._trades if t.trade_id != trade_id]
