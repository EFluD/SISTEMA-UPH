from concurrent.futures import ThreadPoolExecutor
import hashlib
import pytest
from fastapi.testclient import TestClient
import database
from main import app
from seguridad import generar_hash_contrasena


@pytest.fixture()
def admin(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_NAME', str(tmp_path/'campus.db'))
    monkeypatch.setattr(database, 'CARPETA_RESPALDOS', str(tmp_path/'respaldos'))
    monkeypatch.setenv('MATRICULA_ADMIN_PASSWORD', 'AdminPruebas2026!')
    with TestClient(app) as cliente:
        r=cliente.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'AdminPruebas2026!'})
        assert r.status_code==200
        cliente.headers['Authorization']='Bearer '+r.json()['token']
        yield cliente


def crear_curso_y_alumno(c):
    d=c.post('/docentes',json={'nombre':'Docente Demo','correo':'docente@example.edu','especialidad':'Programación'}).json()
    cu=c.post('/cursos',json={'codigo':'IS-2026-3','nombre':'Programación III','creditos':4,'cupo':1,'docente_id':d['id'],'periodo':'2026-3','horario':'LU-MI 07:00–09:00','aula':'LAB-01'}).json()
    e=c.post('/estudiantes',json={'nombre':'Alumno Ejemplo','cuenta':'2026001','carrera':'Sistemas','correo':'alumno@example.edu','edad':20}).json()
    return d,cu,e


def test_docente_no_puede_escalar_privilegios(admin):
    assert admin.post('/auth/usuarios',json={'nombre_usuario':'docente','contrasena':'DocentePruebas2026!','rol':'docente'}).status_code==201
    with TestClient(app) as docente:
        r=docente.post('/auth/login',json={'nombre_usuario':'docente','contrasena':'DocentePruebas2026!'})
        docente.headers['Authorization']='Bearer '+r.json()['token']
        assert docente.get('/estudiantes').status_code==200
        assert docente.get('/academico/resumen').status_code==200
        for ruta in ('/auth/usuarios','/datos/respaldos','/auth/auditoria'):
            assert docente.get(ruta).status_code==403
        assert docente.post('/auth/usuarios',json={'nombre_usuario':'escalada','contrasena':'OtraClave2026!','rol':'admin'}).status_code==403
        assert docente.post('/datos/respaldos').status_code==403
        assert docente.delete('/estudiantes/1').status_code==403


def test_cookie_csrf_y_origen(admin):
    admin.headers.pop('Authorization')
    assert admin.post('/datos/demo').status_code==403
    admin.headers['X-CSRF-Token']=admin.cookies.get('csrf')
    assert admin.post('/datos/demo').status_code==201
    assert admin.post('/auth/logout',headers={'Origin':'https://otro.example'}).status_code==403
    assert admin.post('/auth/logout').status_code==200
    assert admin.get('/estudiantes').status_code==401


def test_token_hash_vencimiento_y_logout(admin):
    token=admin.headers['Authorization'].split()[1]
    with database.obtener_conexion() as conexion:
        u=conexion.execute('SELECT * FROM usuarios').fetchone()
        assert u['token'] != token
        assert u['token']==hashlib.sha256(token.encode()).hexdigest()
        assert u['iteraciones']==600000
        conexion.execute("UPDATE usuarios SET token_expira='2000-01-01T00:00:00'")
    assert admin.get('/estudiantes').status_code==401
    r=admin.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'AdminPruebas2026!'})
    admin.headers['Authorization']='Bearer '+r.json()['token']
    assert admin.post('/auth/logout').status_code==200
    assert admin.get('/estudiantes').status_code==401


def test_limite_de_intentos(admin):
    for _ in range(5):
        assert admin.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'incorrecta'}).status_code==401
    assert admin.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'AdminPruebas2026!'}).status_code==429


def test_cambio_clave_revoca_sesion(admin):
    assert admin.post('/auth/cambiar-clave',json={'actual':'incorrecta','nueva':'NuevaClaveSegura2026!'}).status_code==400
    assert admin.post('/auth/cambiar-clave',json={'actual':'AdminPruebas2026!','nueva':'NuevaClaveSegura2026!'}).status_code==200
    assert admin.get('/estudiantes').status_code==401
    assert admin.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'AdminPruebas2026!'}).status_code==401
    assert admin.post('/auth/login',json={'nombre_usuario':'admin','contrasena':'NuevaClaveSegura2026!'}).status_code==200


