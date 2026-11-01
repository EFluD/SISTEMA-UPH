"""
routers/docentes.py  -  Módulo 2: CRUD de docentes

Es el mismo patrón de estudiantes.py y cursos.py. Un docente puede tener varios
cursos (cursos.docente_id apunta a docentes.id).
"""
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from database import mensaje_integridad, obtener_conexion
from esquemas import DocenteCrear, DocenteRespuesta
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Docentes"])

# Cada docente devuelve también cuántos cursos tiene asignados.
SELECT_DOCENTE = """
    SELECT d.id, d.nombre, d.correo, d.especialidad,
           (SELECT COUNT(*) FROM cursos c WHERE c.docente_id = d.id) AS total_cursos
    FROM docentes d
"""


@router.post("/docentes", response_model=DocenteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_docente(docente: DocenteCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute(
                "INSERT INTO docentes (nombre, correo, especialidad) VALUES (?, ?, ?)",
                (docente.nombre, docente.correo, docente.especialidad),
            )
            fila = conexion.execute(SELECT_DOCENTE + " WHERE d.id = ?", (cursor.lastrowid,)).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409, detail=mensaje_integridad(error, "Ya existe un docente con ese correo")
        )


@router.get("/docentes", response_model=list[DocenteRespuesta])
def listar_docentes(buscar: Optional[str] = None, usuario=Depends(obtener_usuario_actual)):
    sql = SELECT_DOCENTE
    parametros: list = []
    if buscar:
        sql += " WHERE d.nombre LIKE ? OR d.correo LIKE ? OR d.especialidad LIKE ?"
        parametros = [f"%{buscar}%"] * 3
    sql += " ORDER BY d.id"
    with obtener_conexion() as conexion:
        return [dict(fila) for fila in conexion.execute(sql, parametros).fetchall()]


@router.get("/docentes/{docente_id}", response_model=DocenteRespuesta)
def obtener_docente(docente_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        fila = conexion.execute(SELECT_DOCENTE + " WHERE d.id = ?", (docente_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return dict(fila)


@router.put("/docentes/{docente_id}", response_model=DocenteRespuesta)
def actualizar_docente(docente_id: int, docente: DocenteCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute(
                "UPDATE docentes SET nombre = ?, correo = ?, especialidad = ? WHERE id = ?",
                (docente.nombre, docente.correo, docente.especialidad, docente_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Docente no encontrado")
            fila = conexion.execute(SELECT_DOCENTE + " WHERE d.id = ?", (docente_id,)).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=mensaje_integridad(error, "Ese correo ya pertenece a otro docente"),
        )


@router.delete("/docentes/{docente_id}")
def eliminar_docente(docente_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        en_uso = conexion.execute(
            "SELECT id FROM cursos WHERE docente_id = ?", (docente_id,)
        ).fetchone()
        if en_uso:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar: el docente tiene cursos asignados",
            )
        cursor = conexion.execute("DELETE FROM docentes WHERE id = ?", (docente_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Docente no encontrado")
    return {"mensaje": "Docente eliminado correctamente"}


@router.get("/docentes/{docente_id}/cursos")
def cursos_de_docente(docente_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        existe = conexion.execute("SELECT id FROM docentes WHERE id = ?", (docente_id,)).fetchone()
        if existe is None:
            raise HTTPException(status_code=404, detail="Docente no encontrado")
        filas = conexion.execute(
            """
            SELECT c.id, c.codigo, c.nombre, c.creditos, c.cupo,
                   (SELECT COUNT(*) FROM matriculas m
                    WHERE m.curso_id = c.id AND m.estado = 'activa') AS matriculados
            FROM cursos c WHERE c.docente_id = ? ORDER BY c.id
            """,
            (docente_id,),
        ).fetchall()
        return [dict(fila) for fila in filas]
