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
else:
    # Fallback to hardcoded credentials (not recommended for production)
    FIREBASE_CRED_JSON = {"type":"service_account","project_id":"dns-project-b2ce0","private_key_id":"657d2cf2bc1ba6118cfccb91390f572ded6a645d","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCwq3DPl7Ii8OkA\nQoCzJQh5TAPAc1grtuadRgh2jI0OeCQFK3+WK1lRpZChpGEGZ/6JE/PtctDWcYxE\nRt7k8d4tVTMlU4GtKGYLUiudhEOc5v4Gx3O++A77LRDWd7n2j7ccNMJoP/g8X5a/\njV9tjJ7WWVp0Xec+HpLIjOsjYnY/9x35/jan1uEX9LLwS3SB2F+F1dun2QkxypUI\nx1Av690B7zxZgXW3BskuVENVJEhaYMboefPmTb76AOlF2yfRWFD2xzLpj93LnzBN\ndFQC+ZGNMlOlbvo+BqFHTX5zUk2yQcA8dhP9sEh8f3DnaZ7ZWNYL0dCyOb64bJ8D\nxfWkgyy5AgMBAAECggEACXz/p0qKoOlG3kJ0For54EfWmL6pINnnG1HAURud1MXb\ni2KJbOeBmcq2UJQbOOSbbUHC00EcGbRJ9/3FaU7bI5ykjU/lkkbt6hQ87u4EUpgu\nUu9h1kMMzO0f7yDJfkY8K5niygYLfzSUDFAbrK7FdhYg70h+y52JPReiZklat/cm\n9xM9Pb+5+7rRxYz5m2hJefEGLYGz/0iIZkcNBIBM4W43+3mMi717ptsrHMk5TrE7\ndxonM2ARtrXmjUl5IY6wdC7j3yFMCYvDkbQ6oPUrljCB329GlO6COICbYrdzo12b\nnaAtQqYuvOyc7fASuCMQQiip6Ft+h1VBWDhdDPkV4QKBgQDo7bujVznDCy+sDCmX\n0o6h/JHotiyZ17ITsGv3Agt8AGyP4b9LldUrzyryyVKM0pwp6mykxQDpQgHakjAc\nnHp3OaokSHjS/A6t8QHCrUOAAJMGj/cVIv471pfzyCzlri2C+UrFRhfptDlTPi3q\nlInuKAj0XC084fpmAKhLdmnKUQKBgQDCKyy26xTkDIeIEspV1EMTXK4vKgzE0EP8\nZ28qJ2X6lPM3Hj2gWnfvyg4GKZHUjnA2x2vbgGofETZn6abna4Bxbnb3+L0PXjUO\n2J3RvnXlqlztoHMAo08CJDmvvRF8+eWVMnSvQ5KrQLF6xehlW2OmuTk+4xWNbtFz\n8gbck8456QKBgQCr/TYKgtKEwRK/P+/KSc/Frh/yq+k84zZ7MU5XAeyG8C05BGBi\nqEzR31OAF8Vbc/uZO55i/5APrAyAXmcmCSioNiz6Q4TrjPAt4YICRDtOHZ5yPwUb\nV05P0sE6YTk9kqHKTta12W64wrl9TLFMv8ck0eziudkxVk602JFrvxCYMQKBgDJr\nd68AGGqnfkItbvEer1RFys1gg/RPiHfwfANcO7T4HLgBWEtdcquHsmCTRtUFL8pp\num5DSEtM8u3E1JxfY/kQkEAQDTgCZJC4WzLt3DuJI5xo/7P4tDmAIqKp2/KyCZXW\nhkpEp79kizGwVoqLUrMmgeD8osoZLraG8JUypGiRAoGBAMTLVVHXpxdHqSgJfr7F\nZP5xSKydvD27tV757DMLPm7fYKTrRgyeM6gsL1Ebr+r2Jaw01S4XdGiSuKewX5nl\nARo8C6n+SHihTjUatymtcHrWiaAqZY+mA0S9mvtkjCGURBwrDAEfuev5WR9af1Z2\nXRKk9TCNlgjLzv5ioAA/ccU8\n-----END PRIVATE KEY-----\n","client_email":"firebase-adminsdk-fbsvc@dns-project-b2ce0.iam.gserviceaccount.com","client_id":"110758275751296471883","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40dns-project-b2ce0.iam.gserviceaccount.com","universe_domain":"googleapis.com"}

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")