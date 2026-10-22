# DespensAPP 🛒📊
> Sistema integral de gestión de despensa y listas de compras con motor de telemetría de producto y consola de analítica en tiempo real para desarrolladores.

---

## 📊 Guía Rápida para ejecutar el proyecto

Este proyecto está diseñado para ser **100% portable y autónomo**. Si descargas o clonas el proyecto en cualquier computadora que no tenga nada instalado previamente, solo necesitas **Python 3.10 o superior, y OJO, solo es recomendable tener como máximo instalada la versión 3.12.X de Python, ya que Kivy suele dar problemas con versiones más actuales**.

### Opción 1: Un Solo Clic (Recomendada en Windows)
Haz doble clic en el archivo:
```text
iniciar.bat
```
El script automáticamente:
1. Detecta tu instalación de Python.
2. Crea el entorno virtual (`venv`) si no existe.
3. Instala todas las dependencias necesarias (`requirements.txt`).
4. Te muestra un menú interactivo para abrir la **App Móvil**, el **Dashboard Web** o ambos a la vez.

---

### Opción 2: Desde la Terminal (PowerShell / CMD)

#### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd DespensAPP
```

#### 2. Crear y activar el entorno virtual
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3. Instalar dependencias
```powershell
pip install -r requirements.txt
```

#### 4. Ejecutar el Dashboard Web de Analítica (Terminal 1)
```powershell
python admin_dashboard/server.py
```
- **Panel Web**: [http://localhost:8000/dashboard](http://localhost:8000/dashboard)
- **Documentación Swagger / OpenAPI**: [http://localhost:8000/docs](http://localhost:8000/docs)

#### 5. Ejecutar la Aplicación Móvil (Terminal 2)
```powershell
python main.py
```

---

## 🗄️ Base de Datos: ¿Qué pasa si el PC no tiene XAMPP?

**No te preocupes por XAMPP ni MySQL:**
- **Si XAMPP está encendido:** El sistema se conectará a MySQL (`despensapp_db`) en el puerto `3306`.
- **Si XAMPP NO está instalado o está apagado:** El sistema activa automáticamente el **modo local SQLite** (`despensapp_local.db`).
  - Crea todas las tablas automáticamente.
  - Inserta los datos iniciales de demostración.
  - Registra las métricas de telemetría.

### Credenciales de Usuario Demo
- **Usuario:** `sofia@despensapp.com`
- **Contraseña:** `despensapp123`

---

## 🏛️ Estructura del Proyecto

```text
DespensAPP/
│
├── controllers/                # [C] Controladores de negocio y eventos (MVC)
│   ├── main_controller.py     # Orquestador central de pantallas y estado
│   ├── auth_controller.py     # Autenticación y hash SHA-256
│   ├── analytics_controller.py # Telemetría y eventos
│   ├── sync_controller.py     # Sincronización offline-to-online
│   ├── cart_controller.py     # Operaciones de carrito
│   ├── pantry_controller.py   # Control de despensa y caducidad
│   └── list_controller.py     # Listas de compras de supermercado
│
├── models/                     # [M] Modelos de dominio y persistencia (MVC)
│   ├── user.py                # Entidad de usuario
│   ├── cart_item.py           # Artículos de carrito
│   ├── pantry_item.py         # Productos de despensa con alertas
│   ├── shopping_list.py       # Listas y productos anotados
│   └── database.py            # Persistencia híbrida (MySQL + SQLite local)
│
├── views/                      # [V] Vistas y componentes gráficos (MVC)
│   ├── theme.py               # Paletas de color reactivas e identidades
│   ├── widgets/               # Componentes interactivos (filas, tarjetas, barras)
│   └── dialogs/               # Modales de captura y formularios
│
├── kv/                         # Plantillas declarativas Kivy
│   ├── dialogs.kv             # Layout de modales y formularios
│   ├── components.kv          # Componentes base
│   └── screens/               # Pantallas (home, cart, pantry, lists, stats, splash)
│
├── database/                   # Infraestructura y esquemas de base de datos
│   ├── database_schema.sql    # DDL con tablas relacionales y telemetría
│   └── db_config.example.json # Plantilla de configuración MySQL
│
├── docs/                       # Documentación y recursos de entrega
│   ├── GUIA_FUNCIONAMIENTO.md # Manual detallado de la aplicación
│   ├── HISTORIAL_CAMBIOS.md   # Registro cronológico de versiones
│   ├── FUNDAMENTACION-UX-UI.md# Sustento del diseño de experiencia
│   └── uso_ia.md              # Bitácora de asistencia por IA
│
├── admin_dashboard/            # Suite de Analítica y Servidor Web FastAPI
│   ├── server.py              # API REST y servidor Jinja2
│   ├── Dockerfile             # Contenedor para despliegue en la nube
│   ├── templates/             # Panel web interactivo con Chart.js
│   └── static/                # Estilos Dark SaaS y lógica de polling
│
├── main.py                     # Punto de entrada de la aplicación móvil (Kivy / KivyMD)
├── main.kv                     # Raíz de navegación de la aplicación
├── iniciar.bat                 # Lanzador y configurador automático para Windows
└── requirements.txt            # Dependencias fijadas del proyecto
```
