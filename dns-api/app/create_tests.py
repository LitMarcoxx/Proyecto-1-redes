"""
create_tests.py
Inserta records + health usando create_record() con geolocalización automática.
- Los targets se simplifican a solo id e ip
- La geolocalización se resuelve automáticamente con lookup_country()
- Ejecuta: python create_tests.py
"""

import time
from firebase_client import get_client

from crud import create_record

def add_health_record(fqdn: str, target_id: str, health_data: dict):
    """Agregar un record de health para un target específico"""
    client = get_client()
    if not client:
        return False
    try:
        client.collection("health").document(fqdn).collection("targets").document(target_id).set(health_data)
        return True
    except Exception as e:
        print(f"Error adding health record: {e}")
        return False

# ---------- samples (estructura simplificada) ----------
samples = {
    "single.example.com": (
        {
            "fqdn": "single.example.com",
            "type": "single",
            "ttl": 60,
            "targets": [{"id": "t1", "ip": "198.135.127.5"}],  # US
            "health": {
            "t1": {
                "status": "healthy",
                "rtt": {"last_ms": 28.4, "by_region": {"na": 28.4}}
            }
            }
        
        }
    ),

    "multi.example.com": (
        {
            "fqdn": "multi.example.com",
            "type": "multi",
            "ttl": 45,
            "targets": [
                {"id": "t1", "ip": "198.135.127.10"},  # US
                {"id": "t2", "ip": "198.135.126.10"},  # CA 
                {"id": "t3", "ip": "198.135.137.10"}   # CH
            ],
            "rr_index": 0,
            "health": {
                "t1": {"status":"healthy","rtt":{"last_ms":34.0,"by_region":{"na":34.0}}},  # US
                "t2": {"status":"healthy","rtt":{"last_ms":40.2,"by_region":{"na":40.2}}},  # CA
                "t3": {"status":"unhealthy","rtt":{"last_ms": None,"by_region": {}}}        # CH
            } 
        }
    ),

    "weight.example.com": (
        {
            "fqdn": "weight.example.com",
            "type": "weight",
            "ttl": 30,
            "targets": [
                {"id":"t1","ip":"198.135.167.20","weight":10},  # GB
                {"id":"t2","ip":"198.135.220.20","weight":1},   # DE
                {"id":"t3","ip":"198.136.186.20","weight":4}    # FR
            ],
            "health": {
            "t1": {"status":"healthy","rtt":{"last_ms":25.0,"by_region":{"eu":25.0}}},    # GB
            "t2": {"status":"unhealthy","rtt":{"last_ms": None,"by_region": {}}},          # DE
            "t3": {"status":"healthy","rtt":{"last_ms":60.1,"by_region":{"eu":60.1}}}     # FR
            }
        }
    ),

    "geo.example.com": (
        {
            "fqdn": "geo.example.com",
            "type": "geo",
            "ttl": 60,
            "targets": [
                {"id":"t1","ip":"198.145.67.50"},   # CR (Central America)
                {"id":"t2","ip":"198.135.127.50"},   # US (North America)
                {"id":"t3","ip":"198.145.66.50"}    # AR (South America)
            ],
            "health": {
            "t1": {"status":"healthy","rtt":{"last_ms":35.2,"by_region":{"ca":35.2}}},   # CR
            "t2": {"status":"healthy","rtt":{"last_ms":20.5,"by_region":{"na":20.5}}},   # US
            "t3": {"status":"unhealthy","rtt":{"last_ms": None,"by_region": {}}}         # AR
            }
        }
    ),

    "roundtrip.example.com": (
        {
            "fqdn": "roundtrip.example.com",
            "type": "roundtrip",
            "ttl": 40,
            "targets": [
                {"id":"t1","ip":"198.135.127.70"},   # US (North America)
                {"id":"t2","ip":"198.137.82.70"},    # AU (Oceania)
                {"id":"t3","ip":"198.137.87.70"}     # JP (Asia)
            ],
            "health": {
            "t1": {"status":"healthy",  # US
                   "rtt":{"last_ms":42.0,"by_region":{"na":42.0,"oc":120.0,"as":180.0}}},
            "t2": {"status":"healthy",  # AU
                   "rtt":{"last_ms":38.5,"by_region":{"oc":38.5,"na":200.0,"as":80.0}}},
            "t3": {"status":"healthy",  # JP
                   "rtt":{"last_ms":25.1,"by_region":{"as":25.1,"na":180.0,"oc":90.0}}}
            }
        }
    )
}

# ---------- upload usando create_record() ----------
def upload_all_with_create_record(samples):
    success_count = 0
    health_count = 0
    
    for fqdn, (record_data) in samples.items():
        print(f"📝 Creating record: {fqdn}")
        
        # 1) Crear record con geolocalización automática
        if create_record(record_data):
            print(f"✅ Record created: {fqdn}")
            success_count += 1

        else:
            print(f"❌ Record failed: {fqdn}")
    
    print(f"\n📊 Summary:")
    print(f"Records created: {success_count}/{len(samples)}")
    print(f"Health records added: {health_count}")

if __name__ == "__main__":
    print("🚀 Creating test records with automatic geolocation...")
    upload_all_with_create_record(samples)
    print("✨ Upload complete. Check Firestore console.")