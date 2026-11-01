"""
routers/paginas.py  -  Páginas HTML (login y dashboard)
"""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from seguridad import obtener_usuario_por_token

plantillas = Jinja2Templates(directory="templates")

router = APIRouter(tags=["Páginas"])


@router.get("/login")
def pagina_login(request: Request):
    return plantillas.TemplateResponse(request, "login.html")


@router.get("/dashboard")
def pagina_dashboard(request: Request):
    token = request.cookies.get("token")
    usuario = obtener_usuario_por_token(token) if token else None
    if usuario is None:
        return RedirectResponse(url="/login")
    return plantillas.TemplateResponse(
        request,
        "dashboard.html",
        {"nombre_usuario": usuario["nombre_usuario"], "rol": usuario["rol"]},
    )
