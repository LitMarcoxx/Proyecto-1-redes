import requests
from google.cloud import firestore

try:
    from firebase_client import get_client
except ImportError:
    from .firebase_client import get_client

REGION_MAP = {
    # A
    "AF":"as","AX":"eu","AL":"eu","DZ":"af","AS":"oc","AD":"eu","AO":"af","AI":"ca",
    "AQ":"an","AG":"ca","AR":"sa","AM":"eu","AW":"ca","AU":"oc","AT":"eu","AZ":"as",

    # B
    "BS":"ca","BH":"as","BD":"as","BB":"ca","BY":"eu","BE":"eu","BZ":"ca","BJ":"af",
    "BM":"ca","BT":"as","BO":"sa","BQ":"ca","BA":"eu","BW":"af","BV":"oc","BR":"sa",
    "IO":"as","BN":"as","BG":"eu","BF":"af","BI":"af",

    # C
    "KH":"as","CM":"af","CA":"na","CV":"af","KY":"ca","CF":"af","TD":"af","CL":"sa",
    "CN":"as","CX":"oc","CC":"oc","CO":"sa","KM":"af","CG":"af","CD":"af","CK":"oc",
    "CR":"ca","CI":"af","HR":"eu","CU":"ca","CW":"ca","CY":"eu","CZ":"eu",

    # D
    "DK":"eu","DJ":"af","DM":"ca","DO":"ca",

    # E
    "EC":"sa","EG":"af","SV":"ca","GQ":"af","ER":"af","EE":"eu","ET":"af",

    # F
    "FK":"sa","FO":"eu","FJ":"oc","FI":"eu","FR":"eu","GF":"sa","PF":"oc","TF":"an",

    # G
    "GA":"af","GM":"af","GE":"eu","DE":"eu","GH":"af","GI":"eu","GR":"eu","GL":"na",
    "GD":"ca","GP":"ca","GU":"oc","GT":"ca","GG":"eu","GN":"af","GW":"af","GY":"sa",

    # H
    "HT":"ca","HM":"oc","VA":"eu","HN":"ca","HK":"as","HU":"eu",

    # I
    "IS":"eu","IN":"as","ID":"as","IR":"as","IQ":"as","IE":"eu","IM":"eu","IL":"as",
    "IT":"eu","JM":"ca","JP":"as","JE":"eu","JO":"as",

    # K
    "KZ":"as","KE":"af","KI":"oc","KP":"as","KR":"as","KW":"as","KG":"as",

    # L
    "LA":"as","LV":"eu","LB":"as","LS":"af","LR":"af","LY":"af","LI":"eu","LT":"eu",
    "LU":"eu",

    # M
    "MO":"as","MK":"eu","MG":"af","MW":"af","MY":"as","MV":"as","ML":"af","MT":"eu",
    "MH":"oc","MQ":"ca","MR":"af","MU":"af","YT":"af","MX":"na","FM":"oc","MD":"eu",
    "MC":"eu","MN":"as","ME":"eu","MS":"ca","MA":"af","MZ":"af","MM":"as",

    # N
    "NA":"af","NR":"oc","NP":"as","NL":"eu","NC":"oc","NZ":"oc","NI":"ca","NE":"af",
    "NG":"af","NU":"oc","NF":"oc","MP":"oc","NO":"eu",

    # O
    "OM":"as",

    # P
    "PK":"as","PW":"oc","PS":"as","PA":"ca","PG":"oc","PY":"sa","PE":"sa","PH":"as",
    "PN":"oc","PL":"eu","PT":"eu","PR":"ca",

    # Q
    "QA":"as",

    # R
    "RE":"af","RO":"eu","RU":"eu","RW":"af",

    # S
    "BL":"ca","SH":"ca","KN":"ca","LC":"ca","MF":"ca","PM":"ca","VC":"ca",
    "WS":"oc","SM":"eu","ST":"af","SA":"as","SN":"af","RS":"eu","SC":"af","SL":"af",
    "SG":"as","SX":"ca","SK":"eu","SI":"eu","SB":"oc","SO":"af","ZA":"af","GS":"oc",
    "SS":"af","ES":"eu","LK":"as","SD":"af","SR":"sa","SJ":"eu","SE":"eu","CH":"eu",
    "SY":"as","TW":"as","TJ":"as","TZ":"af","TH":"as","TL":"as","TG":"af","TK":"oc",
    "TO":"oc","TT":"ca","TN":"af","TR":"as","TM":"as","TC":"ca","TV":"oc",

    # U
    "UG":"af","UA":"eu","AE":"as","GB":"eu","US":"na","UM":"oc","UY":"sa","UZ":"as",

    # V
    "VU":"oc","VE":"sa","VN":"as","VG":"ca","VI":"ca",

    # W-Z
    "WF":"oc","EH":"af","YE":"as","ZM":"af","ZW":"af"
    }

