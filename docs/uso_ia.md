# Registro de Uso de IA - DespensAPP

## Entrada / Prompt del Usuario (Diseño Inicial e Implementación)
> "quiero que lo dejes como en las capturas, pero igual igual sin errores, tomate tu tiempo"

---

## Acciones Realizadas

1. **Reestructuración y Diseño Visual (main.py y main.kv)**:
   - Se ajustó la resolución de la ventana a un formato móvil estándar (390x780) proporcional a las capturas.
   - Se implementó un sistema de paleta de colores reactiva para alternar fluidamente entre **Modo Claro** y **Modo Oscuro**.

2. **Encabezado Global y Menú de Perfil (Captura 1)**:
   - Encabezado con insignia de hoja redondeada, título `DespensAPP` y tag dinámico (`ESTADÍSTICAS`, `LISTAS`, `DESPENSA`, `COMPRAS`, `INICIO`).
   - Botón de avatar circular `"SO"` que abre/cierra un menú flotante con datos de usuario (`Sofía Martínez`), accesos (`Mi perfil`, `Notificaciones`, `Preferencias`) y un `MDSwitch` funcional para cambiar el tema.

3. **Implementación de Pantallas según Prototipo**:
   - **Estadísticas (Capturas 1 y 2)**: Tarjetas métricas lado a lado (Gasto mensual `$182.400`, Productos comprados `47`), ranking de productos con barras de progreso personalizadas (`CustomProgressBar`) y tarjeta inferior *"Buen progreso"*.
   - **Listas (Captura 3)**: Tarjetas blancas con insignias en tonos pastel (`Compra quincenal`, `Cena de cumpleaños`, `Limpieza del hogar`) y botón circular verde `+`.
   - **Despensa (Captura 4)**: Lista de inventario con divisores, iconos y estados de stock con sus respectivos colores (`Suficiente`, `Reponer`, `Por agotarse`).
   - **Compras (Captura 5)**: Carrito de compras con casillas circulares interactivas (`CartItemRow`), subtítulo por lista, precios unitarios y total estimado (`$8.800`).
   - **Inicio**: Tarjetas de resumen general (gasto semanal, alimentos por caducar y receta recomendada).

4. **Navegación Inferior (Dock)**:
   - Barra con 5 pestañas (`Inicio`, `Compras`, `Despensa`, `Listas`, `Estadísticas`).
   - Indicador visual activo con píldora redondeada en verde suave e iconos/etiquetas contrastadas.

5. **Pruebas y Verificación**:
   - Se ejecutó suite de pruebas automatizada sobre el entorno virtual (`venv`) validando el cambio entre pantallas, la apertura del modal y la alternancia de temas con **0 errores**.

---

## Entrada / Prompt del Usuario (Corrección de Bloqueo de Interacción)
> "ya creo que esta bien la app, pero no me deja interactuar con nada, como si estuviera pegado ahi en la interfaz, arregla eso sin errores porfa para poder navegar bien"

---

## Diagnóstico y Solución del Bug

1. **Causa raíz identificada**:
   - Existía un widget `Button` de pantalla completa (`touch_catcher`) con `disabled: True` colocado en la capa superior del diseño para detectar clics fuera del modal de perfil. En el motor de eventos de Kivy, cualquier `Button` deshabilitado intercepta y consume todos los eventos táctiles (`on_touch_down`), impidiendo que los toques lleguen a los botones de navegación, tarjetas, scroll y listas inferiores.

