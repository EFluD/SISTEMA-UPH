"""Sesión opaca, hash de contraseñas, CSRF y autorización centralizada."""
import hashlib
import secrets
import os
from datetime import datetime
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import obtener_conexion

DURACION_SESION_HORAS = 2
ITERACIONES = 600_000
bearer = HTTPBearer(auto_error=False)

def generar_hash_contrasena(contrasena: str, salt: str | None = None, iteraciones: int = ITERACIONES):
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.pbkdf2_hmac("sha256", contrasena.encode(), salt.encode(), iteraciones).hex()

def verificar_contrasena(contrasena, salt, hash_guardado, iteraciones=ITERACIONES):
    return secrets.compare_digest(generar_hash_contrasena(contrasena, salt, iteraciones)[1], hash_guardado)

def resumen_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def crear_usuario_admin_si_no_existe():
    with obtener_conexion() as conexion:
        if conexion.execute("SELECT id FROM usuarios").fetchone():
            admin = conexion.execute("SELECT * FROM usuarios WHERE nombre_usuario='admin'").fetchone()
            if admin and verificar_contrasena("admin123", admin["contrasena_salt"], admin["contrasena_hash"], admin["iteraciones"]):
                raise RuntimeError("Reemplace la clave de demostración ejecutando python configurar.py")
            return
        clave = os.environ.get("MATRICULA_ADMIN_PASSWORD", "")
        if len(clave) < 12:
            raise RuntimeError("Configure primero: python configurar.py (contraseña de 12 caracteres o más)")
        salt, hash_ = generar_hash_contrasena(clave)
        conexion.execute("INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol, iteraciones) VALUES ('admin', ?, ?, 'admin', ?)", (hash_, salt, ITERACIONES))

def obtener_usuario_por_token(token):
    with obtener_conexion() as conexion:
        fila = conexion.execute("SELECT * FROM usuarios WHERE token=?", (resumen_token(token),)).fetchone()
    if not fila or not fila["token_expira"] or datetime.fromisoformat(fila["token_expira"]) < datetime.utcnow():
        return None
    return fila

def obtener_usuario_actual(request: Request, credencial: HTTPAuthorizationCredentials | None = Depends(bearer)):
    encabezado = request.headers.get("Authorization", "")
    es_bearer = encabezado.startswith("Bearer ")
    token = encabezado[7:].strip() if es_bearer else request.cookies.get("token")
    usuario = obtener_usuario_por_token(token) if token else None
    if usuario is None:
        raise HTTPException(401, "Sesión inválida o expirada")
    ruta, metodo = request.url.path, request.method
    if usuario["rol"] not in ("admin", "docente"):
        raise HTTPException(403, "Rol sin permisos")
    if metodo not in ("GET", "HEAD", "OPTIONS"):
        if not es_bearer:
            csrf = request.headers.get("X-CSRF-Token", "")
            if not csrf or not secrets.compare_digest(resumen_token(csrf), usuario["csrf_hash"] or ""):
                raise HTTPException(403, "Solicitud sin verificación CSRF. Actualice la página.")
        if ruta not in ("/auth/logout", "/auth/cambiar-clave") and usuario["rol"] != "admin":
            raise HTTPException(403, "Esta acción requiere un administrador")
    if (ruta.startswith("/datos") or ruta.startswith("/auth/usuarios") or ruta == "/auth/auditoria") and usuario["rol"] != "admin":
        raise HTTPException(403, "Esta sección requiere un administrador")
    request.state.usuario_id = usuario["id"]
    return usuario
