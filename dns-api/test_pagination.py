"""
Script de prueba para paginacion de ip_to_country

Ejecutar:
    python test_pagination.py

Requisitos:
    - API corriendo en http://localhost:8080
    - Collection ip_to_country con datos
"""

import requests
import json

API_URL = "http://localhost:8080"

def test_pagination():
    """Prueba la paginacion del endpoint ip_to_country"""
    
    print("=" * 60)
    print("Prueba de Paginacion - IP to Country")
    print("=" * 60)
    
    # Primera pagina
    print("\n1. Obteniendo primera pagina (limit=10)...")
    response = requests.get(f"{API_URL}/api/ip_to_country?limit=10")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    data = response.json()
    print(f"   - Registros obtenidos: {data['count']}")
    print(f"   - Hay mas paginas: {data['has_more']}")
    print(f"   - Token siguiente: {data['next_page_token']}")
    
    if data['data']:
        print(f"\n   Primer registro:")
        first = data['data'][0]
        print(f"   - Rango: {first.get('start_ip')} - {first.get('end_ip')}")
        print(f"   - Pais: {first.get('country')}")
    
    # Segunda pagina
    if data['has_more'] and data['next_page_token']:
        print(f"\n2. Obteniendo segunda pagina (usando token)...")
        response = requests.get(
            f"{API_URL}/api/ip_to_country",
            params={"limit": 10, "start_after": data['next_page_token']}
        )
        
        if response.status_code == 200:
            data2 = response.json()
            print(f"   - Registros obtenidos: {data2['count']}")
            print(f"   - Hay mas paginas: {data2['has_more']}")
            print(f"   - Token siguiente: {data2['next_page_token']}")
            
            if data2['data']:
                print(f"\n   Primer registro de pagina 2:")
                first = data2['data'][0]
                print(f"   - Rango: {first.get('start_ip')} - {first.get('end_ip')}")
                print(f"   - Pais: {first.get('country')}")
    
    # Obtener total aproximado iterando varias paginas
    print(f"\n3. Contando registros (maximo 5 paginas)...")
    total = 0
    page_num = 0
    next_token = None
    
    while page_num < 5:
        params = {"limit": 100}
        if next_token:
            params["start_after"] = next_token
        
        response = requests.get(f"{API_URL}/api/ip_to_country", params=params)
        
        if response.status_code != 200:
            break
        
        result = response.json()
        total += result['count']
        page_num += 1
        
        print(f"   - Pagina {page_num}: {result['count']} registros (total: {total})")
        
        if not result['has_more']:
            print(f"\n   Fin de datos alcanzado.")
            break
        
        next_token = result['next_page_token']
    
    print(f"\n   Total de registros procesados: {total}")
    if page_num >= 5:
        print(f"   (Nota: Se procesaron solo las primeras 5 paginas)")
    
    print("\n" + "=" * 60)
    print("Prueba completada")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_pagination()
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar a la API.")
        print("Asegurate de que la API este corriendo en http://localhost:8080")
    except Exception as e:
        print(f"Error inesperado: {e}")
