import firebase_admin
from firebase_admin import credentials, firestore

try:
    from app.config import FIREBASE_CRED_JSON
except ImportError:
    from .config import FIREBASE_CRED_JSON

_app = None
_db = None

def init_firebase():
    global _app, _db
    if _app: 
        return
    cred = credentials.Certificate(FIREBASE_CRED_JSON)
    _app = firebase_admin.initialize_app(cred)
    _db = firestore.client()
    
def get_client():
    if not _db: 
        init_firebase()
    return _db
