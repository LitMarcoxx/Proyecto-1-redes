#Base image
FROM python:3.11-slim

#Evitar buffers en logs (útil en k8s)
ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

#Crear usuario no-root
RUN groupadd -r appgroup && useradd -r -g appgroup -m -d /home/appuser appuser

WORKDIR /app

#Instalar dependencias del sistema necesarias para build y operaciones
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

#Copiar requirements e instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

#Copiar el código (se asume que el contexto de build contiene la carpeta app/)
COPY . /app

#Ajustar permisos
RUN chown -R appuser:appgroup /app

#Cambiar al usuario no-root
USER appuser

#Puerto expuesto por la API (coincidir con config.PORT si usa otro)
EXPOSE 8080/udp
EXPOSE 8080/tcp

#Variables por defecto (puedes sobrescribir con --env-file o -e)
ENV PORT=8080 \
    UPSTREAM_DNS=8.8.8.8 \
    DEFAULT_TIMEOUT_MS=2000

#Healthcheck (usa /healthz que ya existe en tu FastAPI)
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s \
    CMD curl --fail http://127.0.0.1:8080/healthz || exit 1

#Comando por defecto: uvicorn (bind 0.0.0.0)
#--host 0.0.0.0 para que sea accesible desde fuera del contenedor
#--workers 4 para manejar multiples requests concurrentes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]