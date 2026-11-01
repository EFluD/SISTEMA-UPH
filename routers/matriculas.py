"""
routers/matriculas.py  -  Matricular y retirar (reglas de negocio: cupo y duplicados)
"""
import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from database import obtener_conexion
from esquemas import MatriculaCrear, MatriculaRespuesta
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Matrículas"])


def _fila_a_matricula(conexion, matricula_id: int) -> dict:
    fila = conexion.execute(
        """
        SELECT m.id, m.estudiante_id, e.nombre AS estudiante_nombre,
               m.curso_id, c.nombre AS curso_nombre, c.codigo AS curso_codigo,
               m.fecha_matricula, m.estado
        FROM matriculas m
        JOIN estudiantes e ON e.id = m.estudiante_id
        JOIN cursos c ON c.id = m.curso_id
        WHERE m.id = ?
        """,
        (matricula_id,),
    ).fetchone()
    return dict(fila)


@router.post(
    "/matriculas",
    response_model=MatriculaRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_matricula(datos: MatriculaCrear, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        conexion.execute("BEGIN IMMEDIATE")
        estudiante = conexion.execute(
            "SELECT id FROM estudiantes WHERE id = ?", (datos.estudiante_id,)
        ).fetchone()
        if estudiante is None:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        curso = conexion.execute(
            "SELECT * FROM cursos WHERE id = ?", (datos.curso_id,)
        ).fetchone()
        if curso is None:
            raise HTTPException(status_code=404, detail="Curso no encontrado")

        matriculados = conexion.execute(
            "SELECT COUNT(*) AS total FROM matriculas WHERE curso_id = ? AND estado = 'activa'",
            (datos.curso_id,),
        ).fetchone()["total"]
        if matriculados >= curso["cupo"]:
            raise HTTPException(status_code=409, detail="El curso ya no tiene cupo disponible")

        ya_matriculado = conexion.execute(
            """
            SELECT id FROM matriculas
            WHERE estudiante_id = ? AND curso_id = ? AND estado = 'activa'
            """,
            (datos.estudiante_id, datos.curso_id),
        ).fetchone()
        if ya_matriculado:
            raise HTTPException(
                status_code=409, detail="El estudiante ya está matriculado en ese curso"
            )

        # Si el estudiante ya estuvo matriculado y se retiró, reactivamos esa misma fila
        # (la pareja estudiante+curso es UNIQUE, no se puede insertar otra).
        retirada = conexion.execute(
            """
            SELECT id FROM matriculas
            WHERE estudiante_id = ? AND curso_id = ? AND estado = 'retirada'
            """,
            (datos.estudiante_id, datos.curso_id),
        ).fetchone()
        if retirada:
            conexion.execute(
                "UPDATE matriculas SET estado = 'activa', fecha_matricula = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), retirada["id"]),
            )
            return _fila_a_matricula(conexion, retirada["id"])

        try:
            cursor = conexion.execute(
                """
                INSERT INTO matriculas (estudiante_id, curso_id, fecha_matricula, estado)
                VALUES (?, ?, ?, 'activa')
                """,
                (datos.estudiante_id, datos.curso_id, datetime.utcnow().isoformat()),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=409, detail="El estudiante ya está matriculado en ese curso"
            )

        return _fila_a_matricula(conexion, cursor.lastrowid)


@router.get("/matriculas", response_model=list[MatriculaRespuesta])
def listar_matriculas(
    estado: Optional[str] = None,
    curso_id: Optional[int] = None,
    estudiante_id: Optional[int] = None,
    limite: Optional[int] = None,
    usuario=Depends(obtener_usuario_actual),
):
    """Filtros opcionales: ?estado=activa  ?curso_id=3  ?estudiante_id=5
    ?limite=5 devuelve solo las últimas 5 (las más recientes primero)."""
    sql = "SELECT id FROM matriculas WHERE 1 = 1"
    parametros: list = []
    if estado:
        sql += " AND estado = ?"
        parametros.append(estado)
    if curso_id is not None:
        sql += " AND curso_id = ?"
        parametros.append(curso_id)
    if estudiante_id is not None:
        sql += " AND estudiante_id = ?"
        parametros.append(estudiante_id)
    if limite:
        sql += " ORDER BY id DESC LIMIT ?"
        parametros.append(limite)
    else:
        sql += " ORDER BY id"
    with obtener_conexion() as conexion:
        filas = conexion.execute(sql, parametros).fetchall()
        return [_fila_a_matricula(conexion, fila["id"]) for fila in filas]


@router.get("/matriculas/{matricula_id}", response_model=MatriculaRespuesta)
def obtener_matricula(matricula_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        existe = conexion.execute(
            "SELECT id FROM matriculas WHERE id = ?", (matricula_id,)
        ).fetchone()
        if existe is None:
            raise HTTPException(status_code=404, detail="Matrícula no encontrada")
        return _fila_a_matricula(conexion, matricula_id)


@router.delete("/matriculas/{matricula_id}")
def retirar_matricula(matricula_id: int, usuario=Depends(obtener_usuario_actual)):
    """En vez de borrar la fila, la marcamos como 'retirada'. En un sistema de
    matrícula real conviene guardar el historial en lugar de eliminarlo."""
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "UPDATE matriculas SET estado = 'retirada' WHERE id = ? AND estado = 'activa'",
            (matricula_id,),
        )
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404, detail="Matrícula no encontrada o ya estaba retirada"
            )
    return {"mensaje": "Matrícula retirada correctamente"}
