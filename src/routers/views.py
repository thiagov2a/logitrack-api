from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from urllib.parse import urlencode
from src.routers.envios import mock_db_envios, _buscar_envio, _estado_actual
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
    rol: Optional[str] = None,
    error: Optional[str] = None,
    success: Optional[str] = None,
    nuevo_estado: Optional[str] = None,
    ubicacion: Optional[str] = None,
    observaciones: Optional[str] = None,
):
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
        rol=rol,
        error=error,
        success=success,
        nuevo_estado=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
    )


@router.get("/envios/nuevo", response_class=HTMLResponse)
def vista_nuevo_envio(request: Request, rol: Optional[str] = None):
    return _render(
        "nuevo_envio.html",
        request,
        error=None,
        rol=rol,
        form_data={}
    )


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
    if consentimiento != "on":
        return _render(
            "nuevo_envio.html",
            request,
            error="Debe aceptar las politicas de privacidad para registrar el envío",
            rol=rol,
            form_data={
                "origen": origen,
                "destino": destino,
                "remitente_dni": remitente_dni,
                "remitente_nombre": remitente_nombre,
                "destinatario_dni": destinatario_dni,
                "destinatario_nombre": destinatario_nombre,
                "consentimiento": consentimiento,
            }
        )

    destinatario = None
    if destinatario_dni:
        destinatario = Cliente(dni=destinatario_dni, nombre=destinatario_nombre)

    nuevo_envio = Envio(
        trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        origen=origen,
        destino=destino,
        consentimiento=True,
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

    return RedirectResponse(
        url=f"/envios/{nuevo_envio.trackingId}?rol={rol or 'operador'}",
        status_code=303
    )


@router.get("/envios/{tracking_id}", response_class=HTMLResponse)
def vista_detalle(
    request: Request,
    tracking_id: str,
    rol: Optional[str] = None,
    error: Optional[str] = None,
    success: Optional[str] = None,
):
    envio = _buscar_envio(tracking_id)
    estado_actual = _estado_actual(envio)

    return _render(
        "detalle.html",
        request,
        envio=envio,
        rol=rol,
        error=error,
        success=success,
        estado_actual=estado_actual,
    )


# --- Cambio individual de estado desde HTML ---
@router.post("/envios/{tracking_id}/estado")
def cambiar_estado_form(
    tracking_id: str,
    nuevo_estado: str = Form(...),
    ubicacion: str = Form(...),
    observaciones: Optional[str] = Form(None),
    rol: str = Form(...),
):
    if (rol or "").lower() != "supervisor":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: solo el Supervisor puede cambiar estados."
        )

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

    return RedirectResponse(url=f"/envios/{tracking_id}?rol={rol}", status_code=303)


