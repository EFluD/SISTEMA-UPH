"""
main.py  -  Punto de entrada de la API de Matrícula (versión modular)
---------------------------------------------------------------------
Este archivo ya NO tiene la lógica. Solo:
  1. crea la aplicación FastAPI,
  2. prepara la base de datos al arrancar,
  3. "conecta" (include_router) cada módulo.

Estructura:
  database.py   -> conexión y tablas (capa de datos)
  esquemas.py   -> modelos Pydantic (entrada/salida)
  seguridad.py  -> hash de contraseñas y token
  reglas.py     -> reglas de negocio puras (promedio, aprobado/reprobado)
  datos_demo.py -> datos de ejemplo
  routers/      -> un archivo por módulo (auth, estudiantes, docentes, cursos,
                   matriculas, calificaciones, reportes, datos, dashboard, paginas)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from database import obtener_conexion
from urllib.parse import urlparse
from routers import academico
from fastapi.staticfiles import StaticFiles

from database import crear_tablas
from routers import (
    auth,
    calificaciones,
    cursos,
    dashboard,
    datos,
    docentes,
    estudiantes,
    matriculas,
    paginas,
    reportes,
)
from seguridad import crear_usuario_admin_si_no_existe


@asynccontextmanager
async def lifespan(app: FastAPI):
    crear_tablas()
    crear_usuario_admin_si_no_existe()
    yield


app = FastAPI(
    title="API de Matrícula",
    description="API modular con login, dashboard y 8 módulos - Programación III (UPH)",
    version="4.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def inicio():
    return RedirectResponse("/dashboard")


app.include_router(auth.router)
app.include_router(estudiantes.router)
app.include_router(docentes.router)
app.include_router(cursos.router)
app.include_router(matriculas.router)
app.include_router(calificaciones.router)
app.include_router(reportes.router)
app.include_router(datos.router)
app.include_router(dashboard.router)
app.include_router(paginas.router)


app.include_router(academico.router)

@app.middleware("http")
async def controles_http(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origen = request.headers.get("Origin")
        if origen and origen != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail":"Origen no permitido"}, status_code=403)
        longitud = request.headers.get("content-length", "0")
        if longitud.isdigit() and int(longitud) > 2_000_000:
            return JSONResponse({"detail":"Solicitud demasiado grande"}, status_code=413)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    respuesta.headers["Cache-Control"] = "no-store"
    if not request.url.path.startswith(("/docs", "/redoc")):
        respuesta.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    uid = getattr(request.state, "usuario_id", None)
    if uid and request.method in ("POST", "PUT", "PATCH", "DELETE") and respuesta.status_code < 400:
        with obtener_conexion() as conexion:
            conexion.execute("INSERT INTO auditoria (usuario_id, accion, ruta) VALUES (?, ?, ?)", (uid, request.method, request.url.path))
    return respuesta
