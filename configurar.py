"""Asistente de instalación. No guarda contraseñas en texto plano."""
import getpass
import os
from database import crear_tablas, obtener_conexion
from seguridad import crear_usuario_admin_si_no_existe, verificar_contrasena, generar_hash_contrasena, ITERACIONES

def pedir_clave():
    while True:
        clave = getpass.getpass("Nueva contraseña de admin (mínimo 12 caracteres): ")
        if len(clave) >= 12 and clave == getpass.getpass("Repita la contraseña: "):
            return clave
        print("Las claves no coinciden o son demasiado cortas.")

if __name__ == "__main__":
    crear_tablas()
    with obtener_conexion() as conexion:
        admin = conexion.execute("SELECT * FROM usuarios WHERE nombre_usuario='admin'").fetchone()
        hay_usuarios = conexion.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone()
    if not hay_usuarios:
        os.environ["MATRICULA_ADMIN_PASSWORD"] = pedir_clave()
        crear_usuario_admin_si_no_existe()
    elif admin and verificar_contrasena("admin123", admin["contrasena_salt"], admin["contrasena_hash"], admin["iteraciones"]):
        print("La base anterior conserva la clave de demostración. Debe reemplazarla.")
        salt, hash_ = generar_hash_contrasena(pedir_clave())
        with obtener_conexion() as conexion:
            conexion.execute("UPDATE usuarios SET contrasena_hash=?, contrasena_salt=?, iteraciones=?, token=NULL, token_expira=NULL, csrf_hash=NULL WHERE id=?", (hash_, salt, ITERACIONES, admin["id"]))
    else:
        print("Se conservan las cuentas y sus contraseñas existentes.")
    with obtener_conexion() as conexion:
        vacia = conexion.execute("SELECT (SELECT COUNT(*) FROM estudiantes)+(SELECT COUNT(*) FROM cursos)+(SELECT COUNT(*) FROM docentes)").fetchone()[0] == 0
    if vacia and input("¿Cargar datos ficticios para probar en clase? [S/n]: ").strip().lower() != 'n':
        from datos_demo import cargar_datos_demo
        print("Datos de ejemplo:", cargar_datos_demo())
    print("Configuración lista. Puede iniciar el servidor.")
