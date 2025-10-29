## Participantes

- Ian Murillo Campos- 2020148871
- Mariana Quesada Sánchez- 2021579438
- Gerardo Gómez Brenes- 2022089271
- Gianmarco Oporta Pérez- 2022141511

## Instrucciones

Para instalar toda la arquitectura y poder probar nuestros servicios, primero debemos tener _kubectl_ y _Docker_ instalados. Luego, desde la raíz del proyecto, ejecutamos los siguientes comandos:

docker build -t dns-api:latest -f .\dns-api\Docker\Dockerfile .\dns-api
docker build -t dns-interceptor:latest -f .\dns-interceptor\docker\Dockerfile .

Con las imagenes de Docker levantadas se ejecuta el siguiente comando para desplegar con HELM todo el proyecto:

helm upgrade --install dns-project .\chart --namespace dns --create-namespace

Con el proyecto desplegado para correrlo se ejecutan los siguientes comandos:

docker compose down -v
docker compose up --build

## Pruebas

### DNS-Interceptor:

- Hay que levantar un pod de prueba que se comunique con el interceptor con el comando "kubectl run -it --rm --restart=Never dns-tester -n dns --image=busybox:stable -- sh"

- Hay 2 casos posibles query estándar (QR = 0 y OPCODE = 0) y query no estándar (QR != 0 y/o OPCODE != 0)

## Caso query NO estándar:

- Ejecutar dentro del pod el comando "nslookup -type=SOA example.com dns-api-dns-project-interceptor"

- Debe retornar lo siguiente:
  Server: dns-api-dns-project-interceptor
  Address: 10.96.220.74:53

Non-authoritative answer:
example.com
origin = ns.icann.org
mail addr = noc.dns.icann.org
serial = 2025082261
refresh = 7200
retry = 3600
expire = 1209600
minimum = 3600

## Caso query estándar:

### \*\*Caso tipo "Single":

- Ejecutar dentro del pod el comando "nslookup single.example.com dns-api-dns-project-interceptor"

- Debe retornar lo siguiente:
  Server: dns-api-dns-project-interceptor
  Address: 10.96.220.74:53

Non-authoritative answer:
Name: single.example.com
Address: 198.135.127.5

### \*\*Caso tipo "Multi":

- Ejecutar dentro del pod el comando "for i in $(seq 1 6); do nslookup multi.example.com dns-api-dns-project-interceptor; echo ""; done"

- Debe retornar lo siguiente:

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.126.10

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.127.10

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.126.10

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.127.10

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.126.10

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: multi.example.com
Address: 198.135.127.10

### \*\*Caso tipo "Weight":

- Ejecutar dentro del pod el comando "for i in $(seq 1 20); do nslookup weight.example.com dns-api-dns-project-interceptor | grep Address; done"

- Debe retornar lo siguiente:

Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.136.186.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20
Address: 10.96.220.74:53
Address: 198.135.167.20

### \*\*Caso tipo "roundtrip":

- Debe retornar lo siguiente:

Server: dns-api-dns-project-interceptor
Address: 198.137.87.70

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: roundtrip.example.com
Address: 198.137.87.70

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: roundtrip.example.com
Address: 198.137.87.70

Server: dns-api-dns-project-interceptor
Address: 10.96.220.74:53

Non-authoritative answer:
Name: roundtrip.example.com
Address: 198.137.87.70

Address: 10.96.220.74:53

Non-authoritative answer:
Name: roundtrip.example.com
Address: 198.137.87.70

### \*\*Caso tipo "geo":

- Ejecutar dentro del pod el comando "nslookup geo.example.com dns-api-dns-project-interceptor"

- Debe retornar lo siguiente:
  Server: dns-api-dns-project-interceptor
  Address: 10.96.220.74:53

### DNS-API:

El DNS-API es un servicio REST desarrollado en Python con FastAPI que actúa como el backend inteligente del sistema. Se encarga de almacenar y consultar los registros DNS en Firebase Firestore, además de implementar los cinco algoritmos de balanceo de carga.

#### Componentes principales:

El API tiene varios módulos que trabajan juntos. El archivo main.py define todos los endpoints HTTP disponibles. El módulo crud.py maneja todas las operaciones de lectura y escritura a Firebase. El resolver_logic.py se encarga de reenviar consultas DNS a servidores upstream cuando es necesario. El resolve_ip.py contiene la lógica de cada algoritmo de balanceo. Finalmente, utils.py proporciona funciones auxiliares como la geolocalización de direcciones IP.

#### Base de datos Firebase:

El sistema utiliza dos colecciones principales en Firestore. La colección records almacena todos los registros DNS con su configuración de algoritmo y lista de servidores destino. Cada registro tiene un campo host que es el nombre de dominio, un campo type que indica el algoritmo a usar, y un array de targets con las direcciones IP disponibles. La colección ip_to_country contiene más de 500 mil documentos que mapean rangos de direcciones IP a países, necesario para el algoritmo geo.

#### Algoritmos implementados:

