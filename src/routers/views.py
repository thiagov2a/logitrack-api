from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from urllib.parse import urlencode
from src.routers.envios import mock_db_envios, _buscar_envio, _estado_actual
from src.routers.auth import get_usuario_actual
from src.models.envio import Envio
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio
import uuid
import io
import csv

router = APIRouter(tags=["Vistas"])
templates = Jinja2Templates(directory="templates")

ESTADOS_TERMINALES = [EstadoEnvio.ENTREGADO, EstadoEnvio.CANCELADO]


def _render(template: str, request: Request, **kwargs):
    return templates.TemplateResponse(request, template, kwargs)


@router.get("/", response_class=HTMLResponse)
@router.head("/")
def vista_listado(
    request: Request,
    estado: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    error: Optional[str] = None,
    success: Optional[str] = None,
    nuevo_estado: Optional[str] = None,
    ubicacion: Optional[str] = None,
    observaciones: Optional[str] = None,
):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    from datetime import datetime

    resultado = list(mock_db_envios)

    if estado:
        resultado = [
            e for e in resultado
            if e.historial and str(e.historial[-1].estado_actual).split(".")[-1] == estado
        ]

    if fecha_desde:
        dt_desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
        resultado = [e for e in resultado if e.fechaCreacion >= dt_desde]

    if fecha_hasta:
        dt_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        resultado = [e for e in resultado if e.fechaCreacion <= dt_hasta]

    return _render(
        "envios.html",
        request,
        envios=resultado,
        estado_filtro=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        rol=usuario.rol,
        usuario=usuario,
        error=error,
        success=success,
        nuevo_estado=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
    )


@router.get("/envios/nuevo", response_class=HTMLResponse)
def vista_nuevo_envio(request: Request):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return _render("nuevo_envio.html", request, error=None, rol=usuario.rol, usuario=usuario, datos={})


@router.post("/envios/nuevo")
def crear_envio_form(
    request: Request,
    origen: str = Form(...),
    destino: str = Form(...),
    remitente_dni: str = Form(...),
    remitente_nombre: str = Form(...),
    destinatario_dni: str = Form(...),
    destinatario_nombre: str = Form(...),
    consentimiento: Optional[str] = Form(None),
):
    from pydantic import ValidationError
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)

    datos = {
        "origen": origen,
        "destino": destino,
        "remitente_dni": remitente_dni,
        "remitente_nombre": remitente_nombre,
        "destinatario_dni": destinatario_dni or "",
        "destinatario_nombre": destinatario_nombre or "",
    }

    if not consentimiento:
        return _render("nuevo_envio.html", request,
                       error="Debe aceptar las políticas de privacidad.", rol=usuario.rol, usuario=usuario, datos=datos)

    try:
        destinatario = Cliente(dni=destinatario_dni, nombre=destinatario_nombre)
        nuevo_envio = Envio(
            trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
            origen=origen,
            destino=destino,
            consentimiento=True,
            remitente=Cliente(dni=remitente_dni, nombre=remitente_nombre),
            destinatario=destinatario,
        )
    except ValidationError as e:
        errores = " | ".join([err["msg"].replace("Value error, ", "") for err in e.errors()])
        return _render("nuevo_envio.html", request, error=errores, rol=usuario.rol, usuario=usuario, datos=datos)

    nuevo_envio.historial.append(EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=origen,
        observaciones=f"Envio registrado por {usuario.nombre}.",
    ))
    mock_db_envios.append(nuevo_envio)
    return RedirectResponse(url=f"/envios/{nuevo_envio.trackingId}", status_code=303)


@router.get("/envios/{tracking_id}", response_class=HTMLResponse)
def vista_detalle(request: Request, tracking_id: str):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    envio = _buscar_envio(tracking_id)
    return _render("detalle.html", request, envio=envio, rol=usuario.rol, usuario=usuario)


# --- Cambio individual de estado desde HTML ---
@router.post("/envios/{tracking_id}/estado")
def cambiar_estado_form(
    tracking_id: str,
    request: Request,
    nuevo_estado: str = Form(...),
    ubicacion: str = Form(...),
    observaciones: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Supervisor puede cambiar estados.")

    envio = _buscar_envio(tracking_id)
    estado_actual = _estado_actual(envio)

    if estado_actual in ESTADOS_TERMINALES:
        raise HTTPException(
            status_code=400,
            detail=f"El envio esta en estado terminal ({estado_actual.value}) y no puede cambiar de estado."
        )

    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio(nuevo_estado),
        ubicacion=ubicacion,
        observaciones=observaciones,
    ))
    return RedirectResponse(url=f"/envios/{tracking_id}", status_code=303)


