# API Reference - Endpoints CRUD

## Records DNS

### Listar todos los records

```
GET /api/records
```

Sin parametros. Retorna lista de todos los records DNS.

---

### Obtener record por hostname

```
GET /api/records/{hostname}
```

**Parametro de ruta:**

- `hostname`: FQDN del record (ej: "example.com")

---

### Crear record DNS

```
POST /api/records
```

**Body (JSON):**

```json
{
  "fqdn": "example.com",
  "type": "single|multi|weight|geo|roundtrip",
  "ttl": 300,
  "targets": [
    {
      "id": "target-1",
      "ip": "192.0.2.1",
      "weight": 70
    }
  ],
  "health": {
    "target-1": {
      "status": "healthy"
    }
  },
  "rr_index": 0
}
```

**Campos:**

- `fqdn` (string, requerido): Nombre de dominio completo
- `type` (string, requerido): Tipo de algoritmo (single, multi, weight, geo, roundtrip)
- `ttl` (int, opcional): Time to live en segundos
- `targets` (array, requerido): Lista de targets
  - `id` (string): Identificador unico del target
  - `ip` (string): Direccion IP del target
  - `weight` (int, opcional): Peso para tipo weight
- `health` (object, requerido): Estado de salud de cada target
- `rr_index` (int, opcional): Indice para round-robin (tipo multi)

---

### Actualizar record DNS

```
PUT /api/records/{host}
```

**Parametro de ruta:**

- `host`: FQDN del record a actualizar

**Body (JSON):**

```json

```

Solo incluir los campos que se desean actualizar.

---

### Eliminar record DNS

```
DELETE /api/records/{host}
```

**Parametro de ruta:**

- `host`: FQDN del record a eliminar

---

## IP to Country

### Listar rangos IP->pais (con paginacion)

```
GET /api/ip_to_country
```

**Query parameters (opcionales):**

- `limit` (int): Cantidad de registros por pagina (1-1000, default: 100)
- `start_after` (string): Token de paginacion de la pagina anterior

**Respuesta:**

```json
{
  "data": [...],
  "count": 100,
  "next_page_token": "range_123_456",
  "has_more": true
}
```

---

### Buscar por IP o ID de documento

```
GET /api/ip_to_country/{ip_or_id}
```

**Parametro de ruta:**

- `ip_or_id`: Direccion IP (ej: "8.8.8.8") o ID de documento (ej: "range_134744072_134744327")

---

### Crear rango IP->pais

```
POST /api/ip_to_country
```

**Body (JSON):**

```json
{
  "start_ip": "1.0.0.0",
  "end_ip": "1.0.0.255",
  "country": "US"
}
```

**Campos:**

- `start_ip` (string, requerido): IP inicial del rango
- `end_ip` (string, requerido): IP final del rango
- `country` (string, requerido): Codigo de pais (2 letras)

---

### Actualizar rango IP->pais

```
PUT /api/ip_to_country/{ip_or_id}
```

**Parametro de ruta:**

- `ip_or_id`: IP o ID de documento del rango a actualizar

**Body (JSON):**

```json
{
  "country": "CA"
}
```

Solo incluir los campos que se desean actualizar.

---

### Eliminar rango IP->pais

```
DELETE /api/ip_to_country/{ip_or_id}
```

**Parametro de ruta:**

- `ip_or_id`: IP o ID de documento del rango a eliminar

---

## Otros Endpoints

### Verificar existencia de record

```
GET /api/exists?host={hostname}
```

**Query parameter:**

- `host` (string, requerido): FQDN a verificar

**Respuesta:**

```json
{
  "exists": true,
  "record_type": "single"
}
```

---

### Obtener geolocalizacion de IP

```
GET /api/ip-geo/{ip_address}
```

**Parametro de ruta:**

- `ip_address`: Direccion IP

**Respuesta:**

```json
{
  "ip": "8.8.8.8",
  "country": "US",
  "region": "na"
}
```

---

### Health check

```
GET /
GET /healthz
```

Sin parametros. Retorna estado de la API.

---

## Ejemplos de Tipos de Records

### Single

```json
{
  "fqdn": "single.example.com",
  "type": "single",
  "ttl": 300,
  "targets": [{ "id": "s1", "ip": "192.0.2.1" }],
  "health": {
    "s1": { "status": "healthy" }
  }
}
```

### Multi (Round-Robin)

```json
{
  "fqdn": "multi.example.com",
  "type": "multi",
  "ttl": 300,
  "targets": [
    { "id": "m1", "ip": "192.0.2.1" },
    { "id": "m2", "ip": "192.0.2.2" },
    { "id": "m3", "ip": "192.0.2.3" }
  ],
  "rr_index": 0,
  "health": {
    "m1": { "status": "healthy" },
    "m2": { "status": "healthy" },
    "m3": { "status": "healthy" }
  }
}
```

### Weight

```json
{
  "fqdn": "weight.example.com",
  "type": "weight",
  "ttl": 300,
  "targets": [
    { "id": "w1", "ip": "192.0.2.1", "weight": 70 },
    { "id": "w2", "ip": "192.0.2.2", "weight": 20 },
    { "id": "w3", "ip": "192.0.2.3", "weight": 10 }
  ],
  "health": {
    "w1": { "status": "healthy" },
    "w2": { "status": "healthy" },
    "w3": { "status": "healthy" }
  }
}
```

### Geo

```json
{
  "fqdn": "geo.example.com",
  "type": "geo",
  "ttl": 300,
  "targets": [
    {
      "id": "us-east",
      "ip": "192.0.2.1",
      "geolocation": { "country": "US", "region": "na" }
    },
    {
      "id": "eu-west",
      "ip": "198.51.100.1",
      "geolocation": { "country": "DE", "region": "eu" }
    }
  ],
  "health": {
    "us-east": { "status": "healthy" },
    "eu-west": { "status": "healthy" }
  }
}
```

### Roundtrip

```json
{
  "fqdn": "roundtrip.example.com",
  "type": "roundtrip",
  "ttl": 300,
  "targets": [
    { "id": "rt1", "ip": "192.0.2.1" },
    { "id": "rt2", "ip": "198.51.100.1" }
  ],
  "health": {
    "rt1": {
      "status": "healthy",
      "rtt": {
        "last_ms": 45,
        "by_region": {
          "na": 15,
          "eu": 120,
          "as": 200
        }
      }
    },
    "rt2": {
      "status": "healthy",
      "rtt": {
        "last_ms": 60,
        "by_region": {
          "na": 100,
          "eu": 25,
          "as": 180
        }
      }
    }
  }
}
```