def test_expediente_carga_y_retiro(admin):
    d,c,e=crear_curso_y_alumno(admin)
    m=admin.post('/matriculas',json={'estudiante_id':e['id'],'curso_id':c['id']}).json()
    assert admin.put(f"/calificaciones/matricula/{m['id']}",json={'parcial1':80,'parcial2':85,'parcial3':90}).status_code==200
    r=admin.get(f"/academico/estudiantes/{e['id']}?periodo=2026-3").json()
    assert r['resumen']['clases_inscritas']==1
    assert r['resumen']['creditos_aprobados']==4
    assert r['hoja'][0]['docente']=='Docente Demo'
    assert r['historial'][0]['promedio']==85
    assert admin.get(f"/academico/docentes/{d['id']}?periodo=2026-3").json()['total_cursos']==1
    assert len(admin.get(f"/academico/cursos/{c['id']}").json()['estudiantes'])==1
    assert admin.get('/academico/resumen?periodo=2026-1').json()['totales']['matriculas']==0
    assert admin.delete(f"/matriculas/{m['id']}").status_code==200
    r=admin.get(f"/academico/estudiantes/{e['id']}?periodo=2026-3").json()
    assert r['resumen']['clases_inscritas']==0
    assert len(r['historial'])==1
    assert r['historial'][0]['estado']=='retirada'
    assert admin.get('/academico/estudiantes/999').status_code==404
    assert admin.get('/academico/docentes/999').status_code==404
    assert admin.get('/academico/cursos/999').status_code==404


def test_cupo_concurrente_y_periodo_protegido(admin):
    d,c,e=crear_curso_y_alumno(admin)
    e2=admin.post('/estudiantes',json={'nombre':'Segundo Alumno','cuenta':'2026002','carrera':'Sistemas','correo':'segundo@example.edu','edad':21}).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        codigos=list(pool.map(lambda eid:admin.post('/matriculas',json={'estudiante_id':eid,'curso_id':c['id']}).status_code,[e['id'],e2['id']]))
    assert sorted(codigos)==[201,409]
    assert admin.put(f"/cursos/{c['id']}",json={**c,'periodo':'2027-1'}).status_code==409
    assert admin.get('/academico/resumen?periodo=2026-3').json()['ocupados']==1


def test_auditoria_y_csv_seguro(admin):
    r=admin.post('/docentes',json={'nombre':'=SUM(1)','correo':'formula@example.edu','especialidad':'Programación'})
    assert r.status_code==201
    csv=admin.get('/datos/exportar/docentes').content.decode('utf-8-sig')
    assert "'=SUM(1)" in csv
    assert admin.get('/auth/auditoria').json()[0]['ruta']=='/docentes'
    r=admin.post('/datos/importar/docentes',json={'contenido':'nombre,correo,especialidad\nUno Dos,uno@example.edu,Sistemas,extra'})
    assert r.status_code==200 and r.json()['omitidos']==1


def test_migracion_hash_legacy_y_rol_validado(admin):
    salt, hash_=generar_hash_contrasena('ClaveLegacy2026!',iteraciones=100000)
    with database.obtener_conexion() as conexion:
        conexion.execute("INSERT INTO usuarios (nombre_usuario, contrasena_salt, contrasena_hash, rol, iteraciones) VALUES ('legacy', ?, ?, 'docente', 100000)",(salt,hash_))
    assert admin.post('/auth/login',json={'nombre_usuario':'legacy','contrasena':'ClaveLegacy2026!'}).status_code==200
    with database.obtener_conexion() as conexion:
        assert conexion.execute("SELECT iteraciones FROM usuarios WHERE nombre_usuario='legacy'").fetchone()[0]==600000
    assert admin.post('/auth/usuarios',json={'nombre_usuario':'invalido','contrasena':'ClaveSegura2026!','rol':'superpoder'}).status_code==422


def test_demo_periodos_y_headers(admin):
    assert admin.post('/datos/demo').status_code==201
    assert admin.get('/academico/periodos').json()==['2026-3','2026-1']
    r=admin.get('/academico/resumen?periodo=2026-1')
    assert r.json()['totales']['matriculas']==4
    recientes=admin.get('/academico/resumen').json()['matriculas']
    fechas=[m['fecha_matricula'] for m in recientes]
    assert fechas==sorted(fechas,reverse=True)
    assert r.headers['X-Frame-Options']=='DENY'
    assert "script-src 'self'" in r.headers['Content-Security-Policy']
