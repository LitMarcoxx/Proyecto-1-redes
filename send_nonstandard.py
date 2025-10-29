#!/usr/bin/env python3
# send_nonstandard.py
# Uso: ./send_nonstandard.py <fqdn> [port]
# Ejemplo: ./send_nonstandard.py single.example.com 1053
#
# Crea una query A y fuerza OPCODE=1 (paquete "no estándar"), la envía por UDP
# al interceptor y muestra la respuesta (intenta decodificar con dnspython).

import socket, dns.message, sys

def main():
    if len(sys.argv) < 2:
        print("Uso: send_nonstandard.py <fqdn> [port]")
        sys.exit(1)

    name = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1053  # default 1053 para pruebas

    # Crear query normal
    q = dns.message.make_query(name, "A")
    wire = bytearray(q.to_wire())

    # flags en bytes 2-3 (big endian)
    orig = int.from_bytes(wire[2:4], "big")
    # Limpiar OPCODE (bits 11..14) y setear OPCODE=1
    orig_cleared = orig & 0x87FF
    new = orig_cleared | (1 << 11)
    wire[2:4] = new.to_bytes(2, "big")

    print(f"Enviando paquete no-estándar (OPCODE=1) para {name} a 127.0.0.1:{port}")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(6)
    try:
        s.sendto(bytes(wire), ("127.0.0.1", port))
    except Exception as e:
        print("Error enviando paquete:", e)
        sys.exit(2)

    try:
        data, addr = s.recvfrom(65535)
        print("✅ Respuesta recibida:", len(data), "bytes desde", addr)
        # Intentar parsear con dnspython para mostrar algo legible
        try:
            msg = dns.message.from_wire(data)
            print("\n--- Contenido de la respuesta DNS (texto) ---")
            print(msg.to_text())
        except Exception:
            print("No se pudo interpretar con dnspython. Hex (primeros 128 bytes):")
            print(data[:128].hex())
    except socket.timeout:
        print("❌ Timeout: no se recibió respuesta.")
    finally:
        s.close()

if __name__ == "__main__":
    main()
