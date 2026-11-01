# Verificación de Campus académico v4

## Resultado

**20 pruebas aprobadas** en un entorno virtual aislado con las dependencias finales:
FastAPI 0.162.0, Starlette 1.10.0, Pydantic 2.14.2, Jinja2 3.1.6, Uvicorn 0.35.0,
pytest 9.2.0 y httpx2 2.16.0. Python usado: 3.14 en Windows.
`pip check` no encontró incompatibilidades.

Las diez pruebas funcionales del proyecto original se mantienen, con contraseñas
de prueba nuevas y aisladas de la instalación. Otras diez cubren:

- Rechazo de escalamiento de privilegios desde una cuenta docente.
- Restricción de usuarios, auditoría y respaldos a administradores.
- CSRF en escrituras con cookie y rechazo de un Origin distinto.
- Hash del token almacenado, vencimiento y revocación al cerrar sesión.
- Límite de intentos y cambio de contraseña que invalida la sesión.
- Hoja, historial, período, carga docente y retiro sin pérdida del registro.
- Dos inscripciones concurrentes al último cupo: una obtiene 201 y otra 409.
- Protección del período de una oferta con matrículas.
- Auditoría, neutralización de fórmulas CSV y manejo de filas CSV mal formadas.
- Actualización de un hash antiguo, roles válidos y orden cronológico del panel.

También se verificó la sintaxis de los archivos Python y JavaScript.

## Dependencias

- Consulta a los avisos publicados por PyPI para las **18 dependencias efectivas de
  ejecución**: **0 avisos y 0 errores de consulta**. El detalle, fecha UTC, versiones
  y enlaces de fuente están en `VALIDACION_DEPENDENCIAS.json`.
- `pip-audit` sobre el entorno aislado, incluyendo herramientas de pruebas y
  auditoría: **sin vulnerabilidades conocidas reportadas**. Resultado en
  `VALIDACION_PIP_AUDIT.json`.
- Se actualizaron FastAPI y Starlette para dejar de depender de las versiones
  antiguas del proyecto v3. Las versiones resultantes están fijadas con restricciones
  en `requirements-lock.txt`.

Fuentes primarias de versiones y cambios: [FastAPI en PyPI](https://pypi.org/project/fastapi/),
[Starlette en PyPI](https://pypi.org/project/starlette/) y
[cambios de Jinja](https://jinja.palletsprojects.com/en/stable/changes/).
Los resultados de avisos son una consulta fechada, no una garantía contra fallos
desconocidos o vulnerabilidades publicadas posteriormente.

## Navegador

Se ejecutó el servidor local con el entorno actualizado y se comprobaron:

- Login de administrador y docente; logout y redirección al acceso.
- Inicio, indicadores, filtros por período y apertura de sus registros.
- Hoja de Ana Lucía Martínez e historial completo.
- Carga docente de Marta Lilian Reyes, lista de una clase y navegación entre modales.
- Módulo de reportes sin errores de consola.
- Cuenta docente sin módulos administrativos, sin botones para editar alumnos
  y con los campos de notas deshabilitados.
- Diseño de escritorio revisado mediante capturas.

## Límites de esta verificación

No se ejecutaron los BAT mediante doble clic ni la instalación con Python 3.12/3.13.
El entorno aislado se preparó con pip usando una carpeta temporal dentro del espacio
de trabajo por restricciones de esta sesión. No se verificaron la salida física de
impresión, todos los tamaños de móviles o un despliegue público. Persisten avisos de
deprecación con Python 3.14, sin fallos en la suite.

La auditoría de escrituras es básica y se guarda después de la transacción de
negocio; no es una bitácora inmutable o atómica con cada cambio. No se realizó una
prueba de penetración externa. Los límites funcionales de períodos, reactivaciones,
horarios y lectura docente se explican en el README y en la guía de clase.
