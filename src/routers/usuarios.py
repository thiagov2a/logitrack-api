from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.routers.auth import mock_usuarios, get_usuario_actual

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])
templates = Jinja2Templates(directory="templates")


def _render(template: str, request: Request, **kwargs):
    return templates.TemplateResponse(request, template, kwargs)


# US-04: Listado de usuarios
@router.get("/", response_class=HTMLResponse)
def listar_usuarios(request: Request):
    """US-04: Listado de todos los usuarios activos e inactivos. Solo Administrador."""
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol Administrador.")
    return _render("usuarios.html", request, usuarios=mock_usuarios, usuario=usuario, rol=usuario.rol)


# US-04: Listado via API REST
@router.get("/lista", response_model=None)
def listar_usuarios_api(x_rol: str = Header(...)):
    """US-04: Listado de usuarios via API REST. Solo Administrador."""
    if x_rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol Administrador.")
    return [
        {
            "email": u.email,
            "nombre": u.nombre,
            "rol": u.rol,
            "activo": u.activo,
        }
        for u in mock_usuarios
    ]
