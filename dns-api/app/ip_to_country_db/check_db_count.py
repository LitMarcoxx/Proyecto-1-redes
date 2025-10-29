import os
import firebase_admin
from firebase_admin import credentials, firestore

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(script_dir, "firebase-credentials.json")

try:
    # Initialize Firebase (if not already initialized)
    cred = credentials.Certificate(credentials_path)
    firebase_admin.initialize_app(cred)
except ValueError:
    # App already initialized
    pass

db = firestore.client()

def count_documents():
    """Count documents in the ip_to_country collection using efficient count query"""
    try:
        # Use the count() method - much more efficient!
        collection_ref = db.collection("ip_to_country")
        count_query = collection_ref.count()
        count_result = count_query.get()
        
        # Get the count value from the result
        return count_result[0][0].value
        
    except Exception as e:
        print(f"Error al contar documentos: {e}")
        print("Intentando método alternativo...")
        return -1
    
if __name__ == "__main__":
    print("Contando documentos en Firestore...")
    print("=" * 40)
    
    # Count total documents efficiently
    total_count = count_documents()
    
    if total_count >= 0:
        print(f"\nTotal de documentos en 'ip_to_country': {total_count}")
    else:
        print("No se pudo contar los documentos.")
    
    print("=" * 40)