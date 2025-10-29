
try: 
    from firebase_client import get_client
except ImportError:
    from .firebase_client import get_client

try: 
    from utils import get_geo_location_from_db
except ImportError:
    from .utils import get_geo_location_from_db


def create_record(data: dict) -> bool:
    """
    Crea un record DNS en Firestore con geolocalizacion para los targets.
    
    Estructura esperada:
    {
        "fqdn": "example.com",
        "type": "single|multi|weight|geo|roundtrip",
        "ttl": 300,
        "targets": [
            {"id": "target-1", "ip": "192.0.2.1", "weight": 70 (opcional)},
            {"id": "target-2", "ip": "192.0.2.2"}
        ],
        "health": {
            "target-1": {"status": "healthy"},
            "target-2": {"status": "unhealthy"}
        },
        "rr_index": 0 (para tipo multi)
    }
    """
    client = get_client()
    if not client:
        return False
    
    try:
        # Agregar informacion de geolocalizacion a cada target
        for target in data.get("targets", []):
            if "ip" in target:
                location_info = get_geo_location_from_db(target["ip"])
                target["geo_location"] = {
                    "country": location_info.get("country", "unknown"),
                    "region": location_info.get("region", "unknown")
                }
        # Guardar el record en Firestore
        client.collection("records").document(data.get("fqdn")).set(data)
        return True
        
    except Exception as e:
        print(f"Error creating record: {e}")
        return False
    
def get_record(fqdn: str):
    """Obtiene un record DNS por su FQDN."""
    client = get_client()
    if not client:
        return None
    doc = client.collection("records").document(fqdn).get()
    return doc.to_dict() if doc.exists else None

def get_all_records() -> list:
    """Obtiene todos los records DNS de la base de datos."""
    client = get_client()
    if not client:
        return []
    
    try:
        docs = client.collection("records").stream()
        records = [doc.to_dict() for doc in docs]
        return records
        
    except Exception as e:
        print(f"Error retrieving records: {e}")
        return []
    
def get_record_by_fqdn(fqdn: str) -> dict | None:
    """Obtiene un record DNS por su FQDN (alias de get_record)."""
    client = get_client()
    if not client:
        return None
    
    try:
        doc = client.collection("records").document(fqdn).get()
        return doc.to_dict() if doc.exists else None
        
    except Exception as e:
        print(f"Error retrieving record for {fqdn}: {e}")
        return None
    
def delete_record(fqdn: str) -> bool:
    """Elimina un record DNS por su FQDN."""
    client = get_client()
    if not client:
        return False
    
    try:
        client.collection("records").document(fqdn).delete()
        return True
        
    except Exception as e:
        print(f"Error deleting record for {fqdn}: {e}")
        return False

def delete_all_records():
    """Elimina todos los records DNS de la base de datos."""
    client = get_client()
    if not client:
        return False
    
    try:
        docs = client.collection("records").stream()
        for doc in docs:
            doc.reference.delete()
        return True
        
    except Exception as e:
        print(f"Error deleting all records: {e}")
        return False

def update_record(fqdn: str, updates: dict) -> bool:
    """Actualiza campos de un record DNS existente."""
    client = get_client()
    if not client:
        return False
    
    try:
        client.collection("records").document(fqdn).update(updates)
        return True
        
    except Exception as e:
        print(f"Error updating record for {fqdn}: {e}")
        return False





def create_ip_to_country(data: dict) -> bool:
    """
    Crea un mapeo de rango IP a pais en Firestore.
    
    Estructura esperada:
    {
        "start_ip": "1.0.0.0",
        "end_ip": "1.0.0.255",
        "country": "US"
    }
    
    Genera documento con ID: range_{start_int}_{end_int}
    """
    client = get_client()
    if not client:
        return False
    
    try:
        start_ip = data.get("start_ip")
        end_ip = data.get("end_ip")
        country = data.get("country")
        
        if not start_ip or not end_ip:
            print("Error: start_ip y end_ip son requeridos")
            return False
        
        def ip_to_int(ip: str) -> int:
            a, b, c, d = map(int, ip.split("."))
            return (a << 24) | (b << 16) | (c << 8) | d
        
        s = ip_to_int(start_ip)
        e = ip_to_int(end_ip)
        doc_id = f"range_{s}_{e}"
        
        payload = {
            "range_start": s,
            "range_end": e,
            "start_ip": start_ip,
            "end_ip": end_ip,
            "country": country
        }
        
        client.collection("ip_to_country").document(doc_id).set(payload)
        return True
        
    except Exception as e:
        print(f"Error creating ip_to_country: {e}")
        return False

