"""
routers/datos.py  -  Módulo 7: exportar/importar CSV y respaldos de la base de datos

Conceptos de la clase que aparecen aquí:
  * Flujos y archivos: leer y escribir CSV, copiar archivos .db
  * Hilos y sincronización: el respaldo corre en un hilo (threading.Thread) y un
    Lock evita que se hagan dos respaldos al mismo tiempo.
"""
import csv
import io
import os
import sqlite3
import threading
import secrets
from contextlib import closing
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ValidationError

import database
from database import mensaje_integridad, obtener_conexion
from datos_demo import cargar_datos_demo
from esquemas import CursoCrear, DocenteCrear, EstudianteCrear
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Datos (CSV y respaldos)"])

# --------------------------------------------------------------------------
# EXPORTAR CSV
# --------------------------------------------------------------------------
# tabla -> (consulta, encabezados). Solo estas tablas se pueden exportar
# (usuarios NO está: tiene contraseñas).
EXPORTABLES = {
    "estudiantes": (
        "SELECT id, nombre, cuenta, carrera, correo, edad FROM estudiantes ORDER BY id",
        ["id", "nombre", "cuenta", "carrera", "correo", "edad"],
    ),
    "docentes": (
        "SELECT id, nombre, correo, especialidad FROM docentes ORDER BY id",
        ["id", "nombre", "correo", "especialidad"],
    ),
    "cursos": (
        """SELECT c.id, c.codigo, c.nombre, c.creditos, c.cupo, d.nombre AS docente
           FROM cursos c LEFT JOIN docentes d ON d.id = c.docente_id ORDER BY c.id""",
        ["id", "codigo", "nombre", "creditos", "cupo", "docente"],
    ),
    "matriculas": (
        """SELECT m.id, e.cuenta, e.nombre AS estudiante, c.codigo AS curso,
                  m.fecha_matricula, m.estado
           FROM matriculas m JOIN estudiantes e ON e.id = m.estudiante_id
           JOIN cursos c ON c.id = m.curso_id ORDER BY m.id""",
        ["id", "cuenta", "estudiante", "curso", "fecha_matricula", "estado"],
    ),
    "calificaciones": (
        """SELECT e.cuenta, e.nombre AS estudiante, c.codigo AS curso,
                  k.parcial1, k.parcial2, k.parcial3
           FROM calificaciones k JOIN matriculas m ON m.id = k.matricula_id
           JOIN estudiantes e ON e.id = m.estudiante_id
           JOIN cursos c ON c.id = m.curso_id ORDER BY c.codigo, e.nombre""",
        ["cuenta", "estudiante", "curso", "parcial1", "parcial2", "parcial3"],
    ),
}


@router.get("/datos/exportar/{tabla}")
def exportar_csv(tabla: str, usuario=Depends(obtener_usuario_actual)):
    if tabla not in EXPORTABLES:
        raise HTTPException(status_code=404, detail="Esa tabla no se puede exportar")
    consulta, encabezados = EXPORTABLES[tabla]
    with obtener_conexion() as conexion:
        filas = conexion.execute(consulta).fetchall()

    # StringIO funciona como un "archivo en memoria": escribimos el CSV ahí.
    memoria = io.StringIO()
    escritor = csv.writer(memoria)
    escritor.writerow(encabezados)
    for fila in filas:
        escritor.writerow(["" if valor is None else ("\'" + valor if isinstance(valor, str) and valor.lstrip().startswith(("=", "+", "-", "@")) else valor) for valor in fila])

    # "utf-8-sig" agrega una marca al inicio para que Excel muestre bien las tildes.
    contenido = memoria.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        io.BytesIO(contenido),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{tabla}.csv"'},
    )


# --------------------------------------------------------------------------
# IMPORTAR CSV
# --------------------------------------------------------------------------
class ImportacionEntrada(BaseModel):
    contenido: str  # texto del archivo CSV (el navegador lo lee y lo envía)


# tabla -> (modelo Pydantic que valida cada fila, consulta INSERT, campos en orden)
IMPORTABLES = {
    "estudiantes": (
        EstudianteCrear,
        "INSERT INTO estudiantes (nombre, cuenta, carrera, correo, edad) VALUES (?, ?, ?, ?, ?)",
        ["nombre", "cuenta", "carrera", "correo", "edad"],
    ),
    "docentes": (
        DocenteCrear,
        "INSERT INTO docentes (nombre, correo, especialidad) VALUES (?, ?, ?)",
        ["nombre", "correo", "especialidad"],
    ),
    "cursos": (
        CursoCrear,
        "INSERT INTO cursos (codigo, nombre, creditos, cupo) VALUES (?, ?, ?, ?)",
        ["codigo", "nombre", "creditos", "cupo"],
    ),
}

MAX_CARACTERES_CSV = 1_000_000


