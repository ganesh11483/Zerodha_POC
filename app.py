from flask import Flask, session, redirect, url_for
from config import config
from services import TokenStore, TradeStore, KiteService, TradeService
from services.jobs import AutoTradeJob
from controllers import auth_bp, trade_bp

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize services
token_store = TokenStore()
trade_store = TradeStore()
kite_service = KiteService(token_store)
trade_service = TradeService(trade_store, kite_service)

# Store services in app config for access in controllers
app.config['token_store'] = token_store
app.config['trade_store'] = trade_store
app.config['kite_service'] = kite_service
app.config['trade_service'] = trade_service

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(trade_bp)

# Initialize and start scheduled job
auto_trade_job = AutoTradeJob(kite_service, token_store, trade_service)
auto_trade_job.start()

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
