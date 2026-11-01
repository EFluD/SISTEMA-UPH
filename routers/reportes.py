"""
routers/reportes.py  -  Módulo 6: estadísticas, filtros y paginación

Usa colecciones de Python (listas, diccionarios, sorted, sum) sobre los datos
que devuelve SQLite para armar los indicadores del reporte.
"""
from typing import Optional

from fastapi import APIRouter, Depends

from database import obtener_conexion
from reglas import calcular_situacion
from seguridad import obtener_usuario_actual

router = APIRouter(tags=["Reportes"])


@router.get("/reportes/estadisticas")
def estadisticas(usuario=Depends(obtener_usuario_actual)):
    with obtener_conexion() as conexion:
        # 1) Ocupación de cada curso
        cursos = [
            dict(f)
            for f in conexion.execute(
                """
                SELECT c.id, c.codigo, c.nombre, c.cupo, d.nombre AS docente,
                       (SELECT COUNT(*) FROM matriculas m
                        WHERE m.curso_id = c.id AND m.estado = 'activa') AS matriculados
                FROM cursos c LEFT JOIN docentes d ON d.id = c.docente_id
                ORDER BY c.codigo
                """
            )
        ]
        for c in cursos:
            c["ocupacion"] = round(100 * c["matriculados"] / c["cupo"]) if c["cupo"] else 0

        # 2) Estudiantes por carrera
        por_carrera = [
            dict(f)
            for f in conexion.execute(
                "SELECT carrera, COUNT(*) AS total FROM estudiantes GROUP BY carrera ORDER BY total DESC"
            )
        ]

        # 3) Notas: calculamos el promedio por curso y por estudiante en Python
        notas = conexion.execute(
            """
            SELECT c.id AS curso_id, c.codigo, e.id AS estudiante_id, e.nombre AS estudiante,
                   k.parcial1, k.parcial2, k.parcial3
            FROM calificaciones k
            JOIN matriculas m ON m.id = k.matricula_id AND m.estado = 'activa'
            JOIN cursos c ON c.id = m.curso_id
            JOIN estudiantes e ON e.id = m.estudiante_id
            """
        ).fetchall()

        # 4) Carga de cada docente
        carga = [
            dict(f)
            for f in conexion.execute(
                """
                SELECT d.id, d.nombre, d.especialidad, COUNT(DISTINCT c.id) AS cursos,
                       COUNT(m.id) AS estudiantes
                FROM docentes d
                LEFT JOIN cursos c ON c.docente_id = d.id
                LEFT JOIN matriculas m ON m.curso_id = c.id AND m.estado = 'activa'
                GROUP BY d.id ORDER BY estudiantes DESC, d.nombre
                """
            )
        ]

    situacion = {"Aprobado": 0, "Reprobado": 0, "En proceso": 0}
    promedios_curso: dict[str, list[float]] = {}
    promedios_estudiante: dict[int, dict] = {}
    for fila in notas:
        promedio, estado = calcular_situacion(fila["parcial1"], fila["parcial2"], fila["parcial3"])
        situacion[estado] += 1
        if promedio is None:
            continue
        promedios_curso.setdefault(fila["codigo"], []).append(promedio)
        datos = promedios_estudiante.setdefault(
            fila["estudiante_id"], {"estudiante": fila["estudiante"], "notas": []}
        )
        datos["notas"].append(promedio)

    promedio_por_curso = [
        {"codigo": codigo, "promedio": round(sum(lista) / len(lista), 1), "evaluados": len(lista)}
        for codigo, lista in sorted(promedios_curso.items())
    ]
    ranking = sorted(
        (
            {
                "estudiante": d["estudiante"],
                "promedio": round(sum(d["notas"]) / len(d["notas"]), 1),
                "cursos": len(d["notas"]),
            }
            for d in promedios_estudiante.values()
        ),
        key=lambda x: x["promedio"],
        reverse=True,
    )[:5]
    todos = [p for lista in promedios_curso.values() for p in lista]

    return {
        "ocupacion_cursos": cursos,
        "estudiantes_por_carrera": por_carrera,
        "situacion": situacion,
        "promedio_por_curso": promedio_por_curso,
        "mejores_promedios": ranking,
        "carga_docentes": carga,
        "promedio_general": round(sum(todos) / len(todos), 1) if todos else None,
    }


ORDENES = {
    "fecha": "m.fecha_matricula",
    "estudiante": "e.nombre",
    "curso": "c.codigo",
    "estado": "m.estado",
}


@router.get("/reportes/matriculas")
def reporte_matriculas(
    estado: Optional[str] = None,
    curso_id: Optional[int] = None,
    carrera: Optional[str] = None,
    buscar: Optional[str] = None,
    orden: str = "fecha",
    descendente: bool = True,
    pagina: int = 1,
    por_pagina: int = 10,
    usuario=Depends(obtener_usuario_actual),
):
    """Listado de matrículas con filtros, orden y paginación.
    Devuelve: total, pagina, por_pagina, paginas e items."""
    pagina = max(pagina, 1)
    por_pagina = min(max(por_pagina, 1), 100)

    condiciones = ["1 = 1"]
    parametros: list = []
    if estado:
        condiciones.append("m.estado = ?")
        parametros.append(estado)
    if curso_id is not None:
        condiciones.append("m.curso_id = ?")
        parametros.append(curso_id)
    if carrera:
        condiciones.append("e.carrera = ?")
        parametros.append(carrera)
    if buscar:
        condiciones.append("(e.nombre LIKE ? OR e.cuenta LIKE ?)")
        parametros += [f"%{buscar}%"] * 2
    donde = " AND ".join(condiciones)

    # El nombre de la columna NO se puede pasar como parámetro (?), por eso se toma
    # de una lista fija: así nadie puede inyectar SQL con ?orden=...
    columna = ORDENES.get(orden, ORDENES["fecha"])
    sentido = "DESC" if descendente else "ASC"

    desde = """
        FROM matriculas m
        JOIN estudiantes e ON e.id = m.estudiante_id
        JOIN cursos c ON c.id = m.curso_id
        LEFT JOIN docentes d ON d.id = c.docente_id
    """
    with obtener_conexion() as conexion:
        total = conexion.execute(f"SELECT COUNT(*) AS t {desde} WHERE {donde}", parametros).fetchone()["t"]
        filas = conexion.execute(
            f"""
            SELECT m.id, e.nombre AS estudiante, e.cuenta, e.carrera,
                   c.codigo AS curso_codigo, c.nombre AS curso_nombre,
                   d.nombre AS docente, m.fecha_matricula, m.estado
            {desde} WHERE {donde}
            ORDER BY {columna} {sentido}, m.id DESC
            LIMIT ? OFFSET ?
            """,
            parametros + [por_pagina, (pagina - 1) * por_pagina],
        ).fetchall()

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "paginas": max((total + por_pagina - 1) // por_pagina, 1),
        "items": [dict(f) for f in filas],
    }
