# Historial Técnico de Cambios - DespensAPP 🛒📋
> Registro detallado de las mejoras arquitectónicas, nuevas funcionalidades, optimizaciones de UI/UX y componentes de telemetría y sincronización implementados en el proyecto.

---

## 📑 Resumen General de Hitos

| Hito | Área / Módulo | Descripción Principal |
| :--- | :--- | :--- |
| **1. Modularización** | Arquitectura & KV | Desacoplamiento de archivos monolíticos en módulos especializados (`kv/screens/`, `theme.py`, `widgets.py`). |
| **2. Datos Reales** | Base de Datos | Eliminación total de datos simulados/hardcodeados; cálculo dinámico de estadísticas y resúmenes. |
| **3. Transiciones Fluidas** | UI / Animaciones | Eliminación del fondo negro en cambios de pantalla (`clearcolor=[0, 0, 0, 0]`). |
| **4. Pantalla de Carga** | UX / Bienvenida | Implementación de `SplashScreen` progresiva con barra de carga y mensajes de estado en 3 fases. |
| **5. Motor de Telemetría** | Analítica de Producto | Registro de sesiones de uso, tiempos de permanencia por pantalla y eventos de usuario en la app móvil. |
| **6. Dashboard Web Admin** | FastAPI & Frontend | Consola web reactiva con diseño SaaS oscuro, gráficos Chart.js, feed en vivo y API Swagger. |
| **7. Portabilidad 1-Clic** | Despliegue Local | Creación de `requirements.txt`, script lanzador `iniciar.bat` y `README.md` autónomo. |
| **8. Motor de Sincronización**| Offline-First & Auth | Salvaguardas de registro offline y sincronización inteligente de SQLite a MySQL sin duplicados. |
| **9. Vencimiento & Listas**| Despensa & Supermercado | Fechas de vencimiento con opción no perecible y listas interactivas estilo papel (tachado y edición). |

---

## 🛠️ Detalle de Cambios por Hito

### Hito 1: Modularización Integral del Proyecto
- **Problema previo:** El código de la interfaz gráfica estaba concentrado en un archivo `main.kv` monolítico de cientos de líneas, dificultando el mantenimiento y la colaboración.
- **Solución implementada:**
  - Se crearon archivos KV independientes dentro de la carpeta `kv/screens/`:
    - `splash_screen.kv`: Pantalla de bienvenida y carga.
    - `home_screen.kv`: Tarjetas de resumen diario y accesos directos.
    - `cart_screen.kv`: Vista del carrito de compras y totales.
    - `cupboard_screen.kv`: Inventario de despensa con estados de stock.
    - `lists_screen.kv`: Gestión de listas temáticas de compras.
    - `stats_screen.kv`: Gráficos de barras y métricas de consumo.
  - Se extrajeron los estilos comunes a `kv/components.kv`.
  - Se separó la lógica de tema (`theme.py`), widgets personalizados (`widgets.py`) y formularios emergentes (`dialogs.py`).

---

### Hito 2: Eliminación de Datos Hardcodeados (Datos 100% Reales)
- **Problema previo:** La pantalla de Inicio y la de Estadísticas mostraban valores fijos de prueba que no cambiaban al agregar productos o interactuar con el carrito.
- **Solución implementada:**
  - Se añadió el método `get_user_statistics(user_id)` en `database.py`.
  - Ahora se calculan en tiempo real:
    - **Gasto mensual y semanal real:** Basado en la sumatoria de precios de los artículos comprados.
    - **Total de productos adquiridos:** Conteo real de ítems completados.
    - **Ranking de productos más comprados:** Agrupación y cálculo proporcional de porcentajes para las barras de progreso (`CustomProgressBar`).
    - **Alertas de stock:** Conteo real de productos en estado *Reponer* o *Por agotarse*.

---

