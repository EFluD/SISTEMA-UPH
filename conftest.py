"""
conftest.py  -  Configuración de pytest.
Las pruebas usan una base de datos TEMPORAL, así nunca tocan tu matricula.db real.
"""
import os
import tempfile
os.environ["MATRICULA_ADMIN_PASSWORD"] = "AdminPruebas2026!"

_carpeta = tempfile.mkdtemp(prefix="matricula_test_")
os.environ["MATRICULA_DB"] = os.path.join(_carpeta, "prueba.db")      # debe ir antes de importar main
os.environ["MATRICULA_RESPALDOS"] = os.path.join(_carpeta, "respaldos")
