"""Consultas de lectura para fichas, hojas de matrícula y panel interactivo."""
from fastapi import APIRouter, Depends, HTTPException, Query
from database import obtener_conexion
from seguridad import obtener_usuario_actual
from reglas import calcular_situacion

router = APIRouter(prefix="/academico", tags=["Expedientes académicos"], dependencies=[Depends(obtener_usuario_actual)])

SQL_MATRICULAS = """
    SELECT m.id, m.estudiante_id, e.nombre AS estudiante, e.cuenta, e.carrera,
           m.curso_id, c.codigo, c.nombre AS curso, c.creditos, c.periodo,
           c.horario, c.aula, d.nombre AS docente, m.estado, m.fecha_matricula,
           k.parcial1, k.parcial2, k.parcial3
    FROM matriculas m JOIN estudiantes e ON e.id=m.estudiante_id
    JOIN cursos c ON c.id=m.curso_id
    LEFT JOIN docentes d ON d.id=c.docente_id
    LEFT JOIN calificaciones k ON k.matricula_id=m.id
"""

def con_notas(fila):
    d = dict(fila)
    d["promedio"], d["situacion"] = calcular_situacion(d["parcial1"], d["parcial2"], d["parcial3"])
    return d

@router.get("/periodos")
def periodos():
    with obtener_conexion() as conexion:
        return [f[0] for f in conexion.execute("SELECT DISTINCT periodo FROM cursos ORDER BY periodo DESC")]

@router.get("/estudiantes/{estudiante_id}")
def expediente(estudiante_id: int, periodo: str | None = Query(default=None, max_length=30)):
    with obtener_conexion() as conexion:
        estudiante = conexion.execute("SELECT * FROM estudiantes WHERE id=?", (estudiante_id,)).fetchone()
        if not estudiante:
            raise HTTPException(404, "Estudiante no encontrado")
        historial = [con_notas(f) for f in conexion.execute(SQL_MATRICULAS + " WHERE e.id=? ORDER BY c.periodo DESC, c.codigo", (estudiante_id,))]
    hoja = [f for f in historial if (periodo is None or f["periodo"] == periodo) and f["estado"] == "activa"]
    aprobadas = [f for f in historial if f["estado"] == "activa" and f["situacion"] == "Aprobado"]
    return {"estudiante":dict(estudiante), "periodo":periodo, "historial":historial, "hoja":hoja,
            "resumen":{"clases_inscritas":len(hoja), "creditos_inscritos":sum(f["creditos"] for f in hoja),
                       "clases_en_proceso":sum(f["situacion"] == "En proceso" for f in hoja),
                       "creditos_aprobados":sum(f["creditos"] for f in aprobadas)}}

@router.get("/docentes/{docente_id}")
def carga_docente(docente_id: int, periodo: str | None = Query(default=None, max_length=30)):
    with obtener_conexion() as conexion:
        docente = conexion.execute("SELECT * FROM docentes WHERE id=?", (docente_id,)).fetchone()
        if not docente:
            raise HTTPException(404, "Docente no encontrado")
        cursos = [dict(f) for f in conexion.execute("""
            SELECT c.*, (SELECT COUNT(*) FROM matriculas m WHERE m.curso_id=c.id AND m.estado='activa') AS matriculados
            FROM cursos c WHERE c.docente_id=? AND (? IS NULL OR c.periodo=?) ORDER BY c.periodo DESC, c.codigo
        """, (docente_id, periodo, periodo))]
    return {"docente":dict(docente), "cursos":cursos, "total_cursos":len(cursos),
            "total_inscripciones":sum(c["matriculados"] for c in cursos)}

@router.get("/cursos/{curso_id}")
def lista_curso(curso_id: int):
    with obtener_conexion() as conexion:
        curso = conexion.execute("SELECT c.*, d.nombre AS docente FROM cursos c LEFT JOIN docentes d ON d.id=c.docente_id WHERE c.id=?", (curso_id,)).fetchone()
        if not curso:
            raise HTTPException(404, "Curso no encontrado")
        alumnos = [con_notas(f) for f in conexion.execute(SQL_MATRICULAS + " WHERE c.id=? AND m.estado='activa' ORDER BY e.nombre", (curso_id,))]
    return {"curso":dict(curso), "estudiantes":alumnos}

@router.get("/resumen")
def resumen(periodo: str | None = Query(default=None, max_length=30)):
    with obtener_conexion() as conexion:
        cursos = [dict(f) for f in conexion.execute("""
            SELECT c.*, d.nombre AS docente,
                   (SELECT COUNT(*) FROM matriculas m WHERE m.curso_id=c.id AND m.estado='activa') AS matriculados
            FROM cursos c LEFT JOIN docentes d ON d.id=c.docente_id
            WHERE (? IS NULL OR c.periodo=?) ORDER BY c.codigo
        """, (periodo, periodo))]
        matriculas = [con_notas(f) for f in conexion.execute(SQL_MATRICULAS + " WHERE m.estado='activa' AND (? IS NULL OR c.periodo=?) ORDER BY m.fecha_matricula DESC, m.id DESC", (periodo, periodo))]
        alumnos = [dict(f) for f in conexion.execute("SELECT id, nombre, cuenta, carrera, correo FROM estudiantes ORDER BY nombre")]
        docentes = [dict(f) for f in conexion.execute("SELECT * FROM docentes ORDER BY nombre")]
    if periodo is not None:
        ids = {m["estudiante_id"] for m in matriculas}
        alumnos = [e for e in alumnos if e["id"] in ids]
        ids = {c["docente_id"] for c in cursos}
        docentes = [d for d in docentes if d["id"] in ids]
    carga = [{**d, "cursos":sum(c["docente_id"] == d["id"] for c in cursos),
              "inscripciones":sum(c["matriculados"] for c in cursos if c["docente_id"] == d["id"])} for d in docentes]
    situacion = {s:sum(m["situacion"] == s for m in matriculas) for s in ("Aprobado", "Reprobado", "En proceso")}
    return {"periodo":periodo, "cursos":cursos, "matriculas":matriculas, "estudiantes":alumnos, "docentes":carga,
            "totales":{"estudiantes":len(alumnos), "docentes":len(carga), "cursos":len(cursos), "matriculas":len(matriculas)},
            "situacion":situacion, "cupos":sum(c["cupo"] for c in cursos), "ocupados":len(matriculas)}