def get_ip_to_country(ip_or_id: str):
    """
    Busca el mapeo IP->pais por IP (ej: "8.8.8.8") o por ID de documento (ej: "range_134744072_134744327").
    Si es una IP, busca el rango que la contiene.
    """
    client = get_client()
    if not client:
        return None
    
    try:
        # Si contiene punto, es una IP
        if "." in ip_or_id:
            def ip_to_int(ip: str) -> int:
                a, b, c, d = map(int, ip.split("."))
                return (a << 24) | (b << 16) | (c << 8) | d
            
            ip_int = ip_to_int(ip_or_id)
            
            # Buscar por range_start <= ip_int, ordenar descendente y validar range_end
            from google.cloud import firestore
            docs = list(
                client.collection("ip_to_country")
                .where("range_start", "<=", ip_int)
                .order_by("range_start", direction=firestore.Query.DESCENDING)
                .limit(10)
                .stream()
            )
            
            for doc in docs:
                data = doc.to_dict()
                if data.get("range_end", 0) >= ip_int:
                    return data
            return None
        else:
            # Es un ID de documento
            doc = client.collection("ip_to_country").document(ip_or_id).get()
            return doc.to_dict() if doc.exists else None
            
    except Exception as e:
        print(f"Error retrieving ip_to_country: {e}")
        return None


def get_all_ip_to_country(limit: int = 100, start_after: str = None) -> dict:
    """
    Obtiene rangos IP->pais con paginacion.
    
    Args:
        limit: Cantidad maxima de documentos a retornar (default: 100, max: 1000)
        start_after: ID del ultimo documento de la pagina anterior (para continuar)
    
    Returns:
        dict: {
            "data": [...],
            "count": int,
            "next_page_token": str | None,
            "has_more": bool
        }
    """
    client = get_client()
    if not client:
        return {"data": [], "count": 0, "next_page_token": None, "has_more": False}

    try:
        # Limitar el tamaño de página para evitar timeouts
        limit = min(limit, 1000)
        
        query = client.collection("ip_to_country").order_by("__name__").limit(limit + 1)
        
        # Si hay un cursor, continuar desde ese documento
        if start_after:
            start_doc = client.collection("ip_to_country").document(start_after).get()
            if start_doc.exists:
                query = query.start_after(start_doc)
        
        docs = list(query.stream())
        
        # Verificar si hay más páginas
        has_more = len(docs) > limit
        if has_more:
            docs = docs[:limit]  # Remover el documento extra
        
        records = [doc.to_dict() for doc in docs]
        
        # Obtener el token para la próxima página
        next_page_token = docs[-1].id if (docs and has_more) else None
        
        return {
            "data": records,
            "count": len(records),
            "next_page_token": next_page_token,
            "has_more": has_more
        }

    except Exception as e:
        print(f"Error retrieving IP to Country records: {e}")
        return {"data": [], "count": 0, "next_page_token": None, "has_more": False}

def update_ip_to_country(ip_or_id: str, updates: dict) -> bool:
    """
    Actualiza un rango IP->pais por IP o por ID de documento.
    Nota: No se recomienda cambiar start_ip/end_ip porque el ID incluye los valores.
    """
    client = get_client()
    if not client:
        return False
    
    try:
        doc_id = ip_or_id
        
        # Si es una IP, buscar el documento
        if "." in ip_or_id:
            found = get_ip_to_country(ip_or_id)
            if not found:
                print(f"No se encontro rango para IP: {ip_or_id}")
                return False
            s = found.get("range_start")
            e = found.get("range_end")
            doc_id = f"range_{s}_{e}"
        
        client.collection("ip_to_country").document(doc_id).update(updates)
        return True
        
    except Exception as e:
        print(f"Error updating IP to Country record: {e}")
        return False

def delete_ip_to_country(ip_or_id: str) -> bool:
    """Elimina un rango IP->pais por IP o por ID de documento."""
    client = get_client()
    if not client:
        return False
    
    try:
        doc_id = ip_or_id
        
        # Si es una IP, buscar el documento
        if "." in ip_or_id:
            found = get_ip_to_country(ip_or_id)
            if not found:
                print(f"No se encontro rango para IP: {ip_or_id}")
                return False
            s = found.get("range_start")
            e = found.get("range_end")
            doc_id = f"range_{s}_{e}"
        
        client.collection("ip_to_country").document(doc_id).delete()
        return True
        
    except Exception as e:
        print(f"Error deleting IP to Country record: {e}")
        return False