import asyncio
import time
from datetime import datetime
from typing import List
from enum import Enum
from services.interfaces.i_trade_service import ITradeService
from services.interfaces.i_kite_service import IKiteService
from services.interfaces.i_trade_store import ITradeStore
from models.trade import Trade
from models.trade_signal import TradeSignal
from models.option_contract import OptionContract
from utils.sl_target_calculator import SLTargetCalculator
from config import config

class IndexType(Enum):
    NIFTY_50 = "NIFTY"
    SENSEX = "SENSEX"

class TradeService(ITradeService):
    def __init__(self, trade_store: ITradeStore, kite_service: IKiteService):
        self._trade_store = trade_store
        self._kite_service = kite_service
        self._orders_placed_today = 0
        self._max_orders_per_session = 50
    
    def validate_trading_day(self, symbol: str):
        """Validate if trading is allowed for the index on current day"""
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        
        # Determine index type from symbol
        if "NIFTY" in symbol.upper():
            index_type = IndexType.NIFTY_50
        elif "SENSEX" in symbol.upper() or "BANKEX" in symbol.upper():
            index_type = IndexType.SENSEX
        else:
            # For other symbols, allow trading any day
            return
        
        # Define allowed trading days
        nifty_allowed_days = {2, 3, 4}  # Wednesday, Thursday, Friday
        sensex_allowed_days = {0, 1}    # Monday, Tuesday
        
        if index_type == IndexType.NIFTY_50:
            if current_day not in nifty_allowed_days:
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_day]
                raise Exception(f"NIFTY 50 trading not allowed on {day_name}. Allowed days: Wednesday, Thursday, Friday")
        
        elif index_type == IndexType.SENSEX:
            if current_day not in sensex_allowed_days:
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][current_day]
                raise Exception(f"SENSEX trading not allowed on {day_name}. Allowed days: Monday, Tuesday")
    
    def validate_order_params(self, symbol: str, qty: int, max_loss_percent: float = 5.0):
        """Validate order parameters before placement"""
        # Trading day validation
        self.validate_trading_day(symbol)
        
        # Circuit breaker check
        if self._orders_placed_today >= self._max_orders_per_session:
            raise Exception(f"Circuit breaker triggered: Max orders ({self._max_orders_per_session}) reached for session")
        
        # Quantity validation
        if qty <= 0:
            raise Exception("Quantity must be positive")
        
        if qty > config.MAX_QTY_PER_ORDER:
            raise Exception(f"Quantity {qty} exceeds max limit {config.MAX_QTY_PER_ORDER}")
        
        if qty % config.LOT_SIZE != 0:
            raise Exception(f"Quantity {qty} must be a multiple of lot size {config.LOT_SIZE}")
        
        # Funds check
        available_funds = self._kite_service.get_available_funds()
        if available_funds <= 0:
            raise Exception("Insufficient funds available")
        
        # Max loss protection
        max_allowed_loss = available_funds * 0.02  # Max 2% of total capital per trade
        estimated_loss = (available_funds * max_loss_percent / 100)
        if estimated_loss > max_allowed_loss:
            raise Exception(f"Trade loss {estimated_loss:.2f} exceeds max allowed loss {max_allowed_loss:.2f}")
        
        print(f"[PROTECTION] Order validated: {symbol} Qty:{qty} MaxLoss:{max_loss_percent}%")
    
    def place_trade_with_gtt(self, symbol: str, qty: int):
        # Add protection before placing order
        self.validate_order_params(symbol, qty, max_loss_percent=5.0)
        
        buy_order = self._kite_service.place_order(
            symbol, qty, "BUY", validity="MINUTE"
        )
        
        self._orders_placed_today += 1
        
        order_id = buy_order['order_id']
        
        orders = self._kite_service.get_orders()
        executed = next((o for o in orders if o['order_id'] == order_id), None)
        
        buy_price = float(executed['average_price'])
        
        # Use config SL/Target instead of hardcoded values
        stop_loss = round(buy_price * (1 - config.SL_PERCENT / 100), 1)
        target = round(buy_price * (1 + config.TARGET_PERCENT / 100), 1)
        
        self._kite_service.place_gtt_order(symbol, qty, buy_price, stop_loss, target)
    
    async def execute_trades_in_parallel(self, signals: List[TradeSignal]):
        total_funds = self._kite_service.get_available_funds()
        
        print(f"Available Funds: {total_funds}")
        
        funds_per_trade = total_funds / len(signals)
        
        async def execute_signal(signal):
            try:
                qty = self._kite_service.calculate_quantity(
                    funds_per_trade,
                    signal.price,
                    signal.lot_size
                )
                
                print(f"Placing order: {signal.symbol} Qty: {qty}")
                
                await self.place_trade_with_protection(
                    signal.symbol,
                    qty,
                    5,   # SL %
                    10   # Target %
                )
            except Exception as ex:
                print(f"Error for {signal.symbol}: {ex}")
        
        tasks = [execute_signal(signal) for signal in signals]
        await asyncio.gather(*tasks)
        
        print("All trades completed")
    
    async def place_trade_with_protection(self, symbol: str, total_qty: int, sl_percent: float, target_percent: float):
        # Add protection before placing order
        self.validate_order_params(symbol, total_qty, max_loss_percent=sl_percent)
        
        max_qty_per_order = 1755  # NSE freeze limit
        tasks = []
        trades = []
        
        total_qty = (total_qty // 65) * 65
        
        while total_qty > 0:
            qty = min(total_qty, max_qty_per_order)
            qty = (qty // 65) * 65
            
            async def execute_chunk():
                try:
                    print(f"Placing chunk: {symbol} Qty: {qty}")
                    
                    buy_order = self._kite_service.place_order(
                        symbol,
                        qty,
                        "BUY",
                        validity="MINUTE"
                    )
                    
                    self._orders_placed_today += 1
                    
                    executed = self._kite_service.wait_for_order_execution(buy_order['order_id'], 10)
                    
                    for attempt in range(5):
                        try:
                            current_ltp = self._kite_service.get_ltp(symbol)
                            
                            result = SLTargetCalculator.calculate(current_ltp)
                            
                            stop_loss = result.stop_loss
                            target = result.target
                            
                            gtt_id = self._kite_service.place_gtt_order(
                                symbol,
                                qty,
                                current_ltp,
                                stop_loss,
                                target
                            )
                            
                            print(f"GTT Created: {gtt_id}")
                            
                            trade = Trade(
                                symbol=symbol,
                                quantity=qty,
                                entry_order_id=buy_order['order_id'],
                                entry_price=current_ltp,
                                gtt_trigger_id=gtt_id,
                                current_stop_loss=stop_loss,
                                current_target=target,
                                is_open=True,
                                last_modified_time=datetime.now()
                            )
                            
                            self._trade_store.add(trade)
                            trades.append(trade)
                            print(f"Chunk complete | Qty: {qty} | GTT: {gtt_id}")
                            break
                        except Exception as ex:
                            await asyncio.sleep(1)
                except Exception as ex:
                    print(f"Chunk error ({symbol} Qty {qty}): {ex}")
            
            tasks.append(execute_chunk())
            total_qty -= qty
        
        await asyncio.gather(*tasks)
        print(f"Trade completed for {symbol}")
        return trades
    
    async def execute_dynamic_trades(self):
        total_funds = self._kite_service.get_available_funds()
        print(f"Total funds is: {total_funds}")
        
        total_funds *= 0.90
        
        ce_option = self._kite_service.get_latest_atm_option("CE")
        pe_option = self._kite_service.get_latest_atm_option("PE")
        
        options = [ce_option, pe_option]
        
        funds_per_trade = total_funds / len(options)
        
        async def execute_option(option):
            qty = self._kite_service.calculate_quantity(
                funds_per_trade,
                option.price,
                option.lot_size
            )
            
            print(f"Symbol: {option.symbol}")
            print(f"Price: {option.price}")
            print(f"Qty: {qty}")
            
            return await self.place_trade_with_protection(
                option.symbol,
                65,
                3,
                6
            )
        
        tasks = [execute_option(option) for option in options]
        results = await asyncio.gather(*tasks)
        
        all_trades = []
        for result in results:
            all_trades.extend(result)
        
        gtt_failed = any(not t.gtt_trigger_id or t.gtt_trigger_id <= 0 for t in all_trades)
        if gtt_failed:
            for trade in all_trades:
                try:
                    self._kite_service.exit_position(trade.symbol, trade.quantity)
                except:
                    pass
            
            raise Exception("GTT creation failed. All positions exited.")
        
        print("All trades executed")
    
    def sync_trades_with_positions(self):
        positions = self._kite_service.get_positions()
        
        for trade in self._trade_store.get_open_trades():
            position = next((p for p in positions['net'] if p['tradingsymbol'] == trade.symbol), None)
            
            if position and position['quantity'] == 0:
                trade.is_open = False
                trade.exit_price = position['last_price']
                trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity
                trade.closed_at = datetime.now()
                
                print(f"Trade closed: {trade.symbol}")
    
    def sync_trades_with_gtt(self):
        gtts = self._kite_service.get_gtts()
        
        for trade in self._trade_store.get_open_trades():
            gtt = next((g for g in gtts if g['id'] == trade.gtt_trigger_id), None)
            
            if gtt and gtt['status'] == 'triggered':
                trade.is_open = False
                trade.closed_at = datetime.now()
                
                print(f"GTT executed for {trade.symbol}")
    
    def cancel_trade_gtt(self, trade: Trade):
        if trade.gtt_trigger_id:
            self._kite_service.delete_gtt(trade.gtt_trigger_id)
            trade.gtt_trigger_id = None
            print("GTT removed")
    
    def close_expired_trades(self):
        trades = self._trade_store.get_open_trades()
        
        for trade in trades:
            if (datetime.now() - trade.created_at).total_seconds() > 3600:  # 60 minutes
                print(f"Trade expired: {trade.symbol}")
                
                self._kite_service.exit_position(trade.symbol, trade.quantity)
                
                trade.is_open = False
                trade.closed_at = datetime.now()
