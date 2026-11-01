"""
routers/estudiantes.py  -  CRUD de estudiantes (con búsqueda)
"""
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from database import mensaje_integridad, obtener_conexion
from esquemas import EstudianteCrear, EstudianteRespuesta
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Estudiantes"])


@router.post(
    "/estudiantes",
    response_model=EstudianteRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear_estudiante(estudiante: EstudianteCrear, usuario=Depends(obtener_usuario_actual)):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO estudiantes (nombre, cuenta, carrera, correo, edad)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    estudiante.nombre,
                    estudiante.cuenta,
                    estudiante.carrera,
                    estudiante.correo,
                    estudiante.edad,
                ),
            )
            fila = conexion.execute(
                "SELECT * FROM estudiantes WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=mensaje_integridad(error, "La cuenta o el correo ya están registrados"),
        )


@router.get("/estudiantes", response_model=list[EstudianteRespuesta])
def listar_estudiantes(
    buscar: Optional[str] = None,
    carrera: Optional[str] = None,
    usuario=Depends(obtener_usuario_actual),
):
    """Lista estudiantes. ?buscar=ana filtra por nombre, cuenta o correo;
    ?carrera=... filtra por carrera exacta."""
    sql = "SELECT * FROM estudiantes WHERE 1 = 1"
    parametros: list = []
    if buscar:
        sql += " AND (nombre LIKE ? OR cuenta LIKE ? OR correo LIKE ?)"
        parametros += [f"%{buscar}%"] * 3
    if carrera:
        sql += " AND carrera = ?"
        parametros.append(carrera)
    sql += " ORDER BY id"
    with obtener_conexion() as conexion:
        filas = conexion.execute(sql, parametros).fetchall()
        return [dict(fila) for fila in filas]


@router.get("/estudiantes/{estudiante_id}", response_model=EstudianteRespuesta)
def obtener_estudiante(estudiante_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)
        ).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return dict(fila)


@router.put("/estudiantes/{estudiante_id}", response_model=EstudianteRespuesta)
def actualizar_estudiante(
    estudiante_id: int, estudiante: EstudianteCrear, usuario=Depends(obtener_usuario_actual)
):
    try:
        with obtener_conexion() as conexion:
            cursor = conexion.execute(
                """
                UPDATE estudiantes
                SET nombre = ?, cuenta = ?, carrera = ?, correo = ?, edad = ?
                WHERE id = ?
                """,
                (
                    estudiante.nombre,
                    estudiante.cuenta,
                    estudiante.carrera,
                    estudiante.correo,
                    estudiante.edad,
                    estudiante_id,
                ),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Estudiante no encontrado")
            fila = conexion.execute(
                "SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail=mensaje_integridad(
                error, "La cuenta o el correo ya pertenecen a otro estudiante"
            ),
        )


@router.delete("/estudiantes/{estudiante_id}")
def eliminar_estudiante(estudiante_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        en_uso = conexion.execute(
            "SELECT id FROM matriculas WHERE estudiante_id = ?", (estudiante_id,)
        ).fetchone()
        if en_uso:
            raise HTTPException(
                status_code=409,
                detail="No se puede eliminar: el estudiante tiene matrículas registradas",
            )
        cursor = conexion.execute("DELETE FROM estudiantes WHERE id = ?", (estudiante_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"mensaje": "Estudiante eliminado correctamente"}


# RETO (Semana 2): cursos de un estudiante específico
@router.get("/estudiantes/{estudiante_id}/matriculas")
def matriculas_de_estudiante(estudiante_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        existe = conexion.execute(
            "SELECT id FROM estudiantes WHERE id = ?", (estudiante_id,)
        ).fetchone()
        if existe is None:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        filas = conexion.execute(
            """
            SELECT m.id, c.codigo, c.nombre AS curso, m.fecha_matricula, m.estado
            FROM matriculas m
            JOIN cursos c ON c.id = m.curso_id
            WHERE m.estudiante_id = ?
            ORDER BY m.id
            """,
            (estudiante_id,),
        ).fetchall()
        return [dict(fila) for fila in filas]
