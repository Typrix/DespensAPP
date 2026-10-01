# Reglas de Proyecto y Desarrollo - Antigravity

1. **Registro de Uso de IA:** En cada proyecto nuevo, crea y mantén `uso_ia.md` registrando solo hitos importantes y solución de bugs críticos con el prompt y la solución concisa.
2. **Plan de Implementación:** Antes de realizar cambios técnicos no triviales, presenta siempre un Plan de Implementación estructurado (fases, archivos y validación) antes de tocar código.
3. **Validación previa:** Antes de dar por finalizada una tarea con código, ejecuta una prueba de validación en la terminal para asegurar cero errores de sintaxis e importación.
4. **Commits en Git:** Al hacer commits en Git, usa el estándar Conventional Commits en español (ej: feat:, fix:, refactor:) y deja el working tree limpio.
5. **Explicación de Bugs:** Al corregir un bug, explica primero en 1 o 2 líneas la causa raíz del error antes de mostrar la solución técnica.
6. **Entorno Virtual en Windows:** En proyectos Python en Windows, usa siempre el intérprete del venv local (`.\venv\Scripts\python`) para librerías y pruebas, nunca el global.
7. **Idioma y Estilo:** Escribe el código en inglés (funciones, variables y clases), pero los comentarios y explicaciones en español de forma concisa.
8. **Diseño de Interfaces (UI):** En UI (Kivy, Flutter, Web), crea interfaces responsivas con paletas armoniosas y tipografía moderna, sin placeholders ni componentes rotos.
9. **Código Modular:** Estructura siempre el código de forma modular separando lógica, datos e interfaz gráfica.
10. **Archivo .gitignore:** En cada proyecto nuevo, crea siempre un .gitignore adecuado para el lenguaje y entorno detectado.
