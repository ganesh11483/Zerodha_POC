import asyncio
from flask import Blueprint, render_template, request, jsonify
from flask import current_app
from services.interfaces.i_kite_service import IKiteService
from services.interfaces.i_trade_service import ITradeService
from models.order_request import OrderRequest

trade_bp = Blueprint('trade', __name__, url_prefix='/trade')

@trade_bp.route('/index')
def index():
    return render_template('trade/index.html')

@trade_bp.route('/get_funds')
def get_funds():
    kite_service: IKiteService = current_app.config['kite_service']
    funds = kite_service.get_margins()
    return jsonify(funds)

@trade_bp.route('/get_latest_nifty_symbol')
def get_latest_nifty_symbol():
    kite_service: IKiteService = current_app.config['kite_service']
    option_type = request.args.get('optionType', 'CE')
    
    available_funds = kite_service.get_available_funds()
    option = kite_service.get_latest_atm_option(option_type)
    max_quantity = kite_service.calculate_quantity(available_funds, option.price, option.lot_size)
    
    if not option.symbol:
        return jsonify({"error": "No valid NIFTY option found"}), 400
    
    return jsonify({
        "symbol": option.symbol,
        "quantity": max_quantity
    })

@trade_bp.route('/place_orders', methods=['POST'])
def place_orders():
    kite_service: IKiteService = current_app.config['kite_service']
    
    orders_data = request.get_json()
    if not orders_data:
        return jsonify({"error": "No orders received."}), 400
    
    orders = [OrderRequest(o['trading_symbol'], o['transaction_type'], o['quantity']) for o in orders_data]
    
    max_qty_per_order = 1755
    all_order_ids = []
    
    for order in orders:
        remaining_qty = order.quantity
        remaining_qty = (remaining_qty // 65) * 65
        
        while remaining_qty > 0:
            chunk_qty = min(remaining_qty, max_qty_per_order)
            chunk_qty = (chunk_qty // 65) * 65
            
            try:
                response = kite_service.place_order(
                    order.trading_symbol,
                    chunk_qty,
                    order.transaction_type,
                    validity="MINUTE"
                )
                
                executed = kite_service.wait_for_order_execution(response['order_id'], 5)
                buy_price = float(executed['average_price'])
                
                from utils.sl_target_calculator import SLTargetCalculator
                result = SLTargetCalculator.calculate(buy_price)
                stop_loss = result.stop_loss
                target = result.target
                
                gtt_id = kite_service.place_gtt_order(
                    order.trading_symbol,
                    65,
                    buy_price,
                    stop_loss,
                    target
                )
                
                print(f"Placed {order.trading_symbol} Qty: {chunk_qty}")
                all_order_ids.append(response['order_id'])
            except Exception as ex:
                print(f"Error placing {order.trading_symbol} Qty {chunk_qty}: {ex}")
                all_order_ids.append(f"ERROR-{order.trading_symbol}")
            
            remaining_qty -= chunk_qty
    
    return jsonify({
        "message": "Orders placed successfully (chunked + parallel)",
        "order_ids": all_order_ids
    })

@trade_bp.route('/place_trade')
def place_trade():
    trade_service: ITradeService = current_app.config['trade_service']
    trade_service.place_trade_with_gtt("NIFTY...", 50)
    return jsonify({"message": "Trade placed with SL & Target"})
