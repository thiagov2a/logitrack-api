from fastapi import APIRouter, Header, HTTPException

from src.routers.auth import mock_usuarios

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])


def _solo_admin_api(x_rol: str):
    if x_rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol Administrador.")


# US-04: Listado via API REST
@router.get("/")
def listar_usuarios_api(x_rol: str = Header(...)):
    """US-04: Listado de usuarios via API REST. Solo Administrador."""
    _solo_admin_api(x_rol)
    return [
        {"email": u.email, "nombre": u.nombre, "rol": u.rol, "activo": u.activo}
        for u in mock_usuarios
    ]