def ip_to_int(ip):
    a,b,c,d = map(int, ip.split('.'))
    return (a << 24) | (b << 16) | (c << 8) | d

def int_to_ip(n):
    return f"{(n>>24)&255}.{(n>>16)&255}.{(n>>8)&255}.{n&255}"

def get_geo_location_from_db(ip: str):
    """Busca pais y region de una IP en la base de datos."""
    db = get_client()
    if not db:
        # fallback simple: devuelve unknown o heurística (útil en tests)
        return {"ip": ip, "country": "unknown", "region": "unknown"}

    # convertir IP a entero (IPv4). Si usas IPv6, añade manejo adicional.
    try:
        ip_int = ip_to_int(ip)
    except Exception:
        # IP inválida
        return {"ip": ip, "country": "unknown", "region": "unknown"}

    try:
        # Construye la query: un solo filtro de desigualdad + order_by
        q = (
            db.collection("ip_to_country")
              .where(filter=firestore.FieldFilter("range_start", "<=", ip_int))
              .order_by("range_start", direction=firestore.Query.DESCENDING)
              .limit(1)
        )
        docs = q.get()
    except Exception as e:
        # Si la consulta falla por cualquier razón (p. ej. índice), fallback local heurístico
        print(f"Warning: IP geolocation query failed: {e}")
        # Fallback heurístico simplificado (igual que tu versión actual)
        # --- heurística simple para testing ---
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            country = "US"
        else:
            # pequeña heurística por residuo (solo para pruebas)
            try:
                if (ip_int % 10) < 3:
                    country = "US"
                elif (ip_int % 10) < 6:
                    country = "CA"
                else:
                    country = "MX"
            except Exception:
                country = "US"
        region = REGION_MAP.get(country, "na")
        return {"ip": ip, "country": country, "region": region}

    # Si no hay docs, no hay match
    if not docs:
        return {"ip": ip, "country": "unknown", "region": "unknown"}

    # Tomamos el único doc devuelto y verificamos range_end localmente
    doc = docs[0].to_dict()
    # doc debe contener range_start, range_end, country
    try:
        range_start = int(doc.get("range_start"))
        range_end = int(doc.get("range_end"))
        country = doc.get("country", "unknown")
    except Exception:
        return {"ip": ip, "country": "unknown", "region": "unknown"}

    if range_start <= ip_int <= range_end:
        region = REGION_MAP.get(country, "unknown")
        return {"ip": ip, "country": country, "region": region}

    # si no está dentro del range => no match
    return {"ip": ip, "country": "unknown", "region": "unknown"}

def get_geo_location_from_api(ip: str):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            country = data.get("countryCode", "unknown")
            region = REGION_MAP.get(country, "unknown")
            return {"ip": ip, "country": country, "region": REGION_MAP.get(country, "unknown")}
        else:
            # Fallback a heurística local si la API falla
            return {"ip": ip, "country": "unknown", "region": "unknown"}
    except Exception as e:
        print(f"Warning: IP-API request failed: {e}")
        # Fallback a heurística local
        if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
            country = "US"
        else:
            ip_int = ip_to_int(ip)
            if (ip_int % 10) < 3:
                country = "US"
            elif (ip_int % 10) < 6:
                country = "CA"
            else:
                country = "MX"
        region = REGION_MAP.get(country, "na")
        return {"ip": ip, "country": country, "region": region}
