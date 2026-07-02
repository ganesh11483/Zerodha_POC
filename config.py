import os
from dataclasses import dataclass

@dataclass
class Config:
    # Zerodha Configuration
    ZERODHA_API_KEY = "8899gn3d5zjut2tj"  # Rise-Live
    ZERODHA_API_SECRET = "z3e5lwymds3gi596vx56goou0tgkvt7l"
    
    # Trading Configuration
    IS_LIVE = False  # Simulation mode by default
    
    # Scheduler Configuration
    AUTO_TRADE_CRON = "0 37 18 ? * MON-FRI"  # 6:37 PM IST weekdays
    TIMEZONE = "Asia/Kolkata"
    
    # Trading Strategy Configuration
    SL_PERCENT = 3.0
    TARGET_PERCENT = 6.0
    MAX_QTY_PER_ORDER = 1755  # NSE freeze limit
    LOT_SIZE = 65
    CAPITAL_USAGE_PERCENT = 0.90  # Use 90% of available capital
    
    # Session Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

config = Config()
