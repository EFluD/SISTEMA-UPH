"""
test_api.py  -  Pruebas automáticas de todos los módulos.
Ejecutar con:  python -m pytest -v
"""
import time

import pytest
from fastapi.testclient import TestClient

from main import app
from reglas import calcular_situacion


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as cliente:
        r = cliente.post("/auth/login", json={"nombre_usuario": "admin", "contrasena": "AdminPruebas2026!"})
        assert r.status_code == 200
        cliente.headers.update({"Authorization": f"Bearer {r.json()['token']}"})
        yield cliente


# ---------------------------------------------------------------- reglas puras
def test_reglas_calificacion():
    assert calcular_situacion(80, 70, 90) == (80.0, "Aprobado")
    assert calcular_situacion(60, 60, 60) == (60.0, "Reprobado")
    assert calcular_situacion(90, None, 80) == (None, "En proceso")


# ----------------------------------------------------------------- seguridad
def test_rutas_protegidas_sin_token():
    with TestClient(app) as anonimo:
        for ruta in ["/estudiantes", "/docentes", "/cursos", "/matriculas", "/calificaciones",
                     "/reportes/estadisticas", "/datos/respaldos", "/dashboard/resumen"]:
            assert anonimo.get(ruta).status_code == 401, ruta
        assert anonimo.get("/login").status_code == 200
        assert anonimo.get("/dashboard", follow_redirects=False).status_code in (302, 307)


# ------------------------------------------------------------------ módulos
def test_flujo_completo(c):
    # Docente -> Curso -> Estudiante -> Matrícula -> Nota
    d = c.post("/docentes", json={"nombre": "Marta Reyes", "correo": "marta@uph.edu.hn",
                                  "especialidad": "Programación"})
    assert d.status_code == 201, d.text
    assert c.post("/docentes", json={"nombre": "Otra Persona", "correo": "marta@uph.edu.hn",
                                     "especialidad": "Redes"}).status_code == 409

    cu = c.post("/cursos", json={"codigo": "IS151", "nombre": "Programación III", "creditos": 4,
                                 "cupo": 1, "docente_id": d.json()["id"]})
    assert cu.status_code == 201, cu.text
    assert cu.json()["docente_nombre"] == "Marta Reyes"
    # docente inexistente -> 404, no un 409 engañoso
    assert c.post("/cursos", json={"codigo": "X1", "nombre": "Curso X", "creditos": 3, "cupo": 5,
                                   "docente_id": 999}).status_code == 404

    e = c.post("/estudiantes", json={"nombre": "Ana Pérez", "cuenta": "2026001", "carrera": "Sistemas",
                                     "correo": "ana@uph.edu.hn", "edad": 20})
    assert e.status_code == 201, e.text
    e2 = c.post("/estudiantes", json={"nombre": "Luis Mora", "cuenta": "2026002", "carrera": "Sistemas",
                                      "correo": "luis@uph.edu.hn", "edad": 21})
    assert e2.status_code == 201

    m = c.post("/matriculas", json={"estudiante_id": e.json()["id"], "curso_id": cu.json()["id"]})
    assert m.status_code == 201
    mid = m.json()["id"]
    # duplicado -> 409; cupo lleno (cupo=1) -> 409
    assert c.post("/matriculas", json={"estudiante_id": e.json()["id"], "curso_id": cu.json()["id"]}).status_code == 409
    assert c.post("/matriculas", json={"estudiante_id": e2.json()["id"], "curso_id": cu.json()["id"]}).status_code == 409

    # Docente con cursos no se puede borrar
    assert c.delete(f"/docentes/{d.json()['id']}").status_code == 409
    assert c.get(f"/docentes/{d.json()['id']}/cursos").json()[0]["matriculados"] == 1

    # Calificaciones
    g = c.get("/calificaciones", params={"curso_id": cu.json()["id"]})
    assert g.status_code == 200 and g.json()[0]["situacion"] == "En proceso"
    r = c.put(f"/calificaciones/matricula/{mid}", json={"parcial1": 80, "parcial2": 75, "parcial3": 90})
    assert r.status_code == 200, r.text
    assert r.json()["promedio"] == 81.7 and r.json()["situacion"] == "Aprobado"
    assert c.put(f"/calificaciones/matricula/{mid}", json={"parcial1": 101}).status_code == 422
    r = c.put(f"/calificaciones/matricula/{mid}", json={"parcial1": 50, "parcial2": 50, "parcial3": 50})
    assert r.json()["situacion"] == "Reprobado"
    assert c.put("/calificaciones/matricula/9999", json={}).status_code == 404

    # Dashboard y reportes
    res = c.get("/dashboard/resumen").json()
    assert res["total_matriculas_activas"] == 1 and res["total_docentes"] == 1
    assert res["reprobados"] == 1 and res["promedio_general"] == 50.0
    est = c.get("/reportes/estadisticas").json()
    assert est["ocupacion_cursos"][0]["ocupacion"] == 100
    assert est["situacion"]["Reprobado"] == 1
    rep = c.get("/reportes/matriculas", params={"estado": "activa", "por_pagina": 5}).json()
    assert rep["total"] == 1 and rep["items"][0]["docente"] == "Marta Reyes"
    # intento de inyección en el orden: se ignora y no rompe
    assert c.get("/reportes/matriculas", params={"orden": "id; DROP TABLE cursos"}).status_code == 200

    # Búsqueda
    assert len(c.get("/estudiantes", params={"buscar": "ana"}).json()) == 1
    assert len(c.get("/cursos", params={"buscar": "IS151"}).json()) == 1

    # Retirar y volver a matricular (reactiva la misma fila)
    assert c.delete(f"/matriculas/{mid}").status_code == 200
    assert c.put(f"/calificaciones/matricula/{mid}", json={"parcial1": 90}).status_code == 409
    again = c.post("/matriculas", json={"estudiante_id": e.json()["id"], "curso_id": cu.json()["id"]})
    assert again.status_code == 201 and again.json()["id"] == mid

    r = c.get(f"/estudiantes/{e.json()['id']}/matriculas")
    assert r.status_code == 200 and len(r.json()) == 1


