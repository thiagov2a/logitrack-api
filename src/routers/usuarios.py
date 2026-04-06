from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.routers.auth import mock_usuarios

router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

ROLES_VALIDOS = ["operador", "supervisor", "administrador"]


def _solo_admin_api(x_rol: str):
    if x_rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol Administrador.")


def _buscar_usuario(email: str):
    usuario = next((u for u in mock_usuarios if u.email == email), None)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun usuario con el email {email}.")
    return usuario


# US-04: Listado via API REST
@router.get("/")
def listar_usuarios_api(x_rol: str = Header(...)):
    """US-04: Listado de usuarios via API REST. Solo Administrador."""
    _solo_admin_api(x_rol)
    return [
        {"email": u.email, "nombre": u.nombre, "rol": u.rol, "activo": u.activo}
        for u in mock_usuarios
    ]


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    rol: Optional[str] = None


# US-05: Editar datos y rol de usuario
@router.patch("/{email}")
def editar_usuario_api(email: str, datos: UsuarioUpdate, x_rol: str = Header(...)):
    """US-05: Edita nombre y/o rol de un usuario. Solo Administrador."""
    _solo_admin_api(x_rol)
    usuario = _buscar_usuario(email)

    if datos.nombre is not None:
        if len(datos.nombre.strip()) < 2:
            raise HTTPException(status_code=400, detail="El nombre debe tener al menos 2 caracteres.")
        usuario.nombre = datos.nombre.strip()

    if datos.rol is not None:
        if datos.rol.lower() not in ROLES_VALIDOS:
            raise HTTPException(status_code=400, detail=f"Rol invalido. Debe ser uno de: {ROLES_VALIDOS}.")
        usuario.rol = datos.rol.lower()

    return {"mensaje": "Usuario actualizado con exito", "usuario": {
        "email": usuario.email, "nombre": usuario.nombre, "rol": usuario.rol, "activo": usuario.activo
    }}


# US-06: Baja logica de usuario
@router.patch("/{email}/desactivar")
def desactivar_usuario_api(email: str, x_rol: str = Header(...)):
    """US-06: Desactiva un usuario (activo=false). No lo elimina. Solo Administrador."""
    _solo_admin_api(x_rol)
    usuario = _buscar_usuario(email)
    if not usuario.activo:
        raise HTTPException(status_code=400, detail="El usuario ya se encuentra inactivo.")
    usuario.activo = False
    return {"mensaje": "Usuario desactivado con exito", "email": email, "activo": False}


# US-06: Reactivar usuario
@router.patch("/{email}/activar")
def activar_usuario_api(email: str, x_rol: str = Header(...)):
    """US-06: Reactiva un usuario inactivo. Solo Administrador."""
    _solo_admin_api(x_rol)
    usuario = _buscar_usuario(email)
    if usuario.activo:
        raise HTTPException(status_code=400, detail="El usuario ya se encuentra activo.")
    usuario.activo = True
    return {"mensaje": "Usuario activado con exito", "email": email, "activo": True}