El algoritmo single siempre retorna la misma IP configurada, es el más simple y no hace balanceo real. El algoritmo multi implementa round-robin rotando entre todas las IPs disponibles de forma cíclica. El algoritmo weight distribuye las peticiones según pesos asignados a cada servidor, los que tienen mayor peso reciben más tráfico. El algoritmo geo selecciona el servidor del mismo país que el cliente que hace la consulta usando la IP de origen. El algoritmo roundtrip mide el tiempo de respuesta de cada servidor y retorna el que responde más rápido.

#### Pruebas del API:

Para probar el API se puede usar Postman u otra herramienta similar. El servicio corre en http://localhost:8080 y también tiene documentación interactiva en http://localhost:8080/docs.

_Verificar que el servicio está corriendo:_

GET http://localhost:8080/

Respuesta esperada: {"running": "ok"}

_Verificar si existe un dominio en la base de datos:_

GET http://localhost:8080/api/exists?host=single.example.com

Respuesta esperada: {"exists": true, "record_type": "single"}

_Resolver un dominio con el algoritmo configurado:_

POST http://localhost:8080/api/resolve

Body (JSON):

json
{
"host": "multi.example.com",
"client_ip": "8.8.8.8"
}

Retorna la IP seleccionada por el algoritmo y datos sobre la salud del servidor.

_Procesar una query DNS en base64:_

POST http://localhost:8080/api/dns_resolver

Body (JSON):

json
{
"base64_data": "AAABAAABAAAAAAAAAWE2Z29vZ2xlA2NvbQAAAQAB",
"timeout_ms": 2000
}

Retorna la respuesta del servidor upstream codificada en base64 junto con el tiempo de respuesta.

## DNS HealthChecker

El HealthChecker es un servicio en C que simula varias regiones del mundo y, para cada target de cada record, realiza mediciones de latencia (RTT). Con esas mediciones el sistema decide qué targets están **healthy** por **mayoría** entre regiones.
El HealthChecker publica sus resultados en la API (`/api/update_health`), y la API los fusiona en Firestore dentro del documento del record.

### Regiones simuladas

Por defecto se simulan estas regiones (configurables en `regions.h`):

- **na** (Norteamérica)
- **eu** (Europa)
- **sa** (Sudamérica)
- **ca** (Canadá)
- **as** (Asia)

El sistema también admite labels adicionales de “nodos medidores” (p. ej. `us-east`, `eu-west`, `asia-pacific`) si se desean métricas más finas.

## DNS-UI

Desarrollada en React, la DNS-UI permite administrar los registros y rangos IP del sistema de forma visual. Se comunica con el servicio DNS-API mediante peticiones REST y facilita la gestión de la información almacenada.

La pantalla principal muestra la lista de registros DNS existentes, indicando el dominio, tipo y estado de cada uno. Desde ahí se pueden editar o eliminar registros y acceder a dos pantallas adicionales: **IP-to-Country** y **Crear nuevo registro DNS**.

Los principales componentes son:

1. **DNS Registers:** permite visualizar, crear, editar y eliminar registros de tipo single, multi, weight, roundtrip y geo.
2. **IP-to-Country:** administra los rangos IP asociados a países, mostrando la IP inicial, IP final, país y código ISO.
3. **Formulario de creación y edición:** permite agregar nuevos registros o modificar los existentes mediante campos dinámicos según el tipo seleccionado.

La interfaz mantiene un diseño uniforme con tarjetas y modales, y se ejecuta localmente en http://localhost:5173.

## Recomendaciones

1. Actualizar la base de datos de rangos IP regularmente porque las asignaciones cambian con el tiempo.

2. Implementar caché para los registros más consultados y reducir la carga sobre Firebase.

3. Configurar límites de peticiones por cliente para prevenir abusos del servicio.

4. Monitorear la disponibilidad de los servidores DNS upstream como Google DNS.

5. Usar logs con niveles de severidad para facilitar el debugging en producción.

6. Validar todos los datos de entrada para prevenir inyecciones o datos malformados.

7. Configurar backups automáticos de Firestore para recuperar información si es necesario.

8. Mantener documentación actualizada de las estructuras de datos en Firebase.

9. Usar balanceadores de carga para distribuir tráfico entre múltiples instancias.

10. Establecer métricas de rendimiento y monitorear los tiempos de respuesta del sistema.

## Conclusiones

1. La separación entre interceptor y API permite actualizar la lógica sin afectar la recepción de queries DNS.

2. Kubernetes y Helm facilitan el despliegue y permiten escalar componentes de forma independiente.

3. Los múltiples algoritmos de balanceo ofrecen flexibilidad para diferentes casos de uso.

4. Firebase Firestore funciona bien pero requiere optimización de queries por las limitaciones en índices.

5. El interceptor en C maneja paquetes DNS de forma eficiente a bajo nivel.

6. La paginación fue necesaria para manejar grandes volúmenes de datos sin afectar el rendimiento.

7. Docker garantiza que el entorno de desarrollo sea consistente con producción.

8. Los algoritmos de roundtrip y geo introducen latencia adicional pero mejoran la experiencia del usuario.

9. La documentación automática de FastAPI facilita entender y probar los endpoints.

10. El manejo de errores y timeouts es fundamental para mantener la estabilidad del sistema.