2. **Corrección implementada**:
   - Se eliminó la capa superpuesta permanente del layout raíz en [main.kv](file:///c:/Users/sebas/Documents/GitHub/DespensAPP/main.kv).
   - Se implementó la clase `ProfileModalView` heredando de `ModalView` en [main.py](file:///c:/Users/sebas/Documents/GitHub/DespensAPP/main.py). Esta ventana modal solo se conecta a la ventana gráfica cuando se pulsa el botón `"SO"` y se desconecta de forma limpia e independiente al cerrarse (`auto_dismiss: True`), garantizando cero interferencias con la interacción del usuario.
   - Se convirtió la raíz a un `BoxLayout` directo, eliminando capas intermedias innecesarias.

3. **Verificación**:
   - Se ejecutó prueba interactiva de toques y despacho de eventos con 100% de éxito: navegación inmediata entre las 5 pestañas, apertura/cierre del modal de perfil, interacción con las casillas del carrito y scroll activo en todas las vistas.

---

## Entrada / Prompt del Usuario (Documentación y Reestructuración de Repositorio)
> "necesito que me escribas el readme.md dime que tipo de informacion necestias y te la doy"
> "proyecto universitario, se uso python 3.12.10 con kivy kivymd kivy[base], sin licencia y los autores son los de la foto y Braulio Palma brauliodeus"
> "quiero q organices un poco la estructura y uso de ia, el pdf y el logo junto a la documentacion vayan dentro de una carpeta llamada docs"

---

## Acciones Realizadas

1. **Elaboración de Documentación Central (README.md)**:
   - Se redactó una guía completa con insignias dinámicas, síntesis de la propuesta de valor, descripción funcional de las 5 pantallas, stack tecnológico (Python 3.12.10, Kivy, KivyMD) y guía de instalación paso a paso con entornos virtuales.
   - Se incorporó la tabla de autores y enlaces a la fundamentación de diseño.

2. **Reorganización Estructural (`/docs`)**:
   - Se centralizó la documentación y recursos complementarios dentro de la carpeta `docs/` (`docs/FUNDAMENTACION-UX-UI.md`, `docs/uso_ia.md`, `docs/despensapp_logo.png` y `docs/DespensAPP - Presentación Oral E2.pdf`).
   - Se actualizaron las referencias relativas en `main.kv` y los enlaces cruzados en el `README.md` para garantizar la consistencia del proyecto y la integridad visual de la aplicación.

---

## Entrada / Prompt del Usuario (Modularización en Modelo-Vista-Controlador)
> "puedes ordenar el codigo modularmente?"
> "quiero que sea en modelo vista controlador"
> "si quieres puedes separar todo los modelos y dejar cada uno con un archibo y asi con todos los otros, tambien controlador y vista"

---

## Acciones Realizadas

1. **Arquitectura MVC Granular por Archivo**:
   - **Modelos (`models/`)**: Entidades individuales en archivos separados (`user.py`, `cart_item.py`, `pantry_item.py`, `shopping_list.py`), persistencia resiliente MySQL + SQLite (`database.py`) y unificación en `__init__.py`.
   - **Vistas (`views/`)**: Separación en diseño de temas (`views/theme.py`), componentes interactivos (`views/widgets/`: `progress_bar.py`, `nav_button.py`, `cart_row.py`, `pantry_row.py`, `list_card.py`, `buttons.py`, `profile_modal.py`), controladores de formularios (`views/dialogs/`: `base.py`, `cart_dialog.py`, `pantry_dialog.py`, `list_dialog.py`, `auth_dialog.py`) con carga automática y robusta de plantillas KV.
   - **Controladores (`controllers/`)**: Dominio y servicios desacoplados por módulo (`auth_controller.py`, `analytics_controller.py`, `sync_controller.py`, `cart_controller.py`, `pantry_controller.py`, `list_controller.py`) orquestados por `main_controller.py` (`MainController`).
   - **Punto de Entrada (`main.py`)**: Reescrito para orquestar la aplicación delegando lógica y estado en `MainController` y las vistas modulares.
   - **Retrocompatibilidad**: Wrappers raíz en `models.py`, `database.py`, `auth_manager.py`, `analytics_manager.py`, `sync_manager.py`, `theme.py`, `widgets.py` y `dialogs.py` para asegurar que scripts legados, `iniciar.bat` y `admin_dashboard/server.py` sigan funcionando de forma transparente.

2. **Validación y Pruebas**:
   - Instalación completa de dependencias en el entorno virtual local de Windows (`venv`).
   - Compilación sintáctica exitosa con `compileall` (0 errores).
   - Pruebas automatizadas de importación y ejecución de lógica de negocio (`MainController`, fallback SQLite y telemetría) con 100% de éxito.

---

## Solicitud (resumen): Limpieza de la raíz del repositorio
> Ordenar los archivos sueltos de la raíz y dejar todo dentro de los paquetes MVC.

## Acciones Realizadas

1. **Eliminación de wrappers legados**: se retiraron los módulos raíz de retrocompatibilidad (`models.py`, `database.py`, `auth_manager.py`, etc.) y se centralizaron los imports en `models/`, `controllers/` y `views/`.
2. **Reubicación de recursos**: el esquema SQL y `db_config.example.json` pasaron a `database/`; `GUIA_FUNCIONAMIENTO.md` e `HISTORIAL_CAMBIOS.md` pasaron a `docs/`, con el `README.md` actualizado.

---

## Solicitud (resumen): Notificaciones de stock y caducidad
> Avisar al usuario cuando un producto de la despensa se está agotando o está por vencer.

## Acciones Realizadas

1. **`controllers/notification_controller.py`**: nuevo `NotificationController` que emite notificaciones nativas con **Plyer** para dos tipos de alerta: stock (*Por agotarse* / *Agotado*) y vencimiento (*Por vencerse* / *Vencido*).
2. **Anti-spam**: cooldown en memoria por `(item_id, tipo_alerta)` (15 min por defecto) para no repetir la misma alerta.
3. **Robustez en Windows**: hook sobre los hilos de Plyer y log seguro ante errores de codificación de la terminal, para que un fallo de la bandeja del sistema no tumbe la app.
4. **Integración**: `PantryController` dispara la revisión al agregar un producto o cambiar su cantidad o fecha de vencimiento; `main.py` revisa la despensa al cargarla y cada 10 minutos (`Clock.schedule_interval`); `models/database.py` añade la consulta de producto por id. Se agregó `plyer` a `requirements.txt`.

---

## Solicitud (resumen): Selector de fecha de vencimiento
> Elegir la fecha de vencimiento con un calendario en vez de escribirla a mano.

## Acciones Realizadas

1. **`views/dialogs/pantry_dialog.py` y `kv/dialogs.kv`**: el campo de vencimiento abre un `MDModalDatePicker` (KivyMD 2.0); la fecha elegida se guarda en formato `YYYY-MM-DD`, evitando fechas mal escritas, y se puede limpiar con `clear_expiration`.

---

## Solicitud (resumen): Configuración remota y banner
> Poder cambiar mensajes y funciones de la app sin publicar una nueva versión.

## Acciones Realizadas

1. **`controllers/remote_config_controller.py`**: `RemoteConfigController` carga la configuración con triple respaldo: endpoint remoto → `remote_config.json` local → valores por defecto en memoria.
2. **Feature flags**: métodos `is_feature_enabled`, `is_maintenance_mode` e `is_banner_enabled` para activar/desactivar módulos (`cloud_sync`, `advanced_analytics`, `smart_notifications`).
3. **Banner reactivo**: nuevo widget `views/widgets/remote_banner.py` mostrado en la pantalla de Inicio con título, mensaje, tipo y badge definidos en el JSON.

---

## Corrección de Bugs de Interfaz (iconos, textos y contraste)

1. **Iconos del carrito y de listas invisibles o desalineados**
   - **Causa raíz**: los iconos se dibujaban como `MDIcon` dentro de `Button` transparentes o como caracteres Unicode (`✎`, `✕`); en KivyMD 2.0 eso deja el icono sin tamaño/posición correctos y algunas fuentes no renderizan esos glifos.
   - **Solución**: se reemplazaron por `MDIconButton` con iconos Material (`check-circle`, `trash-can-outline`, `pencil-outline`, `close`) y color personalizado en `kv/components.kv` y `kv/dialogs.kv`.
2. **Texto truncado en el modal de autenticación**
   - **Causa raíz**: la etiqueta de mensajes tenía altura fija (`22dp`) y `text_size: self.size`, por lo que los mensajes largos se cortaban en vez de pasar a una segunda línea.
   - **Solución**: en `kv/dialogs.kv` se usó `text_size: self.width, None` con altura dinámica (`36dp` si hay mensaje) y se agrandó el modal; además, los mensajes de "requerido", "conexión" y "modo local" ahora se pintan en rojo como errores.
3. **Bajo contraste de ítems de lista en modo oscuro y nuevo logo**
   - **Causa raíz**: el fondo y el texto de los ítems tenían colores claros fijos, pensados solo para el modo claro.
   - **Solución**: en `kv/dialogs.kv` los ítems usan `sage_container_color` y `text_secondary_color` cuando `modo_oscuro` está activo; se reemplazó `docs/despensapp_logo.png` por la versión en paleta azul (más liviana).



---

## Entrada / Prompt del Usuario (Fase 1 de mejoras de usabilidad)
> "mira que flujos puedo corregir para que la app se sienta mas comodo para el uso humano"
> "fase 1"

## Diagnóstico y Solución

1. **Bug: precios con punto de miles se guardaban mal**
   - **Causa raíz**: el campo de precio usaba `input_filter: "float"`, así que `1.500` (formato chileno) se interpretaba como `1.5` y el carrito mostraba **$1**; además el filtro bloqueaba la coma decimal (`1,5 kg`).
   - **Solución**: nuevo módulo `controllers/validators.py` (lógica pura, sin Kivy) con `parse_number` que entiende `1.500`, `$2.990`, `1,5` y `0.5`, y un filtro de escritura propio (`numeric_input_filter`).
2. **Formularios que fallaban en silencio**: carrito, listas, anotar producto y edición de nombres ahora muestran el error en rojo (`FormMessageLabel` reutilizable en `kv/dialogs.kv`) y lo borran apenas el usuario vuelve a escribir. Se reutilizó el patrón `validate_*` de despensa y se permitió registrar productos ya vencidos con un aviso ámbar.
3. **Borrado con "Deshacer"**: `controllers/undo_controller.py` oculta el elemento al instante y lo elimina de la BD tras 4 s; la barra `views/widgets/undo_snackbar.py` ofrece deshacer. Aplica a productos del carrito, de la despensa, listas completas y productos de una lista. Los pendientes se confirman al cerrar sesión o la app.
   - **Bug encontrado al probar**: `MDSnackbar` de KivyMD 2.0.0 fallaba con `FBO Initialization failed` (su efecto ripple se crea con altura 0); se reemplazó por una barra propia con widgets base de Kivy.
4. **Ajuste de stock**: el modal de detalle ya no se cierra en cada `+`/`−`, el paso depende de la unidad (100 g/ml, 0,5 kg/L, 1 el resto) y se puede fijar la cantidad exacta (`set_pantry_quantity` en `models/database.py`). Las alertas y el refresco de la lista ocurren una sola vez al cerrar.

## Validación
- `compileall` sin errores y 42 pruebas de parseo, validadores y cola de deshacer.
- Pruebas de integración sobre una copia temporal en SQLite (sin tocar `despensapp_local.db`) y recorrido real de la app con capturas: error de precio, precio `1.500` guardado como 1500, barra de deshacer, aviso de vencido, stepper de stock y modo oscuro.

---

## Entrada / Prompt del Usuario (Fase 2: conectar el flujo de compras)
> "pasemos a la fase 2"
> "Opción A (recomendada): una tabla nueva purchase_history [...] quiero que las ultimas compras puedan vistas como ultima semana, ultimo mes y ultimo año"

## Acciones Realizadas

1. **Historial de compras (`purchase_history`)**: tabla nueva en MySQL, SQLite, `database/database_schema.sql` y en la sincronización offline (`sync_controller.py`). Modelo `models/purchase_record.py`. El gasto de Inicio pasa a ser lo gastado de verdad en los últimos 7 días (antes mostraba el total del carrito).
2. **`controllers/purchase_controller.py`**: lógica del ciclo Listas → Carrito → Despensa.
   - "Pasar al carrito" desde una lista (sin duplicar productos que ya están pendientes).
   - "Finalizar compra": modal con una fila por producto marcado; suma la cantidad al producto existente de la despensa (o lo crea con la unidad elegida), registra el historial y lo quita del carrito.
   - "Añadir al carrito" desde el detalle de un producto por agotarse o sin stock.
   - Gasto e historial por periodo: última semana, último mes y último año.
3. **Estadísticas**: selector Semana / Mes / Año con el total gastado y la lista de últimas compras del periodo.
4. **Inicio con acciones**: la tarjeta de gasto abre el historial, la de alerta abre el producto afectado y la campana muestra un panel con todas las alertas y un contador.
5. **Carrito editable y estados vacíos**: tocar un producto del carrito permite corregir nombre, precio o categoría; Compras, Despensa, Listas e historial muestran una guía con botón cuando no tienen datos.

## Diagnóstico y Solución de Bugs

1. **Etiquetas que no se actualizaban en KV**
   - **Causa raíz**: en Kivy 2.3.1, una expresión KV que llama un método sobre una propiedad (`app.prop.upper()`, `root.msg.lower()`) se evalúa una sola vez y no vuelve a enlazarse. Afectaba al periodo de Estadísticas y, desde antes, al color de los mensajes del login (los errores salían en azul en vez de rojo).
   - **Solución**: los textos derivados se calculan en Python (`stats_period_tag`, `stats_spent_title`, `AuthModal.is_error_message`).
2. **Check de las listas mostraba un cuadro vacío**
   - **Causa raíz**: la fuente Roboto no incluye el glifo `✓`.
   - **Solución**: se reemplazó por el icono Material `check` y se quitaron los demás `✓` de la interfaz.

## Validación
- 21 pruebas de `PurchaseController` sobre SQLite temporal (no duplicar, sumar/crear en despensa, historial por semana/mes/año) más las suites de la Fase 1.
- Recorrido real de la app con capturas en modo claro y oscuro, sin tocar `despensapp_local.db` ni MySQL.

---

## Entrada / Prompt del Usuario (Carrito acumulado, historial por listas y modal de despensa)
> "que al marcar las cosas del carro el precio vaya desde 0 y no descontando, las ultimas compras ponelas por listas, que sea mas comodo para el usuario el modal de los productos de Mi Despensa"

## Acciones Realizadas

1. **Total del carrito acumulado**: "En el carro" parte en $0 y sube al marcar productos (`CartController.summarize`), con el detalle "de $X estimado · N de M productos".
2. **Historial agrupado por lista**: `purchase_history` guarda `list_name` al comprar (con migración `ALTER TABLE` para bases existentes, en MySQL, SQLite, esquema y sincronización). `PurchaseController.group_by_list` arma una tarjeta por lista con subtotal y fecha; lo comprado sin lista va a "Compras sueltas". El nombre se conserva aunque la lista se borre.
3. **Modal de Mi Despensa rediseñado**: píldora de estado, botón editar y cerrar; tarjeta de stock con el mínimo de alerta visible; tarjeta de vencimiento con fecha y días restantes ("Cambiar fecha" / "No vence" sin cerrar el modal); "Listo" como acción principal y "Eliminar" secundario. Nuevo modo edición en el mismo modal para nombre, unidad y mínimo de alerta (`validate_pantry_details`, `PantryController.update_details`), que antes no se podían corregir.

## Validación
- 18 pruebas nuevas (total acumulado, agrupación y migración sobre una base con el esquema anterior, edición de despensa) más las suites de las fases 1 y 2.
- Recorrido de la app con capturas en modo claro y oscuro; se ajustó el contraste de la píldora de estado en modo oscuro.
