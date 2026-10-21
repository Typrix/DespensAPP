# ========================================================
# Dockerfile para DespensAPP Analytics & Admin Server
# Preparado para despliegue Cloud (Render, Railway, AWS, GCP)
# ========================================================
FROM python:3.12-slim

WORKDIR /app

# Evitar escritura de archivos .pyc y forzar buffer directo en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del servidor y archivos estáticos
COPY . .

# Puerto expuesto por defecto
EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0

# Comando de inicio del servidor ASGI Uvicorn
CMD ["python", "server.py"]
