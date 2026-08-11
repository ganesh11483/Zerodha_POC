# Rise Trading - Python Version

Automated options trading system for Zerodha Kite Connect API.

## Features

- **Automated Options Trading**: Executes straddle strategy (ATM CE + PE options)
- **Scheduled Trading**: APScheduler-based job execution (default: 6:37 PM IST weekdays)
- **Risk Management**: Automatic GTT (Good Till Triggered) orders for Stop Loss and Target
- **Chunked Order Placement**: Handles NSE freeze limits (max 1755 qty per order)
- **Simulation Mode**: Test without real trades (configurable)
- **Web Interface**: Flask-based UI for manual trading and monitoring

## Trading Strategy

The system implements an ATM (At The Money) straddle strategy:

1. Fetches NIFTY 50 LTP
2. Identifies ATM strike price (nearest to current price)
3. Buys both CE and PE options at ATM strike
4. Places GTT orders with 3% SL and 6% Target
5. Automatic position exit when SL or Target is hit

## Configuration

Edit `config.py` to customize:

```python
# Zerodha Configuration
ZERODHA_API_KEY = "your_api_key"
ZERODHA_API_SECRET = "your_api_secret"

# Trading Configuration
IS_LIVE = False  # Set to True for live trading

# Scheduler Configuration
AUTO_TRADE_CRON = "0 37 18 ? * MON-FRI"  # 6:37 PM IST weekdays

# Trading Strategy Configuration
SL_PERCENT = 3.0
TARGET_PERCENT = 6.0
MAX_QTY_PER_ORDER = 1755
LOT_SIZE = 65
CAPITAL_USAGE_PERCENT = 0.90
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Zerodha Kite Connect API credentials

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd rise-python
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   On Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   On Linux/Mac:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Zerodha credentials**
   - Edit `config.py`
   - Replace `ZERODHA_API_KEY` and `ZERODHA_API_SECRET` with your credentials
   - Set `IS_LIVE = True` for live trading, `False` for simulation

6. **Configure Zerodha redirect URL**
   - In your Zerodha Kite Connect dashboard
   - Set redirect URL to: `http://localhost:5000/auth/callback`

## Running the Application

1. **Start the Flask application**
   ```bash
   python app.py
   ```

2. **Access the web interface**
   - Open browser to: `http://localhost:5000`
   - Click "Login with Zerodha"
   - Authorize the application
   - You'll be redirected to the trading dashboard

## Project Structure

```
rise-python/
├── app.py                      # Main application entry point
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── models/                     # Data models
│   ├── trade.py
│   ├── option_contract.py
│   ├── trade_signal.py
│   ├── order_request.py
│   ├── sl_target_result.py
│   └── straddle_session.py
├── services/                   # Business logic
│   ├── kite_service.py        # Zerodha API wrapper
│   ├── trade_service.py      # Trading logic
│   ├── token_store.py        # In-memory token storage
│   ├── trade_store.py        # In-memory trade storage
│   ├── interfaces/           # Service interfaces
│   └── jobs/                 # Scheduled jobs
│       └── auto_trade_job.py
├── controllers/               # Flask routes
│   ├── auth_controller.py
│   └── trade_controller.py
├── utils/                     # Utilities
│   └── sl_target_calculator.py
└── templates/                 # HTML templates
    ├── auth/
    │   └── login.html
    └── trade/
        └── index.html
```

## API Endpoints

### Authentication
- `GET /auth/login` - Login page
- `GET /auth/zerodha_login` - Redirect to Zerodha OAuth
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout

### Trading
- `GET /trade/index` - Trading dashboard
- `GET /trade/get_funds` - Get account funds
- `GET /trade/get_latest_nifty_symbol?optionType=CE` - Get latest ATM option
- `POST /trade/place_orders` - Place orders
- `GET /trade/place_trade` - Place single trade with GTT

## Scheduled Job

The `AutoTradeJob` is scheduled using APScheduler:
- **Schedule**: 6:37 PM IST (Monday-Friday)
- **Timezone**: Asia/Kolkata
- **Action**: Executes `execute_dynamic_trades()` (straddle strategy)

To modify the schedule, edit `auto_trade_job.py`:

```python
self._scheduler.add_job(
    self.execute,
    'cron',
    hour=18,
    minute=37,
    day_of_week='mon-fri',
    timezone='Asia/Kolkata',
    id='auto_trade_job'
)
```

## Risk Management

- **Stop Loss**: 3% below entry price (configurable)
- **Target**: 6% above entry price (configurable)
- **GTT Orders**: Automatic exit when SL or Target is hit
- **Chunked Execution**: Orders split to respect NSE limits
- **Capital Usage**: 90% of available funds (configurable)

## Simulation Mode

Set `IS_LIVE = False` in `config.py` to test without real trades:
- Orders return mock order IDs
- No actual trades placed
- Useful for testing and development

## Troubleshooting

### Token Missing Error
- Ensure you've logged in via the web interface
- Check if the token is stored in memory
- Try logging out and logging in again

### GTT Creation Failed
- Check if you have sufficient funds
- Verify option symbol is valid
- Check Zerodha API status

### Order Execution Timeout
- Increase wait time in `wait_for_order_execution()`
- Check network connectivity
- Verify Zerodha API is operational

## Dependencies

- Flask 3.0.0 - Web framework
- kiteconnect 5.0.0 - Zerodha API client
- apscheduler 3.10.4 - Job scheduling
- python-dotenv 1.0.0 - Environment variables

## Security Notes

- Never commit `config.py` with real API credentials
- Use environment variables for sensitive data in production
- Set a strong `SECRET_KEY` in production
- Use HTTPS in production environments
- Implement rate limiting for production use

## License

This is a private trading system. Use at your own risk. Options trading involves significant risk.

## Support

For issues related to:
- Zerodha Kite Connect API: https://kite.trade/docs/
- Flask: https://flask.palletsprojects.com/
- APScheduler: https://apscheduler.readthedocs.io/
