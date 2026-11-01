"""
routers/auth.py  -  Iniciar/cerrar sesión y administrar usuarios
"""
import secrets
import os
import time
import sqlite3
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status

from database import obtener_conexion
from esquemas import LoginEntrada, UsuarioCrear, UsuarioRespuesta, CambioClave
from seguridad import (
    DURACION_SESION_HORAS, ITERACIONES, resumen_token,
    generar_hash_contrasena,
    obtener_usuario_actual,
    verificar_contrasena,
)

router = APIRouter(tags=["Autenticación"])
HASH_FICTICIO = generar_hash_contrasena(secrets.token_urlsafe(24))


@router.post("/auth/login")
def iniciar_sesion(datos: LoginEntrada, response: Response, request: Request):
    ahora = int(time.time())
    fallo = False
    ip = request.client.host if request.client else "local"
    claves = ("usuario:" + datos.nombre_usuario, "ip:" + ip)
    with obtener_conexion() as conexion:
        conexion.execute("BEGIN IMMEDIATE")
        conexion.execute("DELETE FROM intentos_login WHERE inicio<?", (ahora-300,))
        intentos = {k: conexion.execute("SELECT * FROM intentos_login WHERE nombre=?", (k,)).fetchone() for k in claves}
        if any(f and f["cantidad"] >= (5 if k.startswith("usuario:") else 30) for k,f in intentos.items()):
            raise HTTPException(429, "Demasiados intentos. Espere cinco minutos.", headers={"Retry-After":"300"})
        usuario = conexion.execute("SELECT * FROM usuarios WHERE nombre_usuario=?", (datos.nombre_usuario,)).fetchone()
        valido = verificar_contrasena(datos.contrasena,
            usuario["contrasena_salt"] if usuario else HASH_FICTICIO[0],
            usuario["contrasena_hash"] if usuario else HASH_FICTICIO[1],
            usuario["iteraciones"] if usuario else ITERACIONES)
        if not usuario or not valido:
            for k in claves:
                f = intentos[k]
                conexion.execute("INSERT OR REPLACE INTO intentos_login VALUES (?, ?, ?)",
                                 (k, f["cantidad"]+1 if f else 1, f["inicio"] if f else ahora))
            fallo = True
        else:
            conexion.execute("DELETE FROM intentos_login WHERE nombre=?", (claves[0],))
            if usuario["iteraciones"] != ITERACIONES:
                salt, hash_ = generar_hash_contrasena(datos.contrasena)
                conexion.execute("UPDATE usuarios SET contrasena_hash=?, contrasena_salt=?, iteraciones=? WHERE id=?", (hash_, salt, ITERACIONES, usuario["id"]))
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            expira = datetime.utcnow() + timedelta(hours=DURACION_SESION_HORAS)
            conexion.execute("UPDATE usuarios SET token=?, token_expira=?, csrf_hash=? WHERE id=?",
                             (resumen_token(token), expira.isoformat(), resumen_token(csrf), usuario["id"]))
    if fallo:
        raise HTTPException(401, "Usuario o contraseña incorrectos")
    secure = os.environ.get("MATRICULA_COOKIE_SECURE") == "1"
    response.set_cookie("token", token, httponly=True, secure=secure, samesite="strict", max_age=DURACION_SESION_HORAS*3600)
    response.set_cookie("csrf", csrf, secure=secure, samesite="strict", max_age=DURACION_SESION_HORAS*3600)
    return {"mensaje":"Sesión iniciada", "token":token, "usuario":usuario["nombre_usuario"], "rol":usuario["rol"]}


@router.post("/auth/logout")
def cerrar_sesion(response: Response, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        conexion.execute(
            "UPDATE usuarios SET token = NULL, token_expira = NULL WHERE id = ?",
            (usuario["id"],),
        )
    response.delete_cookie("token")
    response.delete_cookie("csrf")
    return {"mensaje": "Sesión cerrada correctamente"}


@router.get("/auth/yo", response_model=UsuarioRespuesta)
def usuario_autenticado(usuario=Depends(obtener_usuario_actual)):
    return dict(usuario)


@router.post(
    "/auth/usuarios",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_usuario(datos: UsuarioCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        salt, hash_ = generar_hash_contrasena(datos.contrasena)
        with obtener_conexion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol, iteraciones)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datos.nombre_usuario, hash_, salt, datos.rol, ITERACIONES),
            )
            fila = conexion.execute(
                "SELECT * FROM usuarios WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Ese nombre de usuario ya existe")


@router.get("/auth/usuarios", response_model=list[UsuarioRespuesta])
def listar_usuarios(usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        filas = conexion.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [dict(fila) for fila in filas]


@router.delete("/auth/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, usuario=Depends(obtener_usuario_actual)):
    if usuario_id == usuario["id"]:
        raise HTTPException(status_code=409, detail="No puede eliminar su propio usuario")
    with obtener_conexion() as conexion:
        cursor = conexion.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"mensaje": "Usuario eliminado correctamente"}


@router.post("/auth/cambiar-clave")
def cambiar_clave(datos: CambioClave, response: Response, usuario=Depends(obtener_usuario_actual)):
    if not verificar_contrasena(datos.actual, usuario["contrasena_salt"], usuario["contrasena_hash"], usuario["iteraciones"]):
        raise HTTPException(400, "La contraseña actual no es correcta")
    salt, hash_ = generar_hash_contrasena(datos.nueva)
    with obtener_conexion() as conexion:
        conexion.execute("UPDATE usuarios SET contrasena_hash=?, contrasena_salt=?, iteraciones=?, token=NULL, token_expira=NULL, csrf_hash=NULL WHERE id=?", (hash_, salt, ITERACIONES, usuario["id"]))
    response.delete_cookie("token")
    response.delete_cookie("csrf")
    return {"mensaje":"Contraseña actualizada. Inicie sesión nuevamente."}

@router.get("/auth/auditoria")
def auditoria(usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        return [dict(f) for f in conexion.execute("SELECT * FROM auditoria ORDER BY id DESC LIMIT 100")]
