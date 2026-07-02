from dataclasses import dataclass

@dataclass
class TradeSignal:
    symbol: str = ""
    price: float = 0.0
    lot_size: int = 0