@router.post("/datos/importar/{tabla}")
def importar_csv(tabla: str, entrada: ImportacionEntrada, usuario=Depends(obtener_usuario_actual)):
    if tabla not in IMPORTABLES:
        raise HTTPException(status_code=404, detail="Solo se puede importar: estudiantes, docentes o cursos")
    if len(entrada.contenido) > MAX_CARACTERES_CSV:
        raise HTTPException(status_code=413, detail="El archivo es demasiado grande (máximo 1 MB)")

    modelo, insertar, campos = IMPORTABLES[tabla]
    texto = entrada.contenido.lstrip("﻿")  # quita la marca BOM de Excel
    primera_linea = texto.splitlines()[0] if texto.strip() else ""
    # Excel en español guarda los CSV con punto y coma (;) en lugar de coma.
    separador = ";" if primera_linea.count(";") > primera_linea.count(",") else ","

    lector = csv.DictReader(io.StringIO(texto), delimiter=separador)
    if not lector.fieldnames:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    encabezados = [(nombre or "").strip().lower() for nombre in lector.fieldnames]
    faltantes = [campo for campo in campos if campo not in encabezados]
    if faltantes:
        raise HTTPException(
            status_code=422,
            detail="Faltan columnas en el CSV: " + ", ".join(faltantes) + ". Se esperaba: " + ", ".join(campos),
        )

    insertados = 0
    errores = []
    with obtener_conexion() as conexion:
        for numero, fila in enumerate(lector, start=2):  # la fila 1 es el encabezado
            if None in fila:
                errores.append({"fila": numero, "motivo": "La fila tiene más valores que columnas"})
                continue
            limpia = {(k or "").strip().lower(): (v or "").strip() for k, v in fila.items() if k}
            try:
                registro = modelo(**{campo: limpia.get(campo, "") for campo in campos})
                conexion.execute(insertar, [getattr(registro, campo) for campo in campos])
                insertados += 1
            except ValidationError as error:
                detalle = "; ".join(f"{e['loc'][0]}: {e['msg']}" for e in error.errors())
                errores.append({"fila": numero, "motivo": detalle})
            except sqlite3.IntegrityError as error:
                errores.append({"fila": numero, "motivo": mensaje_integridad(error, "Registro duplicado")})
    return {"insertados": insertados, "omitidos": len(errores), "errores": errores[:50]}


# --------------------------------------------------------------------------
# RESPALDOS (con hilo + Lock)
# --------------------------------------------------------------------------
# Lock = "candado". Mientras un hilo hace el respaldo, el candado está cerrado
# y nadie más puede empezar otro.
candado_respaldo = threading.Lock()


def _hacer_respaldo(ruta_destino: str):
    """Esto es lo que ejecuta el hilo secundario. Copia la base usando la API de
    respaldo de SQLite, que es segura aunque otras personas estén usando el sistema."""
    try:
        with closing(sqlite3.connect(database.DB_NAME)) as origen, closing(sqlite3.connect(ruta_destino)) as destino:
            with destino:
                origen.backup(destino)
    finally:
        candado_respaldo.release()  # abrimos el candado, pase lo que pase


def _listar_respaldos() -> list[dict]:
    carpeta = database.CARPETA_RESPALDOS
    if not os.path.isdir(carpeta):
        return []
    respaldos = []
    for nombre in sorted(os.listdir(carpeta), reverse=True):
        ruta = os.path.join(carpeta, nombre)
        if nombre.endswith(".db") and os.path.isfile(ruta):
            respaldos.append(
                {
                    "nombre": nombre,
                    "tamano_kb": round(os.path.getsize(ruta) / 1024, 1),
                    "fecha": datetime.fromtimestamp(os.path.getmtime(ruta)).isoformat(timespec="seconds"),
                }
            )
    return respaldos


@router.post("/datos/respaldos", status_code=202)
def crear_respaldo(usuario=Depends(obtener_usuario_actual)):
    """Inicia un respaldo en segundo plano y responde de inmediato (202 = 'aceptado')."""
    if not candado_respaldo.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Ya hay un respaldo en curso, espere unos segundos")
    try:
        os.makedirs(database.CARPETA_RESPALDOS, exist_ok=True)
        nombre = f"matricula_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(3)}.db"
        ruta = os.path.join(database.CARPETA_RESPALDOS, nombre)
        hilo = threading.Thread(target=_hacer_respaldo, args=(ruta,), daemon=True)
        hilo.start()
    except Exception:
        candado_respaldo.release()
        raise
    return {"mensaje": "Respaldo iniciado en segundo plano", "archivo": nombre}


@router.get("/datos/respaldos")
def listar_respaldos(usuario=Depends(obtener_usuario_actual)):
    return {"en_curso": candado_respaldo.locked(), "respaldos": _listar_respaldos()}


@router.get("/datos/respaldos/{nombre}")
def descargar_respaldo(nombre: str, usuario=Depends(obtener_usuario_actual)):
    # Solo se permite descargar nombres que existan en la lista: así nadie puede
    # pedir "../../seguridad.py" (ataque de ruta o "path traversal").
    if nombre not in [r["nombre"] for r in _listar_respaldos()]:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
    return FileResponse(os.path.join(database.CARPETA_RESPALDOS, nombre), filename=nombre)


# --------------------------------------------------------------------------
# DATOS DE EJEMPLO
# --------------------------------------------------------------------------
@router.post("/datos/demo", status_code=201)
def cargar_demo(usuario=Depends(obtener_usuario_actual)):
    creados = cargar_datos_demo()
    if not creados:
        raise HTTPException(
            status_code=409, detail="Ya hay datos en el sistema; los de ejemplo solo se cargan en una base vacía"
        )
    return {"mensaje": "Datos de ejemplo cargados", "creados": creados}
