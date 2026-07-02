import math
from models.sl_target_result import SLTargetResult

class SLTargetCalculator:
    @staticmethod
    def calculate(price: float, sl_percent: float = 3.0, target_percent: float = 6.0) -> SLTargetResult:
        tick = 0.05
        
        # Step 1: Calculate raw values
        sl = price * (1 - sl_percent / 100)
        target = price * (1 + target_percent / 100)
        
        # Step 2: Round to tick size
        sl = SLTargetCalculator._round_to_tick(sl, tick)
        target = SLTargetCalculator._round_to_tick(target, tick)
        
        # Step 3: Ensure valid direction
        if sl >= price:
            sl = SLTargetCalculator._round_to_tick(price - tick, tick)
        
        if target <= price:
            target = SLTargetCalculator._round_to_tick(price + tick, tick)
        
        # Step 4: Ensure minimum gap
        min_gap = SLTargetCalculator._get_minimum_gap(price)
        
        if (price - sl) < min_gap:
            sl = SLTargetCalculator._round_to_tick(price - min_gap, tick)
        
        if (target - price) < min_gap:
            target = SLTargetCalculator._round_to_tick(price + min_gap, tick)
        
        # Step 5: Final validation
        SLTargetCalculator._validate(price, sl, target)
        
        return SLTargetResult(stop_loss=sl, target=target)
    
    @staticmethod
    def _round_to_tick(price: float, tick: float) -> float:
        return round(price / tick) * tick
    
    @staticmethod
    def _get_minimum_gap(price: float) -> float:
        return max(price * 0.01, 0.10)
    
    @staticmethod
    def _validate(price: float, sl: float, target: float):
        if sl <= 0:
            raise Exception("Invalid SL")
        
        if sl >= price:
            raise Exception("SL must be less than price")
        
        if target <= price:
            raise Exception("Target must be greater than price")
        
        if target <= sl:
            raise Exception("Target must be greater than SL")
