"""
routers/cursos.py  -  CRUD de cursos (cada curso puede tener un docente)
"""
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from database import mensaje_integridad, obtener_conexion
from esquemas import CursoCrear, CursoRespuesta
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Cursos"])

# Trae el curso + el nombre del docente + cuántos estudiantes lo llevan.
SELECT_CURSO = """
    SELECT c.id, c.codigo, c.nombre, c.creditos, c.cupo, c.docente_id, c.periodo, c.horario, c.aula,
           d.nombre AS docente_nombre,
           (SELECT COUNT(*) FROM matriculas m
            WHERE m.curso_id = c.id AND m.estado = 'activa') AS matriculados
    FROM cursos c
    LEFT JOIN docentes d ON d.id = c.docente_id
"""


def _validar_docente(conexion, docente_id):
    if docente_id is None:
        return
    existe = conexion.execute("SELECT id FROM docentes WHERE id = ?", (docente_id,)).fetchone()
    if existe is None:
        raise HTTPException(status_code=404, detail="Docente no encontrado")


@router.post("/cursos", response_model=CursoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_curso(curso: CursoCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        with obtener_conexion() as conexion:
            _validar_docente(conexion, curso.docente_id)
            cursor = conexion.execute(
                "INSERT INTO cursos (codigo, nombre, creditos, cupo, docente_id, periodo, horario, aula) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (curso.codigo, curso.nombre, curso.creditos, curso.cupo, curso.docente_id, curso.periodo, curso.horario, curso.aula),
            )
            fila = conexion.execute(SELECT_CURSO + " WHERE c.id = ?", (cursor.lastrowid,)).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409, detail=mensaje_integridad(error, "Ya existe un curso con ese código")
        )


@router.get("/cursos", response_model=list[CursoRespuesta])
def listar_cursos(
    buscar: Optional[str] = None,
    docente_id: Optional[int] = None,
    usuario=Depends(obtener_usuario_actual),
):
    sql = SELECT_CURSO + " WHERE 1 = 1"
    parametros: list = []
    if buscar:
        sql += " AND (c.codigo LIKE ? OR c.nombre LIKE ?)"
        parametros += [f"%{buscar}%"] * 2
    if docente_id is not None:
        sql += " AND c.docente_id = ?"
        parametros.append(docente_id)
    sql += " ORDER BY c.id"
    with obtener_conexion() as conexion:
        return [dict(fila) for fila in conexion.execute(sql, parametros).fetchall()]


@router.get("/cursos/{curso_id}", response_model=CursoRespuesta)
def obtener_curso(curso_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        fila = conexion.execute(SELECT_CURSO + " WHERE c.id = ?", (curso_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return dict(fila)


@router.put("/cursos/{curso_id}", response_model=CursoRespuesta)
def actualizar_curso(curso_id: int, curso: CursoCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        with obtener_conexion() as conexion:
            _validar_docente(conexion, curso.docente_id)
            ocupados = conexion.execute("SELECT COUNT(*) FROM matriculas WHERE curso_id=? AND estado='activa'", (curso_id,)).fetchone()[0]
            if curso.cupo < ocupados:
                raise HTTPException(409, "El cupo no puede ser menor que las matrículas activas")
            original = conexion.execute("SELECT periodo FROM cursos WHERE id=?", (curso_id,)).fetchone()
            tiene_historial = conexion.execute("SELECT 1 FROM matriculas WHERE curso_id=? LIMIT 1", (curso_id,)).fetchone()
            if original and tiene_historial and original["periodo"] != "Sin período" and original["periodo"] != curso.periodo:
                raise HTTPException(409, "El período de un curso con matrículas se conserva para proteger el historial")
            cursor = conexion.execute(
                """
                UPDATE cursos
                SET codigo = ?, nombre = ?, creditos = ?, cupo = ?, docente_id = ?, periodo = ?, horario = ?, aula = ?
                WHERE id = ?
                """,
                (curso.codigo, curso.nombre, curso.creditos, curso.cupo, curso.docente_id, curso.periodo, curso.horario, curso.aula, curso_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Curso no encontrado")
            fila = conexion.execute(SELECT_CURSO + " WHERE c.id = ?", (curso_id,)).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=mensaje_integridad(error, "Ya existe otro curso con ese código"),
        )


@router.delete("/cursos/{curso_id}")
def eliminar_curso(curso_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        en_uso = conexion.execute(
            "SELECT id FROM matriculas WHERE curso_id = ?", (curso_id,)
        ).fetchone()
        if en_uso:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar: el curso tiene matrículas registradas",
            )
        cursor = conexion.execute("DELETE FROM cursos WHERE id = ?", (curso_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Curso no encontrado")
    return {"mensaje": "Curso eliminado correctamente"}
