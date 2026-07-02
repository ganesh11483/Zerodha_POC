from abc import ABC, abstractmethod
from typing import List, Optional
from models.option_contract import OptionContract

class IKiteService(ABC):
    @abstractmethod
    def get_login_url(self) -> str:
        pass
    
    @abstractmethod
    def generate_session(self, request_token: str):
        pass
    
    @abstractmethod
    def set_access_token(self, access_token: str):
        pass
    
    @abstractmethod
    def invalidate_session(self):
        pass
    
    @abstractmethod
    def place_order(self, symbol: str, quantity: int, transaction_type: str, 
                   order_type: str = "MARKET", price: Optional[float] = None, 
                   trigger_price: Optional[float] = None, validity: str = "DAY"):
        pass
    
    @abstractmethod
    def get_orders(self) -> List:
        pass
    
    @abstractmethod
    def get_order_by_id(self, order_id: str):
        pass
    
    @abstractmethod
    def wait_for_order_execution(self, order_id: str, max_retries: int = 5):
        pass
    
    @abstractmethod
    def modify_order(self, order_id: str, quantity: int, price: Optional[float] = None, 
                    trigger_price: Optional[float] = None):
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str):
        pass
    
    @abstractmethod
    def exit_position(self, symbol: str, quantity: int):
        pass
    
    @abstractmethod
    def get_margins(self):
        pass
    
    @abstractmethod
    def get_available_funds(self) -> float:
        pass
    
    @abstractmethod
    def get_ltp(self, symbol: str) -> float:
        pass
    
    @abstractmethod
    def get_latest_nifty_symbol(self, option_type: str) -> str:
        pass
    
    @abstractmethod
    def get_latest_atm_option(self, option_type: str) -> OptionContract:
        pass
    
    @abstractmethod
    def calculate_quantity(self, allocated_funds: float, option_price: float, lot_size: int) -> int:
        pass
    
    @abstractmethod
    def get_gtts(self) -> List:
        pass
    
    @abstractmethod
    def delete_gtt(self, trigger_id: int):
        pass
    
    @abstractmethod
    def modify_gtt(self, trigger_id: int, symbol: str, qty: int, last_price: float, 
                  new_sl: float, new_target: float):
        pass
    
    @abstractmethod
    def place_gtt_order(self, symbol: str, qty: int, last_price: float, 
                       stop_loss: float, target: float) -> int:
        pass
