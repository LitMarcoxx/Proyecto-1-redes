import csv, os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(script_dir, "firebase-credentials.json")
cred = credentials.Certificate(credentials_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

BATCH_SIZE = 500
batch = db.batch()
count = 0

def ip_to_int(ip):
    a,b,c,d = map(int, ip.split('.'))
    return (a << 24) | (b << 16) | (c << 8) | d

def int_to_ip(n):
    return f"{(n>>24)&255}.{(n>>16)&255}.{(n>>8)&255}.{n&255}"


with open(os.path.join(script_dir, "ip_country.csv")) as f:
    reader = csv.reader(f)
    
    # Configurar rango de líneas a procesar
    START_INDEX = 50000
    END_INDEX = 341338
    
    for line_index, (start_ip, end_ip, country) in enumerate(reader):
        # Saltar líneas antes del índice de inicio
        if line_index < START_INDEX:
            continue
            
        # Terminar cuando llegue al índice final
        if line_index >= END_INDEX:
            print(f"Reached end index {END_INDEX}, stopping...")
            break
        
        s = ip_to_int(start_ip)
        e = ip_to_int(end_ip)
        doc_id = f"range_{s}_{e}"
        doc_ref = db.collection("ip_to_country").document(doc_id)
        batch.set(doc_ref, {"range_start": s, "range_end": e, "country": country, "start_ip": start_ip, "end_ip": end_ip})
        count += 1
        
        # Mostrar progreso cada 1000 líneas
        if count % 1000 == 0:
            print(f"Processed {count} records (line {line_index})")
        
        if count % BATCH_SIZE == 0:
            batch.commit()
            batch = db.batch()
# commit remaining
if count % BATCH_SIZE != 0:
    batch.commit()

print(f"Total records processed: {count}")
print(f"Range: lines {START_INDEX} to {END_INDEX-1}")