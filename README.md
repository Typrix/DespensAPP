# DespensAPP 🛒📊
> Sistema integral de gestión de despensa y listas de compras con motor de telemetría de producto y consola de analítica en tiempo real para desarrolladores.

---

## ⚡ Guía Rápida para Presentación Universitaria (Plug & Play)

Este proyecto está diseñado para ser **100% portable y autónomo**. Si descargas o clonas el proyecto en cualquier computadora de la universidad que no tenga nada instalado previamente, solo necesitas **Python 3.10 o superior**.

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
  - Crea todas las tablas en milisegundos.
  - Inserta los datos iniciales de demostración.
  - Registra las métricas de telemetría sin ningún error.

### Credenciales de Usuario Demo
- **Usuario:** `sofia@despensapp.com`
- **Contraseña:** `despensapp123`

---

## 🏛️ Estructura del Proyecto

```text
DespensAPP/
│
├── main.py                     # Punto de entrada de la aplicación móvil (Kivy / KivyMD)
├── database.py                 # Gestor híbrido de base de datos (MySQL + SQLite fallback)
├── analytics_manager.py        # Motor cliente de telemetría de uso y eventos
├── auth_manager.py             # Lógica de sesiones y autenticación
├── models.py                   # Entidades de datos (User, CartItem, PantryItem, etc.)
├── theme.py                    # Paleta de colores e identidades visuales
├── widgets.py                  # Componentes reutilizables de UI
├── database_schema.sql         # Esquema SQL completo con tablas de telemetría
├── requirements.txt            # Dependencias fijadas del proyecto
├── iniciar.bat                 # Lanzador y configurador automático para Windows
│
├── kv/                         # Vistas declarativas KV divididas por módulo
│   ├── components.kv
│   └── screens/
│       ├── splash_screen.kv
│       ├── home_screen.kv
│       ├── cart_screen.kv
│       ├── cupboard_screen.kv
│       ├── lists_screen.kv
│       └── stats_screen.kv
│
└── admin_dashboard/            # Suite de Analítica y Servidor Web FastAPI
    ├── server.py               # API REST, endpoints analíticos y servidor Jinja2
    ├── Dockerfile              # Empaquetado Docker para despliegue en la nube
    ├── requirements.txt        # Dependencias exclusivas para el contenedor web
    ├── templates/
    │   └── index.html          # Panel web interactivo con Chart.js
    └── static/
        ├── css/dashboard.css   # Estilos modernos Dark SaaS / Linear
        └── js/dashboard.js     # Lógica reactiva de polling cada 3s y gráficos
```
