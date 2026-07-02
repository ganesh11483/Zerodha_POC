from dataclasses import dataclass
from typing import Optional
from .trade import Trade

@dataclass
class StraddleSession:
    ce_trade: Optional[Trade] = None
    pe_trade: Optional[Trade] = None
