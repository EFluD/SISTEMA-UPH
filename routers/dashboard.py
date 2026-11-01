"""
routers/dashboard.py  -  Resumen numérico que consume el panel
"""
from fastapi import APIRouter, Depends

from database import obtener_conexion
from esquemas import ResumenDashboard
from reglas import calcular_situacion
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Dashboard"])


def _contar(conexion, sql: str) -> int:
    return conexion.execute(sql).fetchone()["total"]


@router.get("/dashboard/resumen", response_model=ResumenDashboard)
def resumen_dashboard(usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        total_estudiantes = _contar(conexion, "SELECT COUNT(*) AS total FROM estudiantes")
        total_docentes = _contar(conexion, "SELECT COUNT(*) AS total FROM docentes")
        total_cursos = _contar(conexion, "SELECT COUNT(*) AS total FROM cursos")
        total_matriculas_activas = _contar(
            conexion, "SELECT COUNT(*) AS total FROM matriculas WHERE estado = 'activa'"
        )
        suma_cupos = _contar(conexion, "SELECT COALESCE(SUM(cupo), 0) AS total FROM cursos")
        notas = conexion.execute(
            """
            SELECT k.parcial1, k.parcial2, k.parcial3
            FROM calificaciones k JOIN matriculas m ON m.id = k.matricula_id
            WHERE m.estado = 'activa'
            """
        ).fetchall()

    situaciones = {"Aprobado": 0, "Reprobado": 0, "En proceso": 0}
    promedios = []
    for fila in notas:
        promedio, situacion = calcular_situacion(fila["parcial1"], fila["parcial2"], fila["parcial3"])
        situaciones[situacion] += 1
        if promedio is not None:
            promedios.append(promedio)

    return {
        "total_estudiantes": total_estudiantes,
        "total_docentes": total_docentes,
        "total_cursos": total_cursos,
        "total_matriculas_activas": total_matriculas_activas,
        "cupos_disponibles": max(suma_cupos - total_matriculas_activas, 0),
        "promedio_general": round(sum(promedios) / len(promedios), 1) if promedios else None,
        "aprobados": situaciones["Aprobado"],
        "reprobados": situaciones["Reprobado"],
        "en_proceso": situaciones["En proceso"],
    }
