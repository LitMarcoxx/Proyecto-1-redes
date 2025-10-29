"""
Reenvio de queries DNS a servidores upstream via UDP/TCP.
Maneja queries no-estandar o que no existen en Firebase.
Soporta fallback TCP cuando respuesta UDP esta truncada.
"""

import base64
import socket
import time
from typing import Tuple

# --- CONFIGURACION ---
UPSTREAM_HOST = "8.8.8.8"    # Servidor DNS upstream (Google DNS por defecto)
UPSTREAM_PORT = 53           # Puerto DNS estandar
DEFAULT_TIMEOUT_MS = 2000    # Timeout por defecto en milisegundos
MAX_PAYLOAD_BYTES = 65535    # Limite razonable para un paquete DNS (64KB)
RECV_BUF = 65535             # Tamaño de buffer para recvfrom

# --- FUNCIONES AUXILIARES ---

def _convert_milliseconds_to_seconds(milliseconds: int) -> float:
    """Convierte milisegundos a segundos (minimo 1ms)."""
    return max(0.001, milliseconds / 1000.0)

def _check_if_dns_response_is_truncated(dns_response_bytes: bytes) -> bool:
    """Verifica si el flag TC (truncation) esta activo en la respuesta DNS."""
    if len(dns_response_bytes) < 4:
        return False
    dns_header_flags = int.from_bytes(dns_response_bytes[2:4], "big")
    return (dns_header_flags & 0x0200) != 0

def send_dns_query_via_udp(dns_query_payload: bytes, upstream_server: str, server_port: int, timeout_milliseconds: int) -> Tuple[bytes, int, str]:
    """Envia query DNS via UDP y retorna (response_bytes, rtt_ms, server_address)."""
    timeout_seconds = _convert_milliseconds_to_seconds(timeout_milliseconds)
    query_start_time = time.monotonic()

    # Resolver direccion del servidor (soporta nombres DNS e IPs)
    # Retorna lista de posibles direcciones
    address_info_list = socket.getaddrinfo(upstream_server, server_port, proto=socket.IPPROTO_UDP)
    
    # Usar la primera direccion disponible
    socket_family, socket_type, protocol, canonical_name, socket_address = address_info_list[0]

    # Crear socket UDP, enviar query y esperar respuesta
    with socket.socket(socket_family, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.settimeout(timeout_seconds)
        try:
            # Enviar los bytes del query DNS
            udp_socket.sendto(dns_query_payload, socket_address)
            
            # Esperar la respuesta (hasta RECV_BUF bytes)
            dns_response, server_address_info = udp_socket.recvfrom(RECV_BUF)

            # Calcular RTT (tiempo total desde envio hasta recepcion)
            round_trip_time_ms = int((time.monotonic() - query_start_time) * 1000)

            # Formatear direccion del servidor como "IP:Puerto"
            server_address_string = f"{server_address_info[0]}:{server_address_info[1]}"
            
            return dns_response, round_trip_time_ms, server_address_string
            
        except socket.timeout:
            # Re-lanzar timeout para que el caller lo maneje
            raise
        except Exception:
            # Re-lanzar cualquier otro error de red
            raise

def send_dns_query_via_tcp(dns_query_payload: bytes, upstream_server: str, server_port: int, timeout_milliseconds: int) -> bytes:
    """Envia query DNS via TCP (fallback cuando UDP esta truncado)."""
    timeout_seconds = _convert_milliseconds_to_seconds(timeout_milliseconds)

    # Resolver direccion del servidor
    address_info_list = socket.getaddrinfo(upstream_server, server_port, proto=socket.IPPROTO_TCP)
    
    # Usar la primera direccion disponible
    socket_family, socket_type, protocol, canonical_name, socket_address = address_info_list[0]

    # Crear socket TCP, conectar, enviar y recibir
    with socket.socket(socket_family, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.settimeout(timeout_seconds)
        tcp_socket.connect(socket_address)
        
        # En DNS sobre TCP: 2 bytes BigEndian con la longitud + payload
        payload_length_prefix = len(dns_query_payload).to_bytes(2, "big")
        tcp_socket.sendall(payload_length_prefix + dns_query_payload)

        # Leer 2 bytes de longitud de la respuesta
        response_length_bytes = tcp_socket.recv(2)
        if len(response_length_bytes) < 2:
            raise RuntimeError("TCP read length failed")
        expected_response_length = int.from_bytes(response_length_bytes, "big")

        # Inicializar buffer para almacenar la respuesta completa
        response_data = bytearray()

        # Leer datos hasta completar expected_response_length
        while len(response_data) < expected_response_length:
            # Calcular cuantos bytes faltan
            remaining_bytes = expected_response_length - len(response_data)
            
            # Intentar recibir los bytes restantes
            data_chunk = tcp_socket.recv(remaining_bytes)
            
            # Si no se reciben datos, la conexion se cerro
            if not data_chunk:
                break
            
            # Agregar los bytes recibidos al buffer
            response_data.extend(data_chunk)
            
        return bytes(response_data)

# --- FUNCION PRINCIPAL ---

def process_dns_query_from_base64(dns_query_base64: str, timeout_milliseconds: int = DEFAULT_TIMEOUT_MS, upstream_dns_server: str = UPSTREAM_HOST, dns_server_port: int = UPSTREAM_PORT):
    """Procesa query DNS en Base64 y lo reenvia a servidor upstream."""
    # 1) Decodificar Base64
    try:
        dns_query_bytes = base64.b64decode(dns_query_base64, validate=True)
    except Exception:
        raise ValueError("invalid_base64")

    if len(dns_query_bytes) == 0 or len(dns_query_bytes) > MAX_PAYLOAD_BYTES:
        raise ValueError("payload_size_invalid")

    # 2) Intentar UDP
    try:
        dns_response_bytes, round_trip_time_ms, contacted_server = send_dns_query_via_udp(dns_query_bytes, upstream_dns_server, dns_server_port, timeout_milliseconds)
    except socket.timeout:
        # upstream no respondió en UDP dentro del timeout
        raise
    except Exception as network_error:
        # Problema de red (DNS unreachable, getaddrinfo falló, etc)
        raise

    # 3) Si la respuesta UDP está truncada (TC), intentar TCP fallback
    try:
        if _check_if_dns_response_is_truncated(dns_response_bytes):
            # TCP fallback
            tcp_dns_response = send_dns_query_via_tcp(dns_query_bytes, upstream_dns_server, dns_server_port, timeout_milliseconds)
            dns_response_bytes = tcp_dns_response
            contacted_server = f"{upstream_dns_server}:{dns_server_port} (tcp)"
            # round_trip_time_ms queda como el medido por UDP; para medir bien haría falta cronometrar TCP también
    except Exception:
        # Si TCP falla, conservamos la respuesta UDP truncada (o podríamos elegir fallar).
        pass

    # 4) Codificar respuesta y devolver
    return {
        "payload_b64": base64.b64encode(dns_response_bytes).decode(),
        "server": contacted_server,
        "rtt_ms": int(round_trip_time_ms)
    }