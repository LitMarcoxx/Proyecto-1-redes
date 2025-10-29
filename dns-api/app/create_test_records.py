"""
Script de ejemplo para cargar records DNS de prueba en Firebase

Ejecutar:
    python create_test_records.py

Requisitos:
    - Firebase credentials configurados
    - Collection 'records' en Firestore
"""

from google.cloud import firestore
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configurar credenciales de Firebase
# Asegurate de tener FIREBASE_CRED_JSON o firebase-credentials.json
try:
    from app.firebase_client import get_client
    client = get_client()
except:
    # Fallback si ejecutas fuera de la app
    cred_json = os.getenv("FIREBASE_CRED_JSON")
    if cred_json:
        from firebase_admin import credentials, firestore as admin_firestore
        import firebase_admin
        cred = credentials.Certificate(json.loads(cred_json))
        firebase_admin.initialize_app(cred)
        client = admin_firestore.client()
    else:
        print("ERROR: Necesitas configurar FIREBASE_CRED_JSON")
        exit(1)

# Records de prueba
test_records = [
    {
        "fqdn": "single.example.com",
        "type": "single",
        "ttl": 300,
        "targets": [
            {"id": "single-1", "ip": "192.0.2.1"}
        ],
        "health": {
            "single-1": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"}
        }
    },
    {
        "fqdn": "multi.example.com",
        "type": "multi",
        "ttl": 300,
        "targets": [
            {"id": "multi-1", "ip": "192.0.2.1"},
            {"id": "multi-2", "ip": "192.0.2.2"},
            {"id": "multi-3", "ip": "192.0.2.3"}
        ],
        "rr_index": 0,
        "health": {
            "multi-1": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "multi-2": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "multi-3": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"}
        }
    },
    {
        "fqdn": "weight.example.com",
        "type": "weight",
        "ttl": 300,
        "targets": [
            {"id": "weight-1", "ip": "192.0.2.1", "weight": 70},
            {"id": "weight-2", "ip": "192.0.2.2", "weight": 20},
            {"id": "weight-3", "ip": "192.0.2.3", "weight": 10}
        ],
        "health": {
            "weight-1": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "weight-2": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "weight-3": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"}
        }
    },
    {
        "fqdn": "geo.example.com",
        "type": "geo",
        "ttl": 300,
        "targets": [
            {
                "id": "us-east",
                "ip": "192.0.2.1",
                "geolocation": {"country": "US", "region": "na"}
            },
            {
                "id": "eu-west",
                "ip": "198.51.100.1",
                "geolocation": {"country": "DE", "region": "eu"}
            },
            {
                "id": "asia-pacific",
                "ip": "203.0.113.1",
                "geolocation": {"country": "JP", "region": "as"}
            }
        ],
        "health": {
            "us-east": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "eu-west": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"},
            "asia-pacific": {"status": "healthy", "last_check": "2025-10-06T10:00:00Z"}
        }
    },
    {
        "fqdn": "roundtrip.example.com",
        "type": "roundtrip",
        "ttl": 300,
        "targets": [
            {"id": "rt-1", "ip": "192.0.2.1"},
            {"id": "rt-2", "ip": "198.51.100.1"},
            {"id": "rt-3", "ip": "203.0.113.1"}
        ],
        "health": {
            "rt-1": {
                "status": "healthy",
                "last_check": "2025-10-06T10:00:00Z",
                "rtt": {
                    "last_ms": 45,
                    "by_region": {
                        "na": 15,
                        "eu": 120,
                        "as": 200,
                        "sa": 80,
                        "af": 150,
                        "oc": 180
                    }
                }
            },
            "rt-2": {
                "status": "healthy",
                "last_check": "2025-10-06T10:00:00Z",
                "rtt": {
                    "last_ms": 60,
                    "by_region": {
                        "na": 100,
                        "eu": 25,
                        "as": 180,
                        "sa": 90,
                        "af": 70,
                        "oc": 200
                    }
                }
            },
            "rt-3": {
                "status": "healthy",
                "last_check": "2025-10-06T10:00:00Z",
                "rtt": {
                    "last_ms": 55,
                    "by_region": {
                        "na": 180,
                        "eu": 160,
                        "as": 20,
                        "sa": 120,
                        "af": 110,
                        "oc": 45
                    }
                }
            }
        }
    }
]

def load_test_records():
    """Cargar records de prueba en Firebase"""
    print("Cargando records de prueba en Firebase...")
    
    for record in test_records:
        fqdn = record["fqdn"]
        print(f"  - Cargando {fqdn} (tipo: {record['type']})")
        
        try:
            client.collection("records").document(fqdn).set(record)
            print(f"    OK: {fqdn}")
        except Exception as e:
            print(f"    ERROR: {fqdn} - {e}")
    
    print("\nRecords cargados exitosamente!")
    print("\nPrueba con:")
    for record in test_records:
        print(f"  nslookup {record['fqdn']} 127.0.0.1")

if __name__ == "__main__":
    load_test_records()
