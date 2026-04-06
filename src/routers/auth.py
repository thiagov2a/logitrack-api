from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import bcrypt
from src.models.usuario import Usuario

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verificar(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- Usuarios simulados ---
mock_usuarios: list[Usuario] = [
    Usuario(email="operador@logitrack.com", password=_hash("operador123"), nombre="Juan Pérez", rol="operador"),
    Usuario(email="operador2@logitrack.com", password=_hash("operador123"), nombre="Sofía Ramírez", rol="operador"),
    Usuario(email="operador3@logitrack.com", password=_hash("operador123"), nombre="Tomás Aguirre", rol="operador"),
    Usuario(email="supervisor@logitrack.com", password=_hash("supervisor123"), nombre="María López", rol="supervisor"),
    Usuario(email="supervisor2@logitrack.com", password=_hash("supervisor123"), nombre="Nicolás Ibarra", rol="supervisor"),
    Usuario(email="admin@logitrack.com", password=_hash("admin123"), nombre="Carlos García", rol="administrador"),
    Usuario(email="inactivo@logitrack.com", password=_hash("inactivo123"), nombre="Pedro Inactivo", rol="operador", activo=False),
]


def get_usuario_actual(request: Request) -> Optional[Usuario]:
    email = request.cookies.get("usuario_email")
    if not email:
        return None
    return next((u for u in mock_usuarios if u.email == email and u.activo), None)


def _render(template: str, request: Request, **kwargs):
    return templates.TemplateResponse(request, template, kwargs)


# US-01: Login
@router.get("/login", response_class=HTMLResponse)
def vista_login(request: Request):
    if get_usuario_actual(request):
        return RedirectResponse(url="/", status_code=303)
    return _render("login.html", request, error=None)


@router.post("/login")
def procesar_login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    usuario = next((u for u in mock_usuarios if u.email == email and u.activo), None)

    if not usuario or not _verificar(password, usuario.password):
        return _render("login.html", request, error="Usuario o contraseña incorrectos.")

    redirect = RedirectResponse(url="/", status_code=303)
    redirect.set_cookie(key="usuario_email", value=usuario.email, httponly=True)
    return redirect


# US-02: Logout
@router.get("/logout")
def logout():
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("usuario_email")
    return redirect
