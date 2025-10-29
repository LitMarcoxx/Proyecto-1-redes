FROM debian:stable-slim

# Instalar herramientas necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc make libc6-dev libcurl4-openssl-dev net-tools \
    && rm -rf /var/lib/apt/lists/*



# Crear usuario no root
RUN groupadd -r interceptor && useradd -r -g interceptor interceptor

WORKDIR /app

# Copiar código fuente
COPY ./src/ /app/

# Compilar todos los archivos C
RUN gcc -o dns-interceptor main.c dnsParser.c -lpthread -lcurl


# Cambiar permisos y usuario
RUN chown -R interceptor:interceptor /app
USER interceptor

# Exponer puerto UDP 53 dentro del contenedor
EXPOSE 53/udp

# Comando por defecto
CMD ["./dns-interceptor"]