from services.interfaces.i_token_store import ITokenStore

class TokenStore(ITokenStore):
    def __init__(self):
        self._token = None
    
    def set_token(self, token: str):
        self._token = token
    
    def get_token(self) -> str:
        return self._token or ""
    
    def clear_token(self):
        self._token = None
