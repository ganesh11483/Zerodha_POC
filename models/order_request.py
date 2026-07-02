from dataclasses import dataclass

@dataclass
class OrderRequest:
    trading_symbol: str = ""
    transaction_type: str = ""
    quantity: int = 0
