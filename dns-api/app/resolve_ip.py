"""
Resolución DNS con algoritmos de balanceo inteligente:
- single: Retorna siempre el mismo IP.
- multi: Round-robin entre targets saludables.
- weight: Distribución ponderada por pesos.
- geo: Selección por cercanía geográfica.
- roundtrip: Selección por menor latencia (RTT) por región.

Todos verifican health antes de retornar.
Si no hay targets healthy, retorna None.
"""

import time
import random
from google.cloud import firestore

try:
    from utils import get_geo_location_from_db, get_geo_location_from_api
except ImportError:
    from .utils import get_geo_location_from_db, get_geo_location_from_api

try:
    from firebase_client import get_client
except ImportError:
    from .firebase_client import get_client


# ---------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def get_record(fqdn: str):
    """Obtiene un record DNS desde Firestore por FQDN."""
    client = get_client()
    if not client:
        return None
    doc = client.collection("records").document(fqdn).get()
    return doc.to_dict() if doc.exists else None


def get_health_record(record: dict, target_id: str):
    """Obtiene información de health de un target."""
    return record.get("health", {}).get(target_id)


# ---------------------------------------------------------------------------
# ALGORITMOS DE RESOLUCIÓN
# ---------------------------------------------------------------------------

def resolve_single(record: dict):
    """Devuelve siempre el mismo IP si está healthy."""
    targets = record.get("targets", [])
    if not targets:
        return None

    target = targets[0]
    health = get_health_record(record, target["id"])
    if not health or health.get("status") != "healthy":
        return None

    print(f"[SINGLE] Retornando {target['ip']} (healthy)")
    return {"ip": target["ip"], "target_id": target["id"], "type": "single"}


def resolve_multi(record: dict):
    """Round-robin entre targets healthy."""
    targets = record.get("targets", [])
    if not targets:
        return None

    healthy = [t for t in targets if get_health_record(record, t["id"]) and get_health_record(record, t["id"]).get("status") == "healthy"]
    if not healthy:
        return None

    rr_index = record.get("rr_index", 0)
    selected = healthy[rr_index % len(healthy)]

    # Actualiza índice para la próxima resolución
    client = get_client()
    if client:
        client.collection("records").document(record["fqdn"]).update({"rr_index": (rr_index + 1) % len(healthy)})

    print(f"[MULTI] Seleccionado {selected['ip']} (RR index {rr_index})")
    return {"ip": selected["ip"], "target_id": selected["id"], "type": "multi"}


def resolve_weight(record: dict):
    """Distribución ponderada por pesos."""
    targets = record.get("targets", [])
    if not targets:
        return None

    healthy = [t for t in targets if get_health_record(record, t["id"]) and get_health_record(record, t["id"]).get("status") == "healthy"]
    if not healthy:
        return None

    total_weight = sum(t.get("weight", 1) for t in healthy)
    rand_value = random.uniform(0, total_weight)
    cumulative = 0
    for target in healthy:
        cumulative += target.get("weight", 1)
        if rand_value <= cumulative:
            print(f"[WEIGHT] Seleccionado {target['ip']} con peso {target.get('weight', 1)}")
            return {"ip": target["ip"], "target_id": target["id"], "type": "weight"}

    return None


def resolve_geo(record: dict, client_ip: str):
    """Selección por país/región del cliente."""
    client_info = get_geo_location_from_db(client_ip)
    country = client_info.get("country", "unknown")
    region = client_info.get("region", "unknown")

    if country == "unknown" and region == "unknown":
        client_info = get_geo_location_from_api(client_ip)
        country = client_info.get("country", "unknown")
        region = client_info.get("region", "unknown")

    targets = record.get("targets", [])
    healthy_targets = []
    for t in targets:
        health = get_health_record(record, t["id"])
        if health and health.get("status") == "healthy":
            geo = t.get("geo_location", {})
            if geo.get("country") == country or geo.get("region") == region:
                healthy_targets.append(t)

    if not healthy_targets:
        healthy_targets = [t for t in targets if get_health_record(record, t["id"]).get("status") == "healthy"]

    if not healthy_targets:
        return None

    selected = healthy_targets[0]
    print(f"[GEO] Cliente {client_ip} -> {selected['ip']} ({region}, {country})")
    return {"ip": selected["ip"], "target_id": selected["id"], "type": "geo"}


def resolve_roundtrip(record: dict, client_ip: str):
    """
    Selección por menor RTT de la región del cliente.
    Simula comportamiento real de Health Checkers distribuidos.
    """
    client_info = get_geo_location_from_db(client_ip)
    client_region = client_info.get("region", "unknown")

    if client_region == "unknown":
        print(f"[ROUNDTRIP] Región desconocida para IP {client_ip}. Usando RTT general.")
        client_region = "na"  # fallback default

    targets = record.get("targets", [])
    if not targets:
        return None

    best_target = None
    best_rtt = float("inf")

    for target in targets:
        health = get_health_record(record, target["id"])
        if not health or health.get("status") != "healthy":
            continue

        rtt_info = health.get("rtt", {})
        rtt_by_region = rtt_info.get("by_region", {})
        rtt_value = rtt_by_region.get(client_region, rtt_info.get("last_ms", 999))

        if rtt_value < best_rtt:
            best_target = target
            best_rtt = rtt_value

    if not best_target:
        return None

    print(f"[ROUNDTRIP] Cliente región={client_region} → {best_target['ip']} (RTT={best_rtt} ms)")
    return {"ip": best_target["ip"], "target_id": best_target["id"], "type": "roundtrip"}


# ---------------------------------------------------------------------------
# DISPATCHER PRINCIPAL
# ---------------------------------------------------------------------------

def resolve(record: dict, client_ip: str):
    """Despacha según el tipo de record."""
    if not record or "type" not in record:
        return None

    rtype = record["type"]
    if rtype == "single":
        return resolve_single(record)
    elif rtype == "multi":
        return resolve_multi(record)
    elif rtype == "weight":
        return resolve_weight(record)
    elif rtype == "geo":
        return resolve_geo(record, client_ip)
    elif rtype == "roundtrip":
        return resolve_roundtrip(record, client_ip)
    else:
        print(f"[WARN] Tipo de record desconocido: {rtype}")
        return None