# --- Cambio masivo de estado desde HTML ---
@router.post("/envios/cambio-masivo")
async def cambiar_estado_masivo_form(
    request: Request,
    nuevo_estado: str = Form(...),
    ubicacion: str = Form(...),
    observaciones: Optional[str] = Form(None),
    estado: Optional[str] = Form(None),
    fecha_desde: Optional[str] = Form(None),
    fecha_hasta: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "supervisor":
        return RedirectResponse(url="/?error=Acceso+denegado", status_code=303)

    form = await request.form()
    tracking_ids = form.getlist("tracking_ids")

    if not tracking_ids:
        return RedirectResponse(url="/?error=No+se+selecciono+ningun+envio", status_code=303)

    try:
        estado_enum = EstadoEnvio(nuevo_estado)
    except ValueError:
        return RedirectResponse(url="/?error=Estado+invalido", status_code=303)

    total_actualizados = 0
    total_omitidos = 0

    for tracking_id in tracking_ids:
        envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
        if not envio:
            continue
        if _estado_actual(envio) in ESTADOS_TERMINALES:
            total_omitidos += 1
            continue
        envio.historial.append(EventoTracking(
            trackingId=tracking_id,
            estado_actual=estado_enum,
            ubicacion=ubicacion,
            observaciones=observaciones or f"Cambio masivo realizado por {usuario.nombre}.",
        ))
        total_actualizados += 1

    params_finales = {}
    if estado:
        params_finales["estado"] = estado
    if fecha_desde:
        params_finales["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params_finales["fecha_hasta"] = fecha_hasta

    if total_actualizados > 0:
        mensaje = f"Se actualizaron {total_actualizados} envio(s) correctamente."
        if total_omitidos > 0:
            mensaje += f" Se omitieron {total_omitidos} envio(s) en estado terminal."
        params_finales["success"] = mensaje
    else:
        params_finales["error"] = "No se realizaron cambios porque los envios seleccionados estan en estado terminal."

    return RedirectResponse(url=f"/?{urlencode(params_finales)}", status_code=303)


# --- US-22: Anonimización desde HTML ---
@router.post("/envios/{tracking_id}/anonimizar")
def anonimizar_envio_form(
    tracking_id: str,
    request: Request,
    confirmar: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Supervisor puede anonimizar.")

    if confirmar != "on":
        return RedirectResponse(url=f"/envios/{tracking_id}?error=Debe+confirmar+la+anonimizacion", status_code=303)

    envio = _buscar_envio(tracking_id)
    estado_actual = _estado_actual(envio)

    if estado_actual not in ESTADOS_TERMINALES:
        return RedirectResponse(
            url=f"/envios/{tracking_id}?error=Solo+se+puede+anonimizar+un+envio+finalizado", status_code=303
        )

    if envio.remitente:
        envio.remitente.nombre = "***"
        envio.remitente.dni = "***"
        envio.remitente.anonimizado = True

    if envio.destinatario:
        envio.destinatario.nombre = "***"
        envio.destinatario.dni = "***"
        envio.destinatario.anonimizado = True

    return RedirectResponse(url=f"/envios/{tracking_id}?success=Datos+anonimizados+correctamente", status_code=303)


# --- US-23: Exportación CSV desde HTML ---
@router.get("/envios/{tracking_id}/exportar-cliente")
def exportar_cliente_form(
    tracking_id: str,
    request: Request,
    tipo_cliente: str = Query(...),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "supervisor":
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Supervisor puede exportar datos.")

    envio = _buscar_envio(tracking_id)

    tipo_normalizado = (tipo_cliente or "").lower()
    if tipo_normalizado not in ["remitente", "destinatario"]:
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido.")

    cliente = envio.remitente if tipo_normalizado == "remitente" else envio.destinatario

    if not cliente:
        raise HTTPException(status_code=404, detail=f"El envío no tiene {tipo_normalizado} registrado.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["tracking_id", "tipo_cliente", "nombre", "dni", "anonimizado"])
    writer.writerow([
        envio.trackingId,
        tipo_normalizado,
        getattr(cliente, "nombre", "") or "",
        getattr(cliente, "dni", "") or "",
        getattr(cliente, "anonimizado", False),
    ])

    output.seek(0)
    filename = f"{tracking_id}_{tipo_normalizado}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