### Hito 3: Corrección de Transición Visual (Sin Fondo Negro)
- **Problema previo:** Al cambiar entre secciones (por ejemplo, de Inicio a Despensa), la pantalla parpadeaba con un fondo negro intermedio que rompía la estética visual.
- **Causa raíz:** En Kivy, el widget `ScreenManager` con `FadeTransition` usa por defecto un búfer de limpieza opaco (`clearcolor=[0, 0, 0, 1]` = color negro).
- **Solución técnica:**
  - Se configuró la transición en `main.py` con `clearcolor=[0, 0, 0, 0]` (transparencia total) y una duración optimizada de `0.15s`.
  - El cambio de pantalla ahora es suave y mantiene los fondos del tema activo sin parpadeos.

---

### Hito 4: Pantalla de Bienvenida Progresiva (*SplashScreen*)
- **Problema previo:** La aplicación tardaba en inicializar y abría directamente la interfaz principal de golpe.
- **Solución implementada:**
  - Se diseñó una pantalla de bienvenida minimalista y moderna con el logotipo de DespensAPP, spinner de carga y barra de progreso animada.
  - Carga secuencial en 3 fases mediante eventos programados (`Clock.schedule_once`):
    1. **Fase 1 (0% - 35%):** Conexión con base de datos, inicialización de telemetría y autenticación.
    2. **Fase 2 (35% - 70%):** Sincronización de usuario, listas, compras e inventario de despensa.
    3. **Fase 3 (70% - 100%):** Transición fluida a la pantalla de Inicio o apertura del modal de login si no hay sesión previa.

---

### Hito 5: Motor de Telemetría en la App Móvil (`analytics_manager.py`)
- **Objetivo:** Medir cómo se usa la aplicación (métricas comerciales y de producto útiles para desarrolladores y evaluación académica).
- **Solución implementada:**
  - Se creó la clase `AnalyticsManager`:
    - **Medición de sesiones:** Registra fecha de inicio, fecha de cierre y duración exacta en segundos.
    - **Permanencia por pantalla:** Cronometra cuántos segundos/minutos pasa el usuario en `home`, `cart`, `cupboard`, `lists` y `stats`.
    - **Eventos clave:** Captura eventos puntuales como `app_opened`, `app_closed`, `pantry_item_added`, `cart_item_added`, `user_authenticated` y `user_logout`.
  - Nuevas tablas en base de datos: `app_sessions` y `app_events`.

---

### Hito 6: Consola Web de Administrador con FastAPI (`admin_dashboard/`)
- **Objetivo:** Disponer de una plataforma web moderna para que los desarrolladores monitoreen las métricas sin necesidad de instalar la app en su equipo.
- **Solución implementada:**
  - **Backend (`admin_dashboard/server.py`):**
    - Construido sobre FastAPI y servidor ASGI Uvicorn.
    - Endpoints REST: `/api/v1/analytics/kpis`, `/screen-times`, `/recent-events` y `/health`.
    - Documentación interactiva autogenerada en `/docs` (Swagger UI) y `/redoc`.
  - **Frontend (`templates/index.html`, `static/css/dashboard.css`, `static/js/dashboard.js`):**
    - **Diseño SaaS oscuro:** Tipografía Google Font *Plus Jakarta Sans*, tarjetas con sombras multicapa y punto pulsante en verde neón.
    - **Gráficos interactivos con Chart.js:** Gráfico de dona (tiempo por sección) y gráfico de barras (frecuencia de visitas).
    - **Feed reactivo en vivo:** Tabla de eventos que se actualiza cada 3 segundos mediante polling asíncrono.
  - **Preparación Cloud:** Incluye `Dockerfile` y `requirements.txt` listos para desplegar en Render, Railway o AWS.

---

### Hito 7: Portabilidad Total y Lanzador 1-Clic
- **Objetivo:** Permitir que el proyecto se clone en cualquier computadora de la universidad y funcione de inmediato sin configuraciones engorrosas.
- **Solución implementada:**
  - `requirements.txt` en la raíz con versiones fijas y compatibles de Kivy 2.3.1, KivyMD 2.0, FastAPI, PyMySQL y Uvicorn.
  - `iniciar.bat`: Script para Windows que detecta Python, crea el entorno virtual automáticamente, instala las dependencias y ofrece un menú para lanzar la App o el Dashboard Web.
  - `README.md`: Documentación completa de puesta en marcha rápida.

