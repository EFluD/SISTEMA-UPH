"""
database.py  -  Capa de acceso a datos
Aquí vive TODO lo que tiene que ver con SQLite: la conexión y la creación de tablas.
Ningún otro archivo debe llamar a sqlite3.connect() directamente
(la única excepción es el respaldo, que usa la API de backup de SQLite).

Tablas del sistema:
  usuarios, estudiantes, docentes, cursos, matriculas, calificaciones
"""
import os
from contextlib import contextmanager
import sqlite3

# Se puede cambiar con variables de entorno (las pruebas usan una base temporal).
DB_NAME = os.environ.get("MATRICULA_DB", "matricula.db")
CARPETA_RESPALDOS = os.environ.get("MATRICULA_RESPALDOS", "respaldos")


@contextmanager
def obtener_conexion():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def mensaje_integridad(error: sqlite3.IntegrityError, mensaje_duplicado: str) -> str:
    """Un IntegrityError puede ser por dato repetido (UNIQUE) o por una referencia
    a algo que no existe (FOREIGN KEY). Devolvemos un mensaje acorde a cada caso."""
    if "FOREIGN KEY" in str(error).upper():
        return "El registro relacionado (docente, estudiante o curso) no existe"
    return mensaje_duplicado


def _agregar_columna_si_falta(conexion, tabla: str, columna: str, definicion: str):
    """CREATE TABLE IF NOT EXISTS no agrega columnas a una tabla que ya existe.
    Por eso, si la base de datos es de una versión anterior, la actualizamos aquí
    con ALTER TABLE (así no hace falta borrar matricula.db)."""
    columnas = [fila["name"] for fila in conexion.execute(f"PRAGMA table_info({tabla})")]
    if columna not in columnas:
        conexion.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")


def crear_tablas():
    with obtener_conexion() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario TEXT NOT NULL UNIQUE,
                contrasena_hash TEXT NOT NULL,
                contrasena_salt TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'admin',
                token TEXT,
                token_expira TEXT
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS estudiantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cuenta TEXT NOT NULL UNIQUE,
                carrera TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                edad INTEGER NOT NULL
            )
            """
        )
        # --- Módulo 2: Docentes ---
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS docentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL UNIQUE,
                especialidad TEXT NOT NULL
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                creditos INTEGER NOT NULL,
                cupo INTEGER NOT NULL,
                docente_id INTEGER REFERENCES docentes (id)
            )
            """
        )
        # Si matricula.db viene de la Semana 2, a cursos le falta docente_id:
        _agregar_columna_si_falta(conexion, "cursos", "docente_id", "INTEGER REFERENCES docentes (id)")

        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS matriculas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estudiante_id INTEGER NOT NULL,
                curso_id INTEGER NOT NULL,
                fecha_matricula TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'activa',
                FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id),
                FOREIGN KEY (curso_id) REFERENCES cursos (id),
                UNIQUE (estudiante_id, curso_id)
            )
            """
        )
        # --- Módulo 5: Calificaciones (una fila por matrícula) ---
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS calificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula_id INTEGER NOT NULL UNIQUE,
                parcial1 REAL,
                parcial2 REAL,
                parcial3 REAL,
                FOREIGN KEY (matricula_id) REFERENCES matriculas (id)
            )
            """
        )

    # Migración aditiva: conserva estudiantes, cursos y notas de la versión 3.
    with obtener_conexion() as conexion:
        for columna, definicion in (
            ("periodo", "TEXT NOT NULL DEFAULT 'Sin período'"),
            ("horario", "TEXT NOT NULL DEFAULT ''"),
            ("aula", "TEXT NOT NULL DEFAULT ''")):
            _agregar_columna_si_falta(conexion, "cursos", columna, definicion)
        _agregar_columna_si_falta(conexion, "usuarios", "iteraciones", "INTEGER NOT NULL DEFAULT 100000")
        _agregar_columna_si_falta(conexion, "usuarios", "csrf_hash", "TEXT")
        conexion.executescript("""
            CREATE TABLE IF NOT EXISTS intentos_login (
                nombre TEXT PRIMARY KEY, cantidad INTEGER NOT NULL, inicio INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER,
                accion TEXT NOT NULL, ruta TEXT NOT NULL,
                fecha TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
