import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from services.interfaces.i_kite_service import IKiteService
from services.interfaces.i_token_store import ITokenStore
from services.interfaces.i_trade_service import ITradeService

class AutoTradeJob:
    def __init__(self, kite_service: IKiteService, token_store: ITokenStore, trade_service: ITradeService):
        self._kite_service = kite_service
        self._token_store = token_store
        self._trade_service = trade_service
        self._scheduler = BackgroundScheduler()
    
    def execute(self):
        try:
            token = self._token_store.get_token()
            
            if not token:
                print("Access token not available. Please login first.")
                raise Exception("Token missing. Please login.")
            
            print(f"Auto trade job started at: {datetime.now()}")
            
            # Set token explicitly
            self._kite_service.set_access_token(token)
            
            # Execute dynamic trades (straddle strategy)
            asyncio.run(self._trade_service.execute_dynamic_trades())
            
            print("Auto trade executed with GTT")
        except Exception as ex:
            print(f"Error in AutoTradeJob: {ex}")
    
    def start(self, cron_expression: str = "0 37 18 ? * MON-FRI"):
        # Parse cron expression - for simplicity, we'll use APScheduler's cron format
        # The original Quartz cron: "0 37 18 ? * MON-FRI" means 6:37 PM on weekdays
        # APScheduler format: hour=18, minute=37, day_of_week='mon-fri'
        self._scheduler.add_job(
            self.execute,
            'cron',
            hour=18,
            minute=37,
            day_of_week='mon-fri',
            timezone='Asia/Kolkata',
            id='auto_trade_job'
        )
        self._scheduler.start()
        print("AutoTradeJob scheduled for 6:37 PM IST on weekdays")
    
    def stop(self):
        self._scheduler.shutdown()
        print("AutoTradeJob stopped")
