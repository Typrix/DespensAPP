# -*- coding: utf-8 -*-
"""
Servidor FastAPI para DespensAPP Developer Analytics & Admin Console.
Provee API REST con documentación OpenAPI/Swagger automática (/docs)
y sirve el Dashboard Web reactivo en /dashboard.
"""

import os
import sys
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
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

import metrics

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
# Versión de los archivos estáticos: obliga al navegador a no usar una copia vieja del CSS/JS
ASSET_VERSION = "2"

# Fuente de métricas. En modo demo (DESPENSAPP_METRICS_DB=demo) solo se lee la base
# simulada y nunca se crea DatabaseManager, así no hay conexión a MySQL ni a la base local real.
if metrics.demo_mode():
    db = None
    source = metrics.SqliteSource(metrics.DEMO_DB_PATH, "Datos simulados")
else:
    from models.database import DatabaseManager
    db = DatabaseManager()
    source = metrics.DatabaseManagerSource(db)


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
    """Renderiza el Dashboard Web de métricas de producto."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "is_demo": source.is_demo,
            "source_label": source.label,
            "periods": metrics.PERIODS,
            "default_period": metrics.DEFAULT_PERIOD,
            "asset_version": ASSET_VERSION,
        },
    )


@app.get("/remote_config.json", tags=["Configuración"])
@app.get("/api/v1/remote-config", tags=["Configuración"])
def get_remote_config():
    """Sirve el archivo de configuración remota para la aplicación móvil y clientes."""
    config_path = os.path.join(PARENT_DIR, "remote_config.json")
    if os.path.isfile(config_path):
        return FileResponse(config_path, media_type="application/json")
    return JSONResponse(
        status_code=404,
        content={"detail": "Archivo remote_config.json no encontrado"}
    )


# --------------------------------------------------------
# Endpoints de API REST (Telemetría y Métricas)
# --------------------------------------------------------

@app.get("/api/v1/analytics/overview", tags=["Telemetría"])
def get_overview(days: int = Query(metrics.DEFAULT_PERIOD, description="Periodo: 7, 30 o 90 días")):
    """KPIs, retención, embudo, series diarias, pantallas, plataformas y eventos del periodo."""
    return metrics.collect(source, days=days)


@app.get("/api/v1/analytics/kpis", tags=["Telemetría"])
def get_kpis(days: int = metrics.DEFAULT_PERIOD):
    """Solo los KPIs del periodo (compatibilidad con clientes anteriores)."""
    data = metrics.collect(source, days=days)
    return {**data.get("kpis", {}), "db_status": source.label, "is_demo": source.is_demo}


@app.get("/api/v1/analytics/screen-times", tags=["Telemetría"])
def get_screen_times(days: int = metrics.DEFAULT_PERIOD):
    """Minutos, visitas y participación por pantalla en el periodo."""
    return metrics.collect(source, days=days).get("screens", [])


@app.get("/api/v1/analytics/recent-events", tags=["Telemetría"])
def get_recent_events(limit: int = 15):
    """Últimos eventos registrados (sin datos personales)."""
    if not source.available():
        return []
    return metrics.recent_events(source, limit=limit)


@app.post("/api/v1/telemetry/event", tags=["Telemetría"])
def ingest_event(payload: TelemetryEventPayload):
    """Endpoint receptor de eventos HTTP en segundo plano."""
    if db is None:
        return JSONResponse(status_code=409, content={"detail": "El modo demo no recibe eventos."})
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
        "database": source.label,
        "is_mysql": bool(db and db.is_mysql),
        "is_demo": source.is_demo,
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"\n[DespensAPP Analytics Server] Iniciando en http://localhost:{port}/dashboard")
    print(f"[Documentación Swagger] Disponible en http://localhost:{port}/docs\n")
    uvicorn.run("server:app", host=host, port=port, reload=True, app_dir=BASE_DIR)
