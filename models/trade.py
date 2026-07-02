from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    quantity: int = 0
    entry_price: float = 0.0
    current_stop_loss: float = 0.0
    current_target: float = 0.0
    entry_order_id: str = ""
    gtt_trigger_id: Optional[int] = None
    is_open: bool = True
    is_break_even_hit: bool = False
    last_price: float = 0.0
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    last_modified_time: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
