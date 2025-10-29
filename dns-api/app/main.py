from fastapi import FastAPI, Query, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict
from datetime import datetime

# Importar funciones CRUD con alias para evitar shadowing
from app.crud import get_record
from app.crud import get_all_records
from app.crud import create_record as crud_create_record
from app.crud import update_record as crud_update_record
from app.crud import delete_record as crud_delete_record
from app.crud import get_ip_to_country
from app.crud import get_all_ip_to_country
from app.crud import create_ip_to_country
from app.crud import update_ip_to_country
from app.crud import delete_ip_to_country

from app.schemas import *
from app.resolver_logic import process_dns_query_from_base64
from app.resolve_ip import resolve
from app.utils import get_geo_location_from_db
from app.firebase_client import get_client

# Conjunto de regiones "simuladas" por el healthchecker
REGIONS = {"na", "eu", "sa", "ca", "as"}

app = FastAPI(
    title="DNS API Inteligente",
    description="""
    API para resolución DNS con algoritmos de balanceo de carga inteligente.

    ## Tipos de Records
    * single: Un solo target siempre
    * multi: Round-robin entre múltiples targets
    * weight: Distribución ponderada por pesos
    * geo: Selección basada en país/región del cliente
    * roundtrip: Selección por menor tiempo de respuesta
    """,
    version="1.0.0",
)

@app.get("/", summary="Health Check", tags=["Health"], status_code=status.HTTP_200_OK)
def is_running():
    return {"running": "ok"}

@app.get("/healthz", summary="Health Status", tags=["Health"], status_code=status.HTTP_200_OK)
def health_status():
    return {"status": "ok"}

@app.get("/api/exists",
         response_model=ExistsOut,
         summary="Verificar Existencia de Record",
         tags=["DNS Records"], status_code=status.HTTP_200_OK)
def exists(host: Optional[str] = Query(None, min_length=3, max_length=255)):
    if not host:
        raise HTTPException(status_code=400, detail="host parameter is required")
    record = get_record(host)
    if record:
        return {"exists": True, "record_type": record.get("type", "unknown")}
    return {"exists": False}

@app.post("/api/dns_resolver",
          response_model=DNSResolverOut,
          summary="Resolver DNS Base64",
          tags=["DNS Resolution"], status_code=status.HTTP_200_OK)
def dns_resolver(request: DNSResolverIn):
    dns_response = process_dns_query_from_base64(request.base64_data, request.timeout_ms)
    return {
        "response_base64": dns_response["payload_b64"],
        "contacted_server": dns_response["server"],
        "rtt_ms": dns_response["rtt_ms"],
    }

@app.post("/api/resolve",
          response_model=DNSResolveOut,
          summary="Resolver DNS Inteligente",
          tags=["DNS Resolution"], status_code=status.HTTP_200_OK)
def dns_resolve(request: DNSResolveIn):
    record = get_record(request.host)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    dns_response = resolve(record, request.client_ip)
    if not dns_response:
        raise HTTPException(status_code=503, detail="No healthy targets available")
    return {**dns_response}

# CRUD Records
@app.get("/api/ip-geo/{ip_address}", summary="Get geolocation by IP address", tags=["CRUD"])
def get_geolocation(ip_address: str):
    return get_geo_location_from_db(ip_address)

@app.get("/api/records", summary="Listar todos los records DNS", tags=["CRUD"])
def get_records():
    # The Firestore CRUD returns a list of record objects. For some tools
    # (exported JSON, healthchecker) it's more convenient to have a mapping
    # keyed by fqdn. Return a mapping when possible to keep clients simple.
    records = get_all_records()
    if isinstance(records, list):
        mapped = {}
        for r in records:
            # prefer explicit fqdn field, fall back to keys that might exist
            fqdn = r.get("fqdn") or r.get("domain")
            if not fqdn:
                # skip malformed records without fqdn
                continue
            mapped[fqdn] = r
        return mapped
    # already a mapping or other shape - return as-is
    return records

@app.get("/api/records/{hostname}", summary="Obtener record DNS por hostname", tags=["CRUD"])
def get_record_by_hostname(hostname: str):
    return get_record(hostname)

@app.post("/api/records", summary="Crear record DNS", tags=["CRUD"], status_code=status.HTTP_201_CREATED)
def create_dns_record(data: dict):
    return crud_create_record(data)

@app.put("/api/records/{host}", summary="Actualizar record DNS", tags=["CRUD"])
def update_dns_record(host: str, data: dict):
    return crud_update_record(host, data)

@app.delete("/api/records/{host}", summary="Eliminar record DNS", tags=["CRUD"], status_code=status.HTTP_204_NO_CONTENT)
def delete_dns_record(host: str):
    return crud_delete_record(host)

# CRUD ip_to_country
@app.get("/api/ip_to_country", summary="Listar rangos IP->pais", tags=["CRUD"])
def list_ip_to_country(
    limit: int = Query(100, ge=1, le=1000),
    start_after: Optional[str] = Query(None)
):
    return get_all_ip_to_country(limit=limit, start_after=start_after)

@app.get("/api/ip_to_country/{ip_or_id}", summary="Obtener mapeo IP->pais", tags=["CRUD"])
def get_ip_country_mapping(ip_or_id: str):
    result = get_ip_to_country(ip_or_id)
    if not result:
        raise HTTPException(status_code=404, detail="IP mapping not found")
    return result

@app.post("/api/ip_to_country", summary="Crear rango IP->pais", tags=["CRUD"], status_code=status.HTTP_201_CREATED)
def create_ip_country_mapping(data: dict):
    ok = create_ip_to_country(data)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to create IP mapping")
    return {"created": True}