# --- Cambio masivo de estado desde HTML ---
@router.post("/envios/cambio-masivo")
async def cambiar_estado_masivo_form(
    request: Request,
    nuevo_estado: str = Form(...),
    ubicacion: str = Form(...),
    observaciones: Optional[str] = Form(None),
    rol: str = Form(...),
    estado: Optional[str] = Form(None),
    fecha_desde: Optional[str] = Form(None),
    fecha_hasta: Optional[str] = Form(None),
):
    form = await request.form()
    tracking_ids = form.getlist("tracking_ids")

    params = {
        "rol": rol,
        "nuevo_estado": nuevo_estado,
        "ubicacion": ubicacion,
        "observaciones": observaciones or "",
    }

    if estado:
        params["estado"] = estado
    if fecha_desde:
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta

    if (rol or "").lower() != "supervisor":
        params["error"] = "Acceso denegado: solo el Supervisor puede ejecutar cambios masivos."
        return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)

    if not tracking_ids:
        params["error"] = "No se seleccionó ningún checkbox."
        return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)

    try:
        estado_enum = EstadoEnvio(nuevo_estado)
    except ValueError:
        params["error"] = "Estado inválido."
        return RedirectResponse(url=f"/?{urlencode(params)}", status_code=303)

    total_actualizados = 0
    total_omitidos = 0

    for tracking_id in tracking_ids:
        envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)

        if not envio:
            continue

        estado_actual = _estado_actual(envio)

        if estado_actual in ESTADOS_TERMINALES:
            total_omitidos += 1
            continue

        envio.historial.append(EventoTracking(
            trackingId=tracking_id,
            estado_actual=estado_enum,
            ubicacion=ubicacion,
            observaciones=observaciones or "Cambio masivo realizado por Supervisor.",
        ))
        total_actualizados += 1

    params_finales = {"rol": rol}
    if estado:
        params_finales["estado"] = estado
    if fecha_desde:
        params_finales["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params_finales["fecha_hasta"] = fecha_hasta

    if total_actualizados > 0:
        mensaje = f"Se actualizaron {total_actualizados} envío(s) correctamente."
        if total_omitidos > 0:
            mensaje += f" Se omitieron {total_omitidos} envío(s) en estado terminal."
        params_finales["success"] = mensaje
    else:
        params_finales["error"] = "No se realizaron cambios porque los envíos seleccionados están en estado terminal."

    return RedirectResponse(url=f"/?{urlencode(params_finales)}", status_code=303)


# --- US-22: Anonimización desde HTML ---
@router.post("/envios/{tracking_id}/anonimizar")
def anonimizar_envio_form(
    tracking_id: str,
    confirmar: Optional[str] = Form(None),
    rol: str = Form(...),
):
    if (rol or "").lower() != "supervisor":
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=Acceso denegado: solo el Supervisor puede anonimizar.",
            status_code=303
        )

    if confirmar != "on":
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=Debe confirmar la anonimización.",
            status_code=303
        )

    envio = _buscar_envio(tracking_id)
    estado_actual = _estado_actual(envio)

    if estado_actual not in [EstadoEnvio.ENTREGADO, EstadoEnvio.CANCELADO]:
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=Solo se puede anonimizar un envío finalizado.",
            status_code=303
        )

    if envio.remitente:
        envio.remitente.nombre = "***"
        envio.remitente.dni = "***"
        if hasattr(envio.remitente, "direccion"):
            envio.remitente.direccion = "***"
        if hasattr(envio.remitente, "anonimizado"):
            envio.remitente.anonimizado = True

    if getattr(envio, "destinatario", None):
        envio.destinatario.nombre = "***"
        envio.destinatario.dni = "***"
        if hasattr(envio.destinatario, "direccion"):
            envio.destinatario.direccion = "***"
        if hasattr(envio.destinatario, "anonimizado"):
            envio.destinatario.anonimizado = True

    return RedirectResponse(
        url=f"/envios/{tracking_id}?rol={rol}&success=Datos personales anonimizados correctamente.",
        status_code=303
    )


# --- US-23: Exportación CSV desde HTML ---
@router.get("/envios/{tracking_id}/exportar-cliente")
def exportar_cliente_form(
    tracking_id: str,
    tipo_cliente: str = Query(...),
    rol: str = Query(...),
):
    if (rol or "").lower() != "supervisor":
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=Acceso denegado: solo el Supervisor puede exportar datos.",
            status_code=303
        )

    envio = _buscar_envio(tracking_id)

    tipo_normalizado = (tipo_cliente or "").lower()
    if tipo_normalizado not in ["remitente", "destinatario"]:
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=Tipo de cliente inválido.",
            status_code=303
        )

    cliente = envio.remitente if tipo_normalizado == "remitente" else envio.destinatario

    if not cliente:
        return RedirectResponse(
            url=f"/envios/{tracking_id}?rol={rol}&error=El envío no tiene {tipo_normalizado} registrado.",
            status_code=303
        )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "tracking_id",
        "tipo_cliente",
        "nombre",
        "dni",
        "direccion",
        "anonimizado"
    ])

    writer.writerow([
        envio.trackingId,
        tipo_normalizado,
        getattr(cliente, "nombre", "") or "",
        getattr(cliente, "dni", "") or "",
        getattr(cliente, "direccion", "") or "",
        getattr(cliente, "anonimizado", False),
    ])

    output.seek(0)
    filename = f"{tracking_id}_{tipo_normalizado}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )