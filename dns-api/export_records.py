import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# 🔹 Cargar las variables del archivo .env
load_dotenv()

print("📡 Exportando colección 'records' de Firestore...")

# Leer credenciales del entorno (.env)
cred_json_str = os.getenv("FIREBASE_CRED_JSON")
if not cred_json_str:
    raise ValueError("No se encontró FIREBASE_CRED_JSON en las variables de entorno")

try:
    cred_data = json.loads(cred_json_str)
except json.JSONDecodeError as e:
    raise ValueError(f"Error al parsear FIREBASE_CRED_JSON: {e}")

# Inicializar Firebase con las credenciales
cred = credentials.Certificate(cred_data)
firebase_admin.initialize_app(cred)

# Conexión a Firestore
db = firestore.client()

# Leer todos los documentos de la colección 'records'
docs = db.collection("records").stream()

data = {}
for doc in docs:
    data[doc.id] = doc.to_dict()

# Guardar a archivo JSON
output_file = "records_export.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Exportación completada: {output_file} generado correctamente.")