def test_editar_y_borrar(c):
    d = c.post("/docentes", json={"nombre": "Borrar Docente", "correo": "borrar@uph.edu.hn",
                                  "especialidad": "Redes"}).json()
    r = c.put(f"/docentes/{d['id']}", json={"nombre": "Docente Editado", "correo": "borrar@uph.edu.hn",
                                            "especialidad": "Seguridad"})
    assert r.status_code == 200 and r.json()["especialidad"] == "Seguridad"
    assert c.delete(f"/docentes/{d['id']}").status_code == 200
    assert c.get(f"/docentes/{d['id']}").status_code == 404


def test_usuarios(c):
    u = c.post("/auth/usuarios", json={"nombre_usuario": "profe", "contrasena": "DocentePruebas2026!", "rol": "docente"})
    assert u.status_code == 201
    assert c.delete(f"/auth/usuarios/{u.json()['id']}").status_code == 200
    yo = c.get("/auth/yo").json()
    assert c.delete(f"/auth/usuarios/{yo['id']}").status_code == 409


# ---------------------------------------------------------------- CSV / datos
def test_exportar_importar_csv(c):
    r = c.get("/datos/exportar/estudiantes")
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert r.content.startswith(b"\xef\xbb\xbfid,nombre")
    assert c.get("/datos/exportar/usuarios").status_code == 404  # no se exportan contraseñas

    csv_texto = (
        "nombre;cuenta;carrera;correo;edad\n"
        "Rosa Elena Díaz;2026101;Sistemas;rosa@uph.edu.hn;19\n"
        "Pedro Pablo Cruz;2026001;Sistemas;pedro@uph.edu.hn;22\n"   # cuenta repetida
        "X;2026103;Sistemas;correo-malo;19\n"                         # datos inválidos
    )
    r = c.post("/datos/importar/estudiantes", json={"contenido": csv_texto})
    assert r.status_code == 200, r.text
    assert r.json()["insertados"] == 1 and r.json()["omitidos"] == 2
    assert c.post("/datos/importar/estudiantes", json={"contenido": "a,b\n1,2"}).status_code == 422
    assert c.post("/datos/importar/usuarios", json={"contenido": "x"}).status_code == 404


def test_respaldo_en_segundo_plano(c):
    r = c.post("/datos/respaldos")
    assert r.status_code == 202
    nombre = r.json()["archivo"]
    for _ in range(50):  # esperamos a que el hilo termine
        estado = c.get("/datos/respaldos").json()
        if not estado["en_curso"]:
            break
        time.sleep(0.1)
    assert nombre in [x["nombre"] for x in estado["respaldos"]]
    assert c.get(f"/datos/respaldos/{nombre}").status_code == 200
    assert c.get("/datos/respaldos/..%2Fseguridad.py").status_code == 404


def test_datos_demo_solo_en_base_vacia(c):
    assert c.post("/datos/demo").status_code == 409  # ya hay datos de las pruebas anteriores


def test_datos_demo_en_base_vacia(tmp_path, monkeypatch):
    import database
    from datos_demo import cargar_datos_demo
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "vacia.db"))
    database.crear_tablas()
    creados = cargar_datos_demo()
    assert creados["estudiantes"] == 16 and creados["matriculas"] > 20
    assert cargar_datos_demo() == {}  # segunda vez no duplica


def test_migracion_agrega_docente_id(tmp_path, monkeypatch):
    """Una matricula.db vieja (sin docente_id) se actualiza sola, sin borrarla."""
    import sqlite3
    import database
    ruta = str(tmp_path / "vieja.db")
    viejo = sqlite3.connect(ruta)
    viejo.execute("CREATE TABLE cursos (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL UNIQUE,"
                  " nombre TEXT NOT NULL, creditos INTEGER NOT NULL, cupo INTEGER NOT NULL)")
    viejo.execute("INSERT INTO cursos (codigo, nombre, creditos, cupo) VALUES ('A1', 'Curso viejo', 3, 10)")
    viejo.commit()
    viejo.close()
    monkeypatch.setattr(database, "DB_NAME", ruta)
    database.crear_tablas()
    with database.obtener_conexion() as conexion:
        columnas = [f["name"] for f in conexion.execute("PRAGMA table_info(cursos)")]
        assert "docente_id" in columnas
        assert conexion.execute("SELECT COUNT(*) AS t FROM cursos").fetchone()["t"] == 1
