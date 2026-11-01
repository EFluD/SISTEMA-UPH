# Guía docente · API de matrícula v4

## Propósito

Explicar una petición desde la pantalla hasta la base de datos, distinguir
validación de autorización y demostrar cómo la misma API sirve varias consultas.
El diseño visual ayuda a recorrer el sistema; las reglas se deciden en el servidor.

## Sesión de 90 minutos

| Tiempo | Actividad | Evidencia de aprendizaje |
|---|---|---|
| 0–10 | Inicio de sesión y recorrido por los ocho módulos | Identificar cliente, servidor y recurso |
| 10–25 | GET, POST y PUT en Swagger | Reconocer ruta, parámetros, JSON y respuesta |
| 25–40 | Crear alumno y matrícula; repetir cuenta y llenar cupo | Separar errores 422, 404 y 409 |
| 40–55 | Hoja e historial de Ana Lucía Martínez | Explicar relaciones y filtro por período |
| 55–70 | Comparar roles; logout y token revocado | Distinguir autenticación, autorización y CSRF |
| 70–80 | Dashboard y carga docente | Identificar qué cuenta cada indicador |
| 80–90 | Pruebas y ejercicio guiado | Verificar una regla sin revisar solo la pantalla |

## Recorrido del código

1. `main.py` crea FastAPI, prepara la base y conecta los routers.
2. `esquemas.py` expresa qué datos recibe la API y qué formato devuelve.
3. `seguridad.py` identifica la sesión y comprueba permisos y CSRF cuando corresponde.
4. `routers/estudiantes.py`, `cursos.py` y `matriculas.py` realizan los CRUD y reglas.
5. `database.py` administra conexiones, transacciones y migraciones aditivas.
6. `routers/academico.py` reúne datos para las fichas, carga y dashboard.
7. `static/js/nucleo.js` contiene la comunicación, tablas, formularios y modales.
8. `modulo_inicio.js` y `consultas.js` convierten las respuestas en vistas interactivas.

Es un recorrido conceptual. No implica un orden exacto de ejecución de todas las
dependencias y validaciones internas de FastAPI.

## Demostración con los datos ficticios

En Inicio seleccione 2026-1. Verá una oferta anterior y cuatro matrículas.
Abra la ficha de Ana Lucía Martínez. La hoja muestra únicamente ese período;
el historial muestra también sus registros de 2026-3. Cambie de pestaña y
explique por qué el historial completo no se reduce al filtro de la hoja.

Abra Marta Lilian Reyes desde la carga docente y consulte sus cursos. Abra
«Ver alumnos» en uno de ellos y luego el expediente de un alumno. El dato de
inscripciones suma matrículas y puede contar al mismo estudiante varias veces.

Pulse Aprobadas o Sin nota final en el gráfico: el detalle corresponde a matrículas,
no a personas únicas. En la vista general los estudiantes y docentes son todos los
registrados; al seleccionar un período se muestran estudiantes con matrícula activa
y docentes con oferta asignada en ese período. Los textos del panel lo indican.

## Seguridad para explicar sin confusiones

- **Autenticación:** verificar quién realiza la petición mediante una sesión válida.
- **Autorización:** decidir si su rol puede ejecutar la acción. Ocultar un botón
  facilita el uso, pero la API también debe rechazar la petición directa.
- **Hash de contraseñas:** PBKDF2 y una sal aleatoria permiten verificar la clave
  sin almacenarla en texto plano. Hash y cifrado no son lo mismo.
- **Token opaco:** una credencial aleatoria temporal, no un JWT. El servidor consulta
  su hash y vigencia. JWT es una alternativa, no un requisito de una API segura.
- **Cookie HttpOnly:** JavaScript no puede leer la cookie de sesión. La cookie CSRF
  sí se lee para acompañar las escrituras con un encabezado verificable.
- **CSRF:** evita aceptar escrituras con solo una cookie enviada por el navegador
  sin la comprobación adicional. Authorization con Bearer se envía explícitamente.
- **HTTPS:** protege el transporte; el hash protege contraseñas almacenadas.

## Ejercicio con roles

Cree una cuenta docente en Usuarios. Cierre la sesión de admin y entre como docente:
puede consultar alumnos, cursos, notas e historial. Usuarios y Datos no aparecen,
y sus endpoints también responden 403. La escritura de notas queda en admin para
esta política didáctica. El siguiente ejercicio puede vincular usuarios con docentes
y permitirles calificar solo sus ofertas.

Use Swagger para demostrar 401 sin sesión y 403 con una sesión sin permiso.
Después del logout, reutilice el token anterior: debe obtener 401.
No publique tokens ni contraseñas de su instalación en capturas de clase.

## Reglas y límites para discutir

- El promedio se calcula con tres notas y se aprueba con 70. Una nota faltante
  representa «En proceso» y no debe convertirse en cero automáticamente.
- `BEGIN IMMEDIATE` hace indivisible, respecto a otras escrituras SQLite, la
  verificación de cupo y la inscripción. Dos solicitudes al último cupo deben
  producir una creación y un conflicto, sin sobrepasar la capacidad.
- El período de una oferta ya matriculada se conserva; una oferta nueva usa
  otro código. Los cursos antiguos sin período pueden clasificarse una vez.
- Un retiro conserva su registro. Reactivarlo reutiliza la misma fila; una
  aplicación institucional necesitaría eventos separados para cada transición.
- El horario es informativo, sin validación de choques. La carga docente cuenta
  ofertas registradas; no calcula horas de contratación ni equivalencias.

## Extensiones para los estudiantes

1. Crear tablas normalizadas de asignaturas, períodos y secciones.
2. Relacionar usuarios con docentes y probar permisos por curso propio.
3. Validar choques de horario y requisitos académicos.
4. Añadir auditoría transaccional con valores anteriores y posteriores, sin secretos.
5. Definir el tratamiento de asignaturas repetidas al sumar UV aprobadas.

Evalúe la explicación de una petición completa, los códigos HTTP y las pruebas
de casos válidos, inválidos y sin permiso; no únicamente la apariencia de la pantalla.