@app.put("/api/ip_to_country/{ip_or_id}", summary="Actualizar rango IP->pais", tags=["CRUD"])
def update_ip_country_mapping(ip_or_id: str, data: dict):
    ok = update_ip_to_country(ip_or_id, data)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update IP mapping")
    return {"updated": True}

@app.delete("/api/ip_to_country/{ip_or_id}", summary="Eliminar rango IP->pais", tags=["CRUD"], status_code=status.HTTP_204_NO_CONTENT)
def delete_ip_country_mapping(ip_or_id: str):
    ok = delete_ip_to_country(ip_or_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete IP mapping")
    return {"deleted": True}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _majority_status(status_by_region: Dict[str, str]) -> str:
    # Mayoría estricta de "healthy"
    total = len(status_by_region) if status_by_region else 0
    if total == 0:
        return "unknown"
    healthy = sum(1 for v in status_by_region.values() if v == "healthy")
    # Umbral: mitad + 1 sobre las regiones que ya reportaron
    threshold = (total // 2) + 1
    return "healthy" if healthy >= threshold else "unhealthy"

@app.post("/api/update_health")
async def update_health(request: Request, data: dict = None):
    try:
        client_host = request.client.host if request.client else "unknown"
    except Exception:
        client_host = "unknown"
    headers = dict(request.headers)
    user_agent = headers.get("user-agent", "")
    body_bytes = await request.body()
    body_text = body_bytes.decode(errors="replace") if body_bytes else None
    print(f"[API:DBG] update_health called from {client_host} UA='{user_agent}' headers={{{', '.join(list(headers.keys())[:5]) + (', ...' if len(headers)>5 else '')}}}")
    if body_text:
        print(f"[API:DBG] body={body_text}")

    if data is None and body_text:
        try:
            import json as _json
            data = _json.loads(body_text)
        except Exception:
            data = {}

    db = get_client()
    fqdn = data.get("fqdn")
    if not fqdn:
        raise HTTPException(status_code=400, detail="Missing fqdn")

    doc_ref = db.collection("records").document(fqdn)
    snap = doc_ref.get()
    if not snap.exists:
        # Auto-create a minimal record so health updates from agents don't fail
        # Payload usually contains at least target_id and optionally ip.
        print(f"[API] Record {fqdn} not found — creating minimal placeholder from payload")
        target_id = data.get("target_id") if isinstance(data, dict) else None
        target_ip = data.get("ip") if isinstance(data, dict) else None
        targets = []
        if target_id or target_ip:
            t = {}
            if target_id:
                t["id"] = str(target_id)
            if target_ip:
                t["ip"] = str(target_ip)
            # add placeholder geo_location to keep schemas consistent
            t["geo_location"] = {"country": "ZZ", "region": "unknown"}
            targets.append(t)

        minimal = {
            "fqdn": fqdn,
            "type": "single" if len(targets) <= 1 else "multi",
            "ttl": 300,
            "targets": targets,
            "health": {}
        }
        try:
            doc_ref.set(minimal)
            snap = doc_ref.get()
            record = snap.to_dict() or {}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create placeholder record: {e}")
    else:
        record = snap.to_dict() or {}

    # Caso 1: formato nuevo
    if "updates" in data and isinstance(data["updates"], dict):
        try:
            doc_ref.update(data["updates"])
            return {"success": True, "updated": data["updates"], "format": "new"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Firestore update failed: {str(e)}")

    # Caso 2: formato antiguo
    required = ["target_id", "region", "status", "rtt"]
    for f in required:
        if f not in data:
            raise HTTPException(status_code=400, detail=f"Missing field: {f}")

    target_id = str(data["target_id"])
    region = str(data["region"])
    status_in = str(data["status"])
    try:
        rtt = float(data["rtt"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid rtt")

    if region not in REGIONS:
        # Permitimos regiones inesperadas pero no las usamos para mayoría “global”
        pass

    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # Construir update granular (NO sobrescribir otros países/regiones)
    update_data: Dict[str, object] = {
        # Target: últimos datos observados desde ESTA región
        f"health.{target_id}.last_check": now,
        f"health.{target_id}.rtt.last_ms": rtt if status_in == "healthy" else 999.0,
        f"health.{target_id}.rtt.by_region.{region}": rtt if status_in == "healthy" else 999.0,

        # Health del "agente" regional que reporta
        f"health.{region}.status": status_in,
        f"health.{region}.last_check": now,
        f"health.{region}.rtt.last_ms": rtt if status_in == "healthy" else 999.0,
        f"health.{region}.rtt.by_region.{region}": rtt if status_in == "healthy" else 999.0,
    }

    # Mantener status por región para el TARGET y derivar mayoría
    target_health: Dict = (record.get("health", {}).get(target_id) or {})
    status_by_region: Dict[str, str] = dict(target_health.get("status_by_region") or {})
    status_by_region[region] = status_in

    agg_status = _majority_status(status_by_region)
    update_data[f"health.{target_id}.status_by_region"] = status_by_region
    if agg_status != "unknown":
        update_data[f"health.{target_id}.status"] = agg_status

    # No actualizar geo de targets aunque venga en el payload
    # Los targets mantienen la región y país original con la que fueron creados

    try:
        doc_ref.update(update_data)
        print(f"[API] Updated {fqdn} ({target_id} -> {region}, {status_in}, {rtt}ms)")
        return {"success": True, "updated": update_data, "format": "expanded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Firestore update failed: {str(e)}")
