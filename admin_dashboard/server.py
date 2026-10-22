# -*- coding: utf-8 -*-
"""
Servidor FastAPI para DespensAPP Developer Analytics & Admin Console.
Provee API REST con documentación OpenAPI/Swagger automática (/docs)
y sirve el Dashboard Web reactivo en /dashboard.
"""

import os
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Añadir directorio base y directorio padre al path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from models.database import DatabaseManager

# Inicializar aplicación FastAPI
app = FastAPI(
    title="DespensAPP Developer Analytics & Admin API",
    description="API de telemetría y consola de métricas para la aplicación móvil DespensAPP.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar archivos estáticos y plantillas Jinja2
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Inicializar conexión central a base de datos
db = DatabaseManager()


# Modelos Pydantic para validación y Swagger
class TelemetryEventPayload(BaseModel):
    session_id: Optional[int] = None
    user_id: Optional[int] = None
    event_name: str
    screen_name: Optional[str] = "home"
    duration_seconds: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None


# --------------------------------------------------------
# Rutas Web y Vistas
# --------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    """Redirige automáticamente al panel principal de analítica."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard Web"])
def render_dashboard(request: Request):
    """Renderiza el Dashboard Web de Analítica para Desarrolladores."""
    kpis = db.get_telemetry_kpis()
    kpis["db_status"] = db.status_message
    kpis["is_mysql"] = db.is_mysql

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"kpis": kpis}
    )


# --------------------------------------------------------
# Endpoints de API REST (Telemetría y Métricas)
# --------------------------------------------------------

@app.get("/api/v1/analytics/kpis", tags=["Telemetría"])
def get_kpis():
    """Retorna las métricas consolidadas (KPIs) en tiempo real."""
    data = db.get_telemetry_kpis()
    data["db_status"] = db.status_message
    data["is_mysql"] = db.is_mysql
    return data


@app.get("/api/v1/analytics/screen-times", tags=["Telemetría"])
def get_screen_times():
    """Retorna la distribución de minutos y visitas por pantalla."""
    return db.get_telemetry_screen_times()


@app.get("/api/v1/analytics/recent-events", tags=["Telemetría"])
def get_recent_events(limit: int = 25):
    """Retorna los últimos eventos registrados por la aplicación móvil."""
    return db.get_telemetry_recent_events(limit=limit)


@app.post("/api/v1/telemetry/event", tags=["Telemetría"])
def ingest_event(payload: TelemetryEventPayload):
    """Endpoint receptor de eventos HTTP en segundo plano."""
    event_id = db.log_event(
        session_id=payload.session_id,
        user_id=payload.user_id,
        event_name=payload.event_name,
        screen_name=payload.screen_name or "home",
        duration_seconds=payload.duration_seconds or 0,
        metadata=payload.metadata
    )
    return {"status": "success", "event_id": event_id}


@app.get("/api/v1/health", tags=["Sistema"])
def health_check():
    """Verificación de estado y conectividad del servidor."""
    return {
        "status": "online",
        "service": "DespensAPP Analytics Server",
        "database": db.status_message,
        "is_mysql": db.is_mysql
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n[DespensAPP Analytics Server] Iniciando en http://localhost:{port}/dashboard")
    print(f"[Documentación Swagger] Disponible en http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host=host, port=port, reload=True, app_dir=BASE_DIR)
