import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

UPSTREAM_DNS = os.getenv("UPSTREAM_DNS", "8.8.8.8")
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "2000"))
PORT = int(os.getenv("PORT", "8080"))

# Load Firebase credentials from environment variable
firebase_cred_str = os.getenv("FIREBASE_CRED_JSON")
if firebase_cred_str:
    FIREBASE_CRED_JSON = json.loads(firebase_cred_str)
    
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")