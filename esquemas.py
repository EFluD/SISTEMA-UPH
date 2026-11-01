"""
esquemas.py  -  Modelos Pydantic (qué datos entran y qué datos salen de la API)
"""
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------- Usuarios
class LoginEntrada(BaseModel):
    nombre_usuario: str = Field(min_length=3, max_length=50)
    contrasena: str = Field(min_length=4, max_length=100)


class CambioClave(BaseModel):
    actual: str = Field(min_length=4, max_length=100)
    nueva: str = Field(min_length=12, max_length=100)


class UsuarioCrear(BaseModel):
    nombre_usuario: str = Field(min_length=3, max_length=50)
    contrasena: str = Field(min_length=12, max_length=100)
    rol: Literal["admin", "docente"] = "docente"


class UsuarioRespuesta(BaseModel):
    id: int
    nombre_usuario: str
    rol: str


# ------------------------------------------------------------- Estudiantes
class EstudianteBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    cuenta: str = Field(min_length=3, max_length=30)
    carrera: str = Field(min_length=3, max_length=100)
    correo: EmailStr
    edad: int = Field(ge=15, le=100)


class EstudianteCrear(EstudianteBase):
    pass


class EstudianteRespuesta(EstudianteBase):
    id: int


# --------------------------------------------------------------- Docentes
class DocenteBase(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    correo: EmailStr
    especialidad: str = Field(min_length=3, max_length=100)


class DocenteCrear(DocenteBase):
    pass


class DocenteRespuesta(DocenteBase):
    id: int
    total_cursos: int = 0


# ----------------------------------------------------------------- Cursos
class CursoBase(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    nombre: str = Field(min_length=3, max_length=100)
    creditos: int = Field(ge=1, le=10)
    cupo: int = Field(ge=1, le=500)
    docente_id: Optional[int] = Field(default=None, gt=0)
    periodo: str = Field(default="Sin período", min_length=1, max_length=30)
    horario: str = Field(default="", max_length=100)
    aula: str = Field(default="", max_length=40)


class CursoCrear(CursoBase):
    pass


class CursoRespuesta(CursoBase):
    id: int
    docente_nombre: Optional[str] = None
    matriculados: int = 0


# ------------------------------------------------------------- Matrículas
class MatriculaCrear(BaseModel):
    estudiante_id: int
    curso_id: int


class MatriculaRespuesta(BaseModel):
    id: int
    estudiante_id: int
    estudiante_nombre: str
    curso_id: int
    curso_nombre: str
    curso_codigo: str
    fecha_matricula: str
    estado: str


# ---------------------------------------------------------- Calificaciones
class CalificacionGuardar(BaseModel):
    """Notas de 0 a 100. None = todavía no se ha evaluado ese parcial."""
    parcial1: Optional[float] = Field(default=None, ge=0, le=100)
    parcial2: Optional[float] = Field(default=None, ge=0, le=100)
    parcial3: Optional[float] = Field(default=None, ge=0, le=100)


class CalificacionRespuesta(CalificacionGuardar):
    matricula_id: int
    estudiante_id: int
    estudiante_nombre: str
    curso_id: int
    curso_codigo: str
    curso_nombre: str
    promedio: Optional[float] = None
    situacion: str


# -------------------------------------------------------------- Dashboard
class ResumenDashboard(BaseModel):
    total_estudiantes: int
    total_docentes: int
    total_cursos: int
    total_matriculas_activas: int
    cupos_disponibles: int
    promedio_general: Optional[float] = None
    aprobados: int = 0
    reprobados: int = 0
    en_proceso: int = 0
