import time
import random
from typing import List, Optional
from kiteconnect import KiteConnect
from services.interfaces.i_kite_service import IKiteService
from services.interfaces.i_token_store import ITokenStore
from models.option_contract import OptionContract
from config import config

class KiteService(IKiteService):
    def __init__(self, token_store: ITokenStore):
        self._config = config
        self._token_store = token_store
        self._kite = KiteConnect(api_key=self._config.ZERODHA_API_KEY)
        
        # Try to get token from memory store first
        token = self._token_store.get_token()
        if token:
            self._kite.set_access_token(token)
    
    def get_login_url(self) -> str:
        return self._kite.login_url()
    
    def generate_session(self, request_token: str):
        return self._kite.generate_session(request_token, self._config.ZERODHA_API_SECRET)
    
    def set_access_token(self, access_token: str):
        self._kite.set_access_token(access_token)
    
    def invalidate_session(self):
        self._kite.invalidate_access_token()
    
    def place_order(self, symbol: str, quantity: int, transaction_type: str, 
                   order_type: str = "MARKET", price: Optional[float] = None, 
                   trigger_price: Optional[float] = None, validity: str = "DAY"):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] {transaction_type} {symbol} Qty: {quantity} Validity:{validity}")
            return {"order_id": str(random.randint(100000, 999999))}
        
        return self._kite.place_order(
            variety=self._kite.VARIETY_REGULAR,
            exchange=self._kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=transaction_type,
            quantity=quantity,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            product=self._kite.PRODUCT_NRML,
            validity=validity
        )
    
    def get_orders(self) -> List:
        try:
            return self._kite.orders()
        except Exception as ex:
            print(f"Error fetching orders: {ex.message}")
            raise
    
    def get_order_by_id(self, order_id: str):
        orders = self._kite.orders()
        for order in orders:
            if order['order_id'] == order_id:
                return order
        return None
    
    def wait_for_order_execution(self, order_id: str, max_retries: int = 5):
        if not self._config.IS_LIVE:
            return {
                'order_id': order_id,
                'status': 'COMPLETE',
                'average_price': 100
            }
        
        for i in range(max_retries):
            order = self.get_order_by_id(order_id)
            if order and order['status'] == 'COMPLETE':
                return order
            time.sleep(1)
        
        raise Exception("Order not completed in time")
    
    def modify_order(self, order_id: str, quantity: int, price: Optional[float] = None, 
                    trigger_price: Optional[float] = None):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] Order Modified")
            return
        
        self._kite.modify_order(
            variety=self._kite.VARIETY_REGULAR,
            order_id=order_id,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price
        )
    
    def cancel_order(self, order_id: str):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] Order cancelled")
            return
        
        self._kite.cancel_order(
            variety=self._kite.VARIETY_REGULAR,
            order_id=order_id
        )
    
    def exit_position(self, symbol: str, quantity: int):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] Order exited")
            return
        
        self._kite.place_order(
            variety=self._kite.VARIETY_REGULAR,
            exchange=self._kite.EXCHANGE_NFO,
            tradingsymbol=symbol,
            transaction_type=self._kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            order_type=self._kite.ORDER_TYPE_MARKET,
            product=self._kite.PRODUCT_NRML,
            validity="MINUTE"
        )
    
    def get_margins(self):
        margins = self._kite.margins("equity")
        return {
            'available_cash': margins['available']['cash'],
            'utilised': margins['utilised']['debit'],
            'net': margins['net']
        }
    
    def get_available_funds(self) -> float:
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] AvailableCash: 100000")
            return 100000.0
        
        margins = self._kite.margins("equity")
        return float(margins['net'])
    
    def get_ltp(self, symbol: str) -> float:
        quote = self._kite.quote([f"NFO:{symbol}"])
        return float(quote[f"NFO:{symbol}"]['last_price'])
    
    def get_latest_nifty_symbol(self, option_type: str) -> str:
        ltp_data = self._kite.quote(["NSE:NIFTY 50"])
        ltp = ltp_data["NSE:NIFTY 50"]['last_price']
        
        strike = round(ltp / 50) * 50
        instruments = self._kite.instruments("NFO")
        
        option = None
        for inst in instruments:
            if (inst['name'] == "NIFTY" and 
                inst['instrument_type'] == option_type and 
                inst['expiry'] and 
                inst['strike'] == strike):
                if option is None or inst['expiry'] < option['expiry']:
                    option = inst
        
        return option['tradingsymbol'] if option else ""
    
    def get_latest_atm_option(self, option_type: str) -> OptionContract:
        ltp_data = self._kite.quote(["NSE:NIFTY 50"])
        nifty_price = ltp_data["NSE:NIFTY 50"]['last_price']
        
        strike = round(nifty_price / 50) * 50
        instruments = self._kite.instruments("NFO")
        
        option = None
        for inst in instruments:
            if (inst['name'] == "NIFTY" and 
                inst['instrument_type'] == option_type and 
                inst['expiry'] and 
                inst['strike'] == strike):
                if option is None or inst['expiry'] < option['expiry']:
                    option = inst
        
        if not option:
            return OptionContract()
        
        option_ltp = self._kite.quote([f"NFO:{option['tradingsymbol']}"])
        premium = float(option_ltp[f"NFO:{option['tradingsymbol']}"]['last_price'])
        
        return OptionContract(
            symbol=option['tradingsymbol'],
            price=premium,
            lot_size=option['lot_size']
        )
    
    def calculate_quantity(self, allocated_funds: float, option_price: float, lot_size: int) -> int:
        one_lot_value = option_price * lot_size
        lots = int(allocated_funds / one_lot_value)
        
        if lots < 1:
            lots = 1
        
        return lots * lot_size
    
    def get_gtts(self) -> List:
        return self._kite.gtts()
    
    def delete_gtt(self, trigger_id: int):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] GTT Deleted")
            return
        
        self._kite.cancel_gtt(trigger_id)
    
    def modify_gtt(self, trigger_id: int, symbol: str, qty: int, last_price: float, 
                  new_sl: float, new_target: float):
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] GTT Modified")
            return
        
        gtt_params = {
            "trigger_type": "two-leg",
            "tradingsymbol": symbol,
            "exchange": self._kite.EXCHANGE_NFO,
            "last_price": last_price,
            "trigger_values": [new_sl, new_target],
            "orders": [
                {
                    "transaction_type": self._kite.TRANSACTION_TYPE_SELL,
                    "quantity": qty,
                    "order_type": self._kite.ORDER_TYPE_SL,
                    "price": new_sl,
                    "product": self._kite.PRODUCT_NRML
                },
                {
                    "transaction_type": self._kite.TRANSACTION_TYPE_SELL,
                    "quantity": qty,
                    "order_type": self._kite.ORDER_TYPE_LIMIT,
                    "price": new_target,
                    "product": self._kite.PRODUCT_NRML
                }
            ]
        }
        
        self._kite.modify_gtt(trigger_id, gtt_params)
    
    def place_gtt_order(self, symbol: str, qty: int, last_price: float, 
                       stop_loss: float, target: float) -> int:
        if not self._config.IS_LIVE:
            print(f"[SIMULATION] GTT Created")
            return random.randint(10000, 99999)
        
        gtt_params = {
            "trigger_type": "two-leg",
            "tradingsymbol": symbol,
            "exchange": self._kite.EXCHANGE_NFO,
            "last_price": last_price,
            "trigger_values": [stop_loss, target],
            "orders": [
                {
                    "transaction_type": self._kite.TRANSACTION_TYPE_SELL,
                    "quantity": qty,
                    "order_type": self._kite.ORDER_TYPE_LIMIT,
                    "price": stop_loss,
                    "product": self._kite.PRODUCT_NRML
                },
                {
                    "transaction_type": self._kite.TRANSACTION_TYPE_SELL,
                    "quantity": qty,
                    "order_type": self._kite.ORDER_TYPE_LIMIT,
                    "price": target,
                    "product": self._kite.PRODUCT_NRML
                }
            ]
        }
        
        response = self._kite.place_gtt(gtt_params)
        return int(response['data']['trigger_id'])
