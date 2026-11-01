"""
routers/calificaciones.py  -  Módulo 5: notas de los tres parciales por matrícula

Cada matrícula ACTIVA tiene (o puede tener) una fila en `calificaciones`.
El promedio y la situación (Aprobado / Reprobado / En proceso) NO se guardan:
se calculan con reglas.calcular_situacion() cada vez que se consultan.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from database import obtener_conexion
from esquemas import CalificacionGuardar, CalificacionRespuesta
from reglas import calcular_situacion
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Calificaciones"])

# LEFT JOIN: aparecen todas las matrículas activas, tengan o no notas todavía.
SELECT_CALIFICACION = """
    SELECT m.id AS matricula_id, e.id AS estudiante_id, e.nombre AS estudiante_nombre,
           c.id AS curso_id, c.codigo AS curso_codigo, c.nombre AS curso_nombre,
           k.parcial1, k.parcial2, k.parcial3
    FROM matriculas m
    JOIN estudiantes e ON e.id = m.estudiante_id
    JOIN cursos c ON c.id = m.curso_id
    LEFT JOIN calificaciones k ON k.matricula_id = m.id
    WHERE m.estado = 'activa'
"""


def _con_promedio(fila) -> dict:
    datos = dict(fila)
    promedio, situacion = calcular_situacion(datos["parcial1"], datos["parcial2"], datos["parcial3"])
    datos["promedio"] = promedio
    datos["situacion"] = situacion
    return datos


@router.get("/calificaciones", response_model=list[CalificacionRespuesta])
def listar_calificaciones(
    curso_id: Optional[int] = None,
    buscar: Optional[str] = None,
    situacion: Optional[str] = None,
    usuario=Depends(obtener_usuario_actual),
):
    sql = SELECT_CALIFICACION
    parametros: list = []
    if curso_id is not None:
        sql += " AND c.id = ?"
        parametros.append(curso_id)
    if buscar:
        sql += " AND (e.nombre LIKE ? OR e.cuenta LIKE ?)"
        parametros += [f"%{buscar}%"] * 2
    sql += " ORDER BY c.codigo, e.nombre"
    with obtener_conexion() as conexion:
        filas = conexion.execute(sql, parametros).fetchall()
    resultado = [_con_promedio(fila) for fila in filas]
    if situacion:  # la situación se calcula en Python, por eso se filtra aquí
        resultado = [r for r in resultado if r["situacion"] == situacion]
    return resultado


@router.get("/calificaciones/matricula/{matricula_id}", response_model=CalificacionRespuesta)
def obtener_calificacion(matricula_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        fila = conexion.execute(SELECT_CALIFICACION + " AND m.id = ?", (matricula_id,)).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Matrícula activa no encontrada")
    return _con_promedio(fila)


@router.put("/calificaciones/matricula/{matricula_id}", response_model=CalificacionRespuesta)
def guardar_calificacion(
    matricula_id: int, notas: CalificacionGuardar, usuario=Depends(obtener_usuario_actual)
):
    """Crea o reemplaza las notas de una matrícula (si ya existían, las actualiza)."""
    with obtener_conexion() as conexion:
        matricula = conexion.execute(
            "SELECT id, estado FROM matriculas WHERE id = ?", (matricula_id,)
        ).fetchone()
        if matricula is None:
            raise HTTPException(status_code=404, detail="Matrícula no encontrada")
        if matricula["estado"] != "activa":
            raise HTTPException(
                status_code=409, detail="No se pueden calificar matrículas retiradas"
            )

        existe = conexion.execute(
            "SELECT id FROM calificaciones WHERE matricula_id = ?", (matricula_id,)
        ).fetchone()
        if existe:
            conexion.execute(
                "UPDATE calificaciones SET parcial1 = ?, parcial2 = ?, parcial3 = ? WHERE matricula_id = ?",
                (notas.parcial1, notas.parcial2, notas.parcial3, matricula_id),
            )
        else:
            conexion.execute(
                "INSERT INTO calificaciones (matricula_id, parcial1, parcial2, parcial3) VALUES (?, ?, ?, ?)",
                (matricula_id, notas.parcial1, notas.parcial2, notas.parcial3),
            )
        fila = conexion.execute(SELECT_CALIFICACION + " AND m.id = ?", (matricula_id,)).fetchone()
        return _con_promedio(fila)


@router.delete("/calificaciones/matricula/{matricula_id}")
def borrar_calificacion(matricula_id: int, usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        cursor = conexion.execute(
            "DELETE FROM calificaciones WHERE matricula_id = ?", (matricula_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Esa matrícula no tiene notas registradas")
    return {"mensaje": "Notas eliminadas correctamente"}
