from flask import Blueprint, render_template, redirect, request, session, jsonify
from services.interfaces.i_kite_service import IKiteService
from services.interfaces.i_token_store import ITokenStore

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    return render_template('auth/login.html')

@auth_bp.route('/zerodha_login')
def zerodha_login():
    from services import KiteService, TokenStore
    from flask import current_app
    
    kite_service: IKiteService = current_app.config['kite_service']
    url = kite_service.get_login_url()
    print(f"Redirecting to Zerodha URL: {url}")
    return redirect(url)

@auth_bp.route('/callback')
def callback():
    from flask import current_app
    
    request_token = request.args.get('request_token')
    if not request_token:
        return "Missing request_token from Zerodha redirect.", 400
    
    kite_service: IKiteService = current_app.config['kite_service']
    token_store: ITokenStore = current_app.config['token_store']
    
    user = kite_service.generate_session(request_token)
    
    session['access_token'] = user['access_token']
    token_store.set_token(user['access_token'])
    
    return redirect('/trade/index')

@auth_bp.route('/logout')
def logout():
    from flask import current_app
    
    kite_service: IKiteService = current_app.config['kite_service']
    token_store: ITokenStore = current_app.config['token_store']
    
    try:
        kite_service.invalidate_session()
    except:
        pass
    
    session.clear()
    token_store.clear_token()
    return redirect('/auth/login')
