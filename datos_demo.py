"""
datos_demo.py  -  Datos de ejemplo (personas ficticias) para probar el sistema.

Se cargan desde el módulo "Datos" del panel o con:  python datos_demo.py
Solo se cargan si las tablas están vacías, así nunca se mezclan con datos reales.
"""
import random
import sqlite3
from datetime import datetime, timedelta

from database import crear_tablas, obtener_conexion

CARRERA = "Ingeniería en Sistemas Computacionales"

DOCENTES = [
    ("Marta Lilian Reyes", "marta.reyes@uph.edu.hn", "Programación y Algoritmos"),
    ("Carlos Andrés Mejía", "carlos.mejia@uph.edu.hn", "Bases de Datos"),
    ("Sofía Elena Paz", "sofia.paz@uph.edu.hn", "Matemática"),
    ("Jorge Luis Banegas", "jorge.banegas@uph.edu.hn", "Redes y Seguridad"),
    ("Karla Patricia Ordóñez", "karla.ordonez@uph.edu.hn", "Ingeniería de Software"),
]

CURSOS = [  # código, nombre, créditos, cupo, índice de docente
    ("MAT-101", "Matemática I", 4, 30, 2),
    ("IS-110", "Programación I", 4, 25, 0),
    ("IS-120", "Programación II", 4, 25, 0),
    ("IS-151", "Programación III", 4, 20, 0),
    ("IS-160", "Bases de Datos I", 4, 25, 1),
    ("IS-170", "Redes de Computadoras", 3, 20, 3),
    ("IS-180", "Ingeniería de Software", 4, 20, 4),
    ("FIS-101", "Física I", 4, 30, 2),
]

NOMBRES = [
    "Ana Lucía Martínez", "Luis Fernando Castillo", "María José Aguilar", "Diego Armando Cruz",
    "Daniela Michelle Flores", "José Miguel Rivera", "Fátima Nicole Herrera", "Kevin Josué Murillo",
    "Andrea Sofía Pineda", "Carlos Eduardo Lagos", "Gabriela Alejandra Soto", "Mario Antonio Valle",
    "Paola Estefanía Zelaya", "Rodrigo Alberto Núñez", "Lesly Yadira Colindres", "Brayan Esteban Ponce",
]


def cargar_datos_demo() -> dict:
    """Inserta los datos de ejemplo. Devuelve cuántos registros creó (o {} si ya había datos)."""
    crear_tablas()
    azar = random.Random(2026)  # misma semilla = siempre los mismos datos
    with obtener_conexion() as conexion:
        hay_datos = conexion.execute(
            "SELECT (SELECT COUNT(*) FROM estudiantes) + (SELECT COUNT(*) FROM cursos) "
            "+ (SELECT COUNT(*) FROM docentes) AS total"
        ).fetchone()["total"]
        if hay_datos:
            return {}

        ids_docentes = []
        for nombre, correo, especialidad in DOCENTES:
            cursor = conexion.execute(
                "INSERT INTO docentes (nombre, correo, especialidad) VALUES (?, ?, ?)",
                (nombre, correo, especialidad),
            )
            ids_docentes.append(cursor.lastrowid)

        ids_cursos = []
        for codigo, nombre, creditos, cupo, indice in CURSOS:
            cursor = conexion.execute(
                "INSERT INTO cursos (codigo, nombre, creditos, cupo, docente_id) VALUES (?, ?, ?, ?, ?)",
                (codigo, nombre, creditos, cupo, ids_docentes[indice]),
            )
            ids_cursos.append(cursor.lastrowid)

        for i, curso_id in enumerate(ids_cursos):
            inicio = 7 + (i % 4) * 2
            dias = "LU-MI" if i < 4 else "MA-JU"
            conexion.execute("UPDATE cursos SET periodo='2026-3', horario=?, aula=? WHERE id=?",
                             (f"{dias} · {inicio:02d}:00–{inicio+2:02d}:00", f"AULA-{i+1:02d}", curso_id))
        ids_estudiantes = []
        for i, nombre in enumerate(NOMBRES, start=1):
            usuario = nombre.lower().split()[0].replace("í", "i").replace("é", "e").replace("á", "a")
            cursor = conexion.execute(
                "INSERT INTO estudiantes (nombre, cuenta, carrera, correo, edad) VALUES (?, ?, ?, ?, ?)",
                (nombre, f"2026{1000 + i}", CARRERA, f"{usuario}{i}@uph.edu.hn", azar.randint(18, 27)),
            )
            ids_estudiantes.append(cursor.lastrowid)

        ahora = datetime.utcnow()
        matriculas = 0
        for estudiante_id in ids_estudiantes:
            for curso_id in azar.sample(ids_cursos, k=azar.randint(2, 4)):
                fecha = (ahora - timedelta(days=azar.randint(0, 30), minutes=azar.randint(0, 600)))
                try:
                    cursor = conexion.execute(
                        "INSERT INTO matriculas (estudiante_id, curso_id, fecha_matricula, estado) "
                        "VALUES (?, ?, ?, 'activa')",
                        (estudiante_id, curso_id, fecha.isoformat()),
                    )
                except sqlite3.IntegrityError:
                    continue
                matriculas += 1
                # Algunas notas completas, otras a medias y otras sin notas todavía
                tipo = azar.random()
                if tipo < 0.55:
                    notas = [azar.randint(48, 98) for _ in range(3)]
                elif tipo < 0.8:
                    notas = [azar.randint(55, 95), azar.randint(55, 95), None]
                else:
                    continue
                conexion.execute(
                    "INSERT INTO calificaciones (matricula_id, parcial1, parcial2, parcial3) VALUES (?, ?, ?, ?)",
                    (cursor.lastrowid, *notas),
                )
        # Una oferta anterior permite demostrar el filtro y el historial por período.
        anterior = conexion.execute("INSERT INTO cursos (codigo, nombre, creditos, cupo, docente_id, periodo, horario, aula) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                    ("IS-110-2026-1", "Programación I", 4, 25, ids_docentes[0], "2026-1", "LU-MI · 07:00–09:00", "LAB-01")).lastrowid
        for estudiante_id in ids_estudiantes[:4]:
            mid = conexion.execute("INSERT INTO matriculas (estudiante_id, curso_id, fecha_matricula, estado) VALUES (?, ?, ?, 'activa')", (estudiante_id, anterior, "2026-01-20T13:00:00")).lastrowid
            conexion.execute("INSERT INTO calificaciones (matricula_id, parcial1, parcial2, parcial3) VALUES (?, 80, 85, 90)", (mid,))
            matriculas += 1
    return {
        "docentes": len(DOCENTES),
        "cursos": len(CURSOS) + 1,
        "estudiantes": len(NOMBRES),
        "matriculas": matriculas,
    }


if __name__ == "__main__":
    resultado = cargar_datos_demo()
    print(resultado or "La base de datos ya tiene datos; no se cargó nada.")
