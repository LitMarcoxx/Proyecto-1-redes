import json, os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()
cred_data = json.loads(os.getenv("FIREBASE_CRED_JSON"))
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred)
db = firestore.client()

records = {
    "singlecheck.example.com": {
        "fqdn": "singlecheck.example.com",
        "type": "single",
        "ttl": 60,
        "targets": [{"ip": "198.135.127.5", "id": "t1"}]
    },
    "geocheck.example.com": {
        "fqdn": "geocheck.example.com",
        "type": "geo",
        "ttl": 60,
        "targets": [
            {"ip": "198.135.126.20", "id": "t1"},
            {"ip": "198.145.67.50", "id": "t2"}
        ]
    },
    "roundtripcheck.example.com": {
        "fqdn": "roundtripcheck.example.com",
        "type": "roundtrip",
        "ttl": 40,
        "targets": [
            {"ip": "198.135.127.70", "id": "t1"},
            {"ip": "198.137.82.70", "id": "t2"},
            {"ip": "198.137.87.70", "id": "t3"}
        ]
    }
}

for name, data in records.items():
    db.collection("records").document(name).set(data)
    print(f"Creado: {name}")

print("Todos los registros se cargaron correctamente.")
