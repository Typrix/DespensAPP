# Fundamentación UX/UI - DespensAPP

## a) Metodología de investigación
* **Instrumento:** Encuesta cuantitativa estructurada aplicada mediante la plataforma Google Forms.
* **Muestra de estudio:** 32 participantes (n=32) pertenecientes a la ciudad de Temuco.
* **Perfil de los participantes:** Público joven-adulto nativo digital con alta adopción de aplicaciones móviles, donde el 52.4% se ubica entre los 18 y 25 años y el 28.6% tiene 33 años o más.
* **Distribución demográfica:** Las decisiones de compra en el hogar están lideradas predominantemente por mujeres (61.9% mujeres y 33.3% hombres).

## b) Resultados principales
* **Gestión informal del inventario:** El 56.3% de las personas gestiona su despensa de memoria sin un registro estructurado, mientras que el 34.4% utiliza bloc de notas simple en el celular sin alertas automáticas de vencimiento.
* **Valoración de la solución:** El 71.9% considera altamente útil contar con una herramienta móvil para el control de inventario y fechas de vencimiento.
* **Principales categorías de pérdida:** Las mayores pérdidas de alimentos en los hogares corresponden a frutas y verduras frescas (68.8%), lácteos o derivados (59.4%) y panadería o salsas (21.9%).
* **Preferencias visuales:** El 57.1% eligió la tonalidad azul como la más cómoda visualmente para el uso diario en aplicaciones móviles.
* **Requisito de Modo Oscuro:** El 50.0% declaró de forma tajante que no utilizaría la aplicación si esta no cuenta con Modo Oscuro integrado.
* **Control presupuestario:** El 88.2% exige llevar un control de gastos acumulado antes de llegar a la caja registradora del supermercado, ya que actualmente el 41.2% lleva un control parcial y otro 41.2% solo lo hace a veces.

## c) Matriz hallazgo -> decisión de diseño

| Hallazgo | Decisión de Interfaz | Por qué |
| :--- | :--- | :--- |
| El 68.8% pierde frutas y verduras olvidadas en la despensa. | Implementación de la pantalla **Despensa** con chips informativos e indicadores con código de colores (verde, naranja y rojo) según la proximidad de vencimiento. | Permite identificar de un vistazo los insumos críticos sin requerir lecturas extensas. |
| El 88.2% exige llevar control de gastos en el supermercado. | Creación de la pantalla **Compras** con un carrito dinámico, cálculo de suma automática en vivo e indicador del presupuesto acumulado total. | Otorga certeza financiera instantánea antes de llegar a la caja registradora. |
| El 50.0% requiere Modo Oscuro y el 57.1% prefiere el color azul. | Paleta Blue de KivyMD con conmutador de tema mediante `MDSwitch` en el modal flotante `ProfileModalView` sincronizado con `theme_cls`. | Garantiza la comodidad visual del usuario en entornos de poca luz y respeta la preferencia estilística dominante. |

## d) Justificación de la estructura de la app
**Esquema de navegación:** Se optó por una arquitectura con `ScreenManager` y una barra de navegación inferior (`BottomNavButton`) con indicador *pill* azul para facilitar el desplazamiento entre las 5 pantallas principales.

**Orden y función de las pantallas:**
1. **Inicio:** Vista global de estado y accesos rápidos para ubicar de inmediato al usuario al ingresar.
2. **Compras:** Carrito dinámico con acumulado en tiempo real para usar presencialmente en el supermercado.
3. **Despensa:** Inventario activo con alertas visuales de stock y caducidad para la gestión continua en casa.
4. **Listas:** Planificación quincenal de compras para la organización previa del hogar.
5. **Estadísticas:** Análisis de gastos e insumos frecuentes para evaluar patrones de consumo.

**Justificación del flujo:** Esta disposición refleja el ciclo de vida real de los insumos en el hogar (planificación, compra presencial, almacenamiento en despensa y evaluación de consumo).

## e) Consideraciones de diversidad y accesibilidad
* **Reducción de fatiga visual:** La combinación de la tonalidad azul con la integración del Modo Oscuro reactivo cuida la vista en uso nocturno.
* **Claridad y baja carga cognitiva:** El uso de componentes como `MDCard`, `MDScrollView` y chips cromáticos permite que personas con poca familiaridad tecnológica comprendan el estado de sus alimentos mediante asociación de colores (verde, naranja, rojo).
* **Feedback transparente:** La actualización dinámica mediante *Property Binding* asegura que los totales presupuestarios y estados de inventario se reflejen en tiempo real sin requerir acciones complejas por parte del usuario.