---

### Hito 8: Motor de Sincronización Offline y Salvaguardas de Autenticación
- **Objetivo:** Resolver qué ocurre cuando la app se usa sin conexión (o sin XAMPP) y luego se recupera la conexión a MySQL.
- **Solución implementada:**
  - **Salvaguardas en `auth_manager.py`:**
    - Se bloquea la creación de cuentas nuevas si no hay conexión a la base central (evita colisiones de correos y cuentas huérfanas).
    - Se permite el acceso a la despensa y carritos locales si el usuario ya tenía su sesión iniciada (`session.json`).
    - En el modal de autenticación (`dialogs.py`), la pestaña "Crear Cuenta" advierte inmediatamente si se está en Modo Local.
  - **Motor `SyncManager` (`sync_manager.py`):**
    - Al recuperar conexión e iniciar sesión, lee los productos de despensa, compras y eventos creados en SQLite.
    - Mapea los registros mediante el correo del usuario (`email`) a su `user_id` en MySQL.
    - Realiza inserción limpia sin duplicar elementos que ya existían.
    - Vacía la cola local una vez respaldada en el servidor.

---

### Hito 9: Fecha de Vencimiento en Despensa y Listas de Supermercado Interactivas (Estilo Papel)
- **Problema previo:**
  - Al ingresar productos a la despensa no existía forma de indicar cuándo vencían ni distinguir alimentos perecibles de no perecibles (como sal, azúcar o aceite). Además, la app no emitía avisos prioritarios de productos próximos a caducar.
  - Las listas de compras no permitían anotar productos como en una lista de papel de supermercado; al pulsar una lista se abría un diálogo genérico en vez de mostrar los alimentos anotados para ir tachándolos mientras se compra.
- **Solución implementada:**
  - **Fecha de Vencimiento en Despensa:**
    - Se agregó el campo `expiration_date` en la tabla `pantry_items` tanto en MySQL como en SQLite local, con migración automática y segura.
    - Se incorporó en el modal `AddPantryItemModal` un campo para ingresar fecha (`AAAA-MM-DD`) y un botón toggle interactivo: `✓ Sin fecha de vencimiento (no perecible)` para productos eternos.
    - El modelo `PantryItem` calcula en tiempo real `days_until_expiration`, `is_expired`, `is_expiring_soon` y estados descriptivos (`Vence hoy`, `Vence en 2 días`, `Venció hace 1d`, `Sin vencimiento`).
    - En la vista de Despensa, cada fila exhibe la fecha y su color de alerta (verde, ámbar o rojo).
    - En la pantalla de Inicio (`home`), la tarjeta de alerta destaca prioritariamente si hay algún alimento vencido o por caducar pronto.
    - En el modal de detalle del producto (`PantryItemDetailModal`), se puede visualizar la fecha y modificarla rápidamente mediante el botón `Cambiar`.
  - **Listas de Supermercado Interactivas (Estilo Papel):**
    - Se creó la tabla `shopping_list_items (id, list_id, name, is_checked, created_at)` en MySQL y SQLite.
    - Al crear una lista (`AddShoppingListModal`), ahora es posible anotar productos iniciales separados por coma o salto de línea (ej: *Leche, Huevos, Pan, Café*).
    - Al pulsar la tarjeta de una lista en la pantalla de listas, se abre `ShoppingListDetailModal` simulando una lista de compras de papel sin precios:
      - Cada producto anotado cuenta con un botón circular para tacharlo (`[s]nombre[/s]`) al echarlo al carro.
      - Botón de lápiz (`✎`) para corregir el nombre si el usuario se equivocó al escribirlo.
      - Botón de eliminar (`✕`) para remover un producto individual.
      - Campo superior de adición rápida con botón `+` para seguir agregando cosas sobre la marcha.
      - Contador reactivo en tiempo real (ej. *4 productos anotados · 2 tachados*).
      - Opciones para renombrar la lista o eliminarla por completo.
