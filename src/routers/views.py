from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from src.routers.envios import mock_db_envios, _buscar_envio
from src.models.envio import Envio
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio
import uuid

router = APIRouter(tags=["Vistas"])
templates = Jinja2Templates(directory="templates")


def _render(template: str, request: Request, **kwargs):
    return templates.TemplateResponse(request, template, kwargs)


@router.get("/", response_class=HTMLResponse)
def vista_listado(
    request: Request,
    estado: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    rol: Optional[str] = None,
):
    resultado = list(mock_db_envios)

    if estado:
        resultado = [e for e in resultado if e.historial and e.historial[-1].estado_actual == estado]

    return _render(
        "envios.html", request,
        envios=resultado,
        estado_filtro=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        rol=rol,
    )


@router.get("/envios/nuevo", response_class=HTMLResponse)
def vista_nuevo_envio(request: Request, rol: Optional[str] = None):
    return _render("nuevo_envio.html", request, error=None, rol=rol)


@router.post("/envios/nuevo")
def crear_envio_form(
    request: Request,
    origen: str = Form(...),
    destino: str = Form(...),
    remitente_dni: str = Form(...),
    remitente_nombre: Optional[str] = Form(None),
    destinatario_dni: Optional[str] = Form(None),
    destinatario_nombre: Optional[str] = Form(None),
    consentimiento: Optional[str] = Form(None),
    rol: Optional[str] = Form(None),
):
    destinatario = None
    if destinatario_dni:
        destinatario = Cliente(dni=destinatario_dni, nombre=destinatario_nombre)

    nuevo_envio = Envio(
        trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        origen=origen,
        destino=destino,
        consentimiento=consentimiento == "on",
        remitente=Cliente(dni=remitente_dni, nombre=remitente_nombre),
        destinatario=destinatario,
    )
    nuevo_envio.historial.append(EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=origen,
        observaciones="Envio registrado por el Operador.",
    ))
    mock_db_envios.append(nuevo_envio)
    return RedirectResponse(url=f"/envios/{nuevo_envio.trackingId}?rol={rol or 'operador'}", status_code=303)


@router.get("/envios/{tracking_id}", response_class=HTMLResponse)
def vista_detalle(request: Request, tracking_id: str, rol: Optional[str] = None):
    envio = _buscar_envio(tracking_id)
    return _render("detalle.html", request, envio=envio, rol=rol)


@router.post("/envios/{tracking_id}/estado")
def cambiar_estado_form(
    tracking_id: str,
    nuevo_estado: str = Form(...),
    ubicacion: str = Form(...),
    observaciones: Optional[str] = Form(None),
    rol: str = Form(...),
):
    envio = _buscar_envio(tracking_id)
    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio(nuevo_estado),
        ubicacion=ubicacion,
        observaciones=observaciones,
    ))
    return RedirectResponse(url=f"/envios/{tracking_id}?rol={rol}", status_code=303)
