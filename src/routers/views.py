from fastapi import APIRouter, Request, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from urllib.parse import urlencode
from src.routers.envios import mock_db_envios, _buscar_envio, _estado_actual, importar_envios_csv
from src.routers.auth import get_usuario_actual, mock_usuarios
from src.models.envio import Envio
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio, PrioridadEnvio  # noqa: F811
from src.models.usuario import Usuario
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
    busqueda: Optional[str] = None,
    orden_prioridad: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    from datetime import datetime

    resultado = list(mock_db_envios)

    if busqueda:
        q = busqueda.strip().upper()
        resultado = [e for e in resultado if e.trackingId and q in e.trackingId.upper()]

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

    ORDEN = {"ALTA": 3, "MEDIA": 2, "BAJA": 1, None: 0}
    if not orden_prioridad and usuario.rol in ["supervisor", "administrador"]:
        orden_prioridad = "desc"
    if orden_prioridad == "asc":
        resultado = sorted(resultado, key=lambda e: ORDEN.get(
            str(e.prioridad_ml).split(".")[-1] if e.prioridad_ml else None, 0
        ))
    elif orden_prioridad == "desc":
        resultado = sorted(resultado, key=lambda e: ORDEN.get(
            str(e.prioridad_ml).split(".")[-1] if e.prioridad_ml else None, 0
        ), reverse=True)

    total = len(resultado)
    total_pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * limit
    resultado_paginado = resultado[offset:offset + limit]

    filtros_activos = any([busqueda, estado, fecha_desde, fecha_hasta])
    aviso_sin_resultados = None
    if filtros_activos and total == 0:
        partes = []
        if busqueda:
            partes.append(f"Tracking ID contiene '{busqueda}'")
        if estado:
            partes.append(f"estado '{estado}'")
        if fecha_desde:
            partes.append(f"desde {fecha_desde}")
        if fecha_hasta:
            partes.append(f"hasta {fecha_hasta}")
        aviso_sin_resultados = "No se encontraron envíos con los filtros: " + ", ".join(partes) + "."

    return _render(
        "envios.html",
        request,
        envios=resultado_paginado,
        estado_filtro=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        busqueda=busqueda or "",
        rol=usuario.rol,
        usuario=usuario,
        error=error,
        success=success,
        aviso_sin_resultados=aviso_sin_resultados,
        orden_prioridad=orden_prioridad or "",
        nuevo_estado=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
        page=page,
        total_pages=total_pages,
        total=total,
        limit=limit,
    )


@router.get("/envios/nuevo", response_class=HTMLResponse)
def vista_nuevo_envio(request: Request, error: Optional[str] = None, success: Optional[str] = None):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    return _render(
        "nuevo_envio.html", request,
        error=error, success=success, rol=usuario.rol, usuario=usuario, datos={}
    )


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
    peso_kg: Optional[float] = Form(None),
    largo_cm: Optional[float] = Form(None),
    ancho_cm: Optional[float] = Form(None),
    alto_cm: Optional[float] = Form(None),
):
    from pydantic import ValidationError
    from src.ml.predictor import predecir_prioridad
    from src.models.enums import PrioridadEnvio
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
        "peso_kg": peso_kg or "",
        "largo_cm": largo_cm or "",
        "ancho_cm": ancho_cm or "",
        "alto_cm": alto_cm or "",
    }

    if not consentimiento:
        return _render("nuevo_envio.html", request,
                       error="Debe aceptar las políticas de privacidad.", rol=usuario.rol, usuario=usuario, datos=datos)

    try:
        dims = None
        if largo_cm and ancho_cm and alto_cm:
            from src.models.envio import Dimensiones
            dims = Dimensiones(largo_cm=largo_cm, ancho_cm=ancho_cm, alto_cm=alto_cm)
        destinatario = Cliente(dni=destinatario_dni, nombre=destinatario_nombre)
        nuevo_envio = Envio(
            trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
            origen=origen,
            destino=destino,
            consentimiento=True,
            peso_kg=peso_kg,
            dimensiones=dims,
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

    dims = nuevo_envio.dimensiones
    pred = predecir_prioridad(
        peso_kg=nuevo_envio.peso_kg,
        largo_cm=dims.largo_cm if dims else None,
        ancho_cm=dims.ancho_cm if dims else None,
        alto_cm=dims.alto_cm if dims else None,
    )
    nuevo_envio.prioridad_ml = PrioridadEnvio(pred)

    mock_db_envios.append(nuevo_envio)
    return RedirectResponse(url=f"/envios/{nuevo_envio.trackingId}", status_code=303)


@router.get("/envios/{tracking_id}", response_class=HTMLResponse)
def vista_detalle(request: Request, tracking_id: str):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    envio = _buscar_envio(tracking_id)
    return _render("detalle.html", request, envio=envio, rol=usuario.rol, usuario=usuario)


# --- Importar CSV desde HTML ---
@router.post("/envios/importar-csv")
async def importar_csv_form(request: Request, archivo: UploadFile = File(...)):
    usuario = get_usuario_actual(request)
    if not usuario:
        return RedirectResponse(url="/login", status_code=303)
    try:
        resultado = await importar_envios_csv(archivo)
        total = resultado["mensaje"]
        return RedirectResponse(url=f"/envios/nuevo?success={total}", status_code=303)
    except HTTPException as e:
        return RedirectResponse(url=f"/envios/nuevo?error={e.detail}", status_code=303)


# --- Cambio de prioridad manual desde HTML ---
@router.post("/envios/{tracking_id}/prioridad")
def cambiar_prioridad_form(
    tracking_id: str,
    request: Request,
    nueva_prioridad: str = Form(...),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol not in ["supervisor", "administrador"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Supervisor puede cambiar la prioridad.")
    envio = _buscar_envio(tracking_id)
    if _estado_actual(envio) in ESTADOS_TERMINALES:
        return RedirectResponse(
            url=f"/envios/{tracking_id}?error=No+se+puede+cambiar+la+prioridad+de+un+envio+finalizado",
            status_code=303
        )
    envio.prioridad_ml = PrioridadEnvio(nueva_prioridad)
    envio.prioridadManual = True
    return RedirectResponse(url=f"/envios/{tracking_id}?success=Prioridad+actualizada+correctamente", status_code=303)


# --- US-09: Editar envío desde HTML (solo Operador, solo en estado INICIADO) ---
@router.post("/envios/{tracking_id}/editar")
def editar_envio_form(
    request: Request,
    tracking_id: str,
    origen: str = Form(...),
    destino: str = Form(...),
    remitente_dni: str = Form(...),
    remitente_nombre: Optional[str] = Form(None),
    destinatario_dni: Optional[str] = Form(None),
    destinatario_nombre: Optional[str] = Form(None),
    consentimiento: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol not in ["operador", "supervisor", "administrador"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Operador puede editar el envío.")

    envio = _buscar_envio(tracking_id)

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(status_code=400, detail="Solo se puede editar un envío en estado INICIADO.")

    envio.origen = origen
    envio.destino = destino
    envio.consentimiento = consentimiento == "on"

    if envio.remitente:
        envio.remitente.dni = remitente_dni
        envio.remitente.nombre = remitente_nombre
    else:
        envio.remitente = Cliente(dni=remitente_dni, nombre=remitente_nombre)

    if destinatario_dni or destinatario_nombre:
        if envio.destinatario:
            envio.destinatario.dni = destinatario_dni
            envio.destinatario.nombre = destinatario_nombre
        else:
            envio.destinatario = Cliente(dni=destinatario_dni, nombre=destinatario_nombre)

    return RedirectResponse(url=f"/envios/{tracking_id}", status_code=303)


# --- US-10: Cancelar envío desde HTML (solo Operador, solo en estado INICIADO) ---
@router.post("/envios/{tracking_id}/cancelar")
def cancelar_envio_form(
    request: Request,
    tracking_id: str,
    confirmar: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol not in ["operador", "supervisor", "administrador"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Operador puede cancelar el envío.")

    if confirmar != "on":
        raise HTTPException(status_code=400, detail="Debe confirmar la cancelación del envío.")

    envio = _buscar_envio(tracking_id)

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(status_code=400, detail="Solo se puede cancelar un envío en estado INICIADO.")

    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio.CANCELADO,
        ubicacion=envio.origen,
        observaciones="Envio cancelado por el Operador.",
    ))
    return RedirectResponse(url=f"/envios/{tracking_id}", status_code=303)


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
    if not usuario or usuario.rol not in ["supervisor", "administrador"]:
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
        usuario=usuario.email,
    ))
    return RedirectResponse(url=f"/envios/{tracking_id}", status_code=303)


# --- Cambio masivo de estado desde HTML ---
@router.post("/envios/cambio-masivo/confirmar")
async def confirmar_cambio_masivo_form(request: Request):
    """Recibe los tracking_ids seleccionados y muestra la página de confirmación."""
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol not in ["supervisor", "administrador"]:
        return RedirectResponse(url="/?error=Acceso+denegado", status_code=303)
    form = await request.form()
    tracking_ids = form.getlist("tracking_ids")
    if not tracking_ids:
        return RedirectResponse(url="/?error=No+se+selecciono+ningun+envio", status_code=303)
    envios_sel = [e for e in mock_db_envios if e.trackingId in tracking_ids]
    return _render(
        "cambio_masivo.html", request,
        envios=envios_sel,
        tracking_ids=tracking_ids,
        rol=usuario.rol,
        usuario=usuario,
    )


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
    if not usuario or usuario.rol not in ["supervisor", "administrador"]:
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
            usuario=usuario.email,
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


# --- US-22: Anonimización desde HTML (Supervisor) ---
@router.post("/envios/{tracking_id}/anonimizar")
def anonimizar_envio_form(
    tracking_id: str,
    request: Request,
    confirmar: Optional[str] = Form(None),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol not in ["supervisor", "administrador"]:
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Supervisor puede anonimizar.")

    if confirmar != "on":
        return RedirectResponse(url=f"/envios/{tracking_id}?error=Debe+confirmar+la+anonimizacion", status_code=303)

    envio = _buscar_envio(tracking_id)

    if _estado_actual(envio) not in ESTADOS_TERMINALES:
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


# --- US-23: Exportación CSV desde HTML (Administrador) ---
@router.get("/envios/{tracking_id}/exportar-cliente")
def exportar_cliente_form(
    tracking_id: str,
    request: Request,
    tipo_cliente: str = Query(...),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado: solo el Administrador puede exportar datos.")

    envio = _buscar_envio(tracking_id)

    tipo_normalizado = (tipo_cliente or "").lower()
    if tipo_normalizado not in ["remitente", "destinatario"]:
        raise HTTPException(status_code=400, detail="Tipo de cliente inválido.")

    cliente = envio.remitente if tipo_normalizado == "remitente" else envio.destinatario

    if not cliente:
        raise HTTPException(status_code=404, detail=f"El envío no tiene {tipo_normalizado} registrado.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["tracking_id", "tipo_cliente", "nombre", "dni", "direccion", "anonimizado"])
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


# --- US-04: Listado de usuarios (vista HTML) ---
@router.get("/usuarios/", response_class=HTMLResponse)
def vista_usuarios(
    request: Request,
    rol_filtro: Optional[str] = None,
    estado_filtro: Optional[str] = None,
    busqueda: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    success = request.query_params.get("success")
    error = request.query_params.get("error")

    resultado = list(mock_usuarios)

    if rol_filtro:
        resultado = [u for u in resultado if u.rol == rol_filtro]
    if estado_filtro == "activo":
        resultado = [u for u in resultado if u.activo]
    elif estado_filtro == "inactivo":
        resultado = [u for u in resultado if not u.activo]
    if busqueda:
        q = busqueda.lower()
        resultado = [u for u in resultado if q in u.nombre.lower() or q in u.email.lower()]

    total = len(resultado)
    total_pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * limit

    return _render(
        "usuarios.html", request,
        usuarios=resultado[offset:offset + limit],
        usuario=usuario,
        rol=usuario.rol,
        success=success,
        error=error,
        rol_filtro=rol_filtro,
        estado_filtro=estado_filtro,
        busqueda=busqueda or "",
        page=page,
        total_pages=total_pages,
        total=total,
        limit=limit,
    )


# --- US-03: Alta de usuario (vista HTML) ---
@router.get("/usuarios/nuevo", response_class=HTMLResponse)
def vista_nuevo_usuario(request: Request):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    return _render("nuevo_usuario.html", request, error=None, usuario=usuario, rol=usuario.rol, datos={})


@router.post("/usuarios/nuevo")
def crear_usuario_form(
    request: Request,
    nombre: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    rol_nuevo: str = Form(...),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)

    datos = {"nombre": nombre, "email": email, "rol": rol_nuevo}

    if next((u for u in mock_usuarios if u.email == email), None):
        return _render("nuevo_usuario.html", request,
                       error="Ya existe un usuario con ese email.",
                       usuario=usuario, rol=usuario.rol, datos=datos)

    mock_usuarios.append(Usuario(email=email, password=password, nombre=nombre, rol=rol_nuevo, activo=True))
    return RedirectResponse(url="/usuarios/", status_code=303)


# --- US-05: Editar usuario (vista HTML) ---
@router.get("/usuarios/{email}/editar", response_class=HTMLResponse)
def vista_editar_usuario(request: Request, email: str):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    target = next((u for u in mock_usuarios if u.email == email), None)
    if not target:
        return RedirectResponse(url="/usuarios/", status_code=303)
    return _render("editar_usuario.html", request, target=target, error=None, usuario=usuario, rol=usuario.rol)


@router.post("/usuarios/{email}/editar")
def editar_usuario_form(
    request: Request,
    email: str,
    nombre: str = Form(...),
    rol_nuevo: str = Form(...),
):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    target = next((u for u in mock_usuarios if u.email == email), None)
    if not target:
        return RedirectResponse(url="/usuarios/", status_code=303)
    roles_validos = ["operador", "supervisor", "administrador"]
    if len(nombre.strip()) < 2:
        return _render("editar_usuario.html", request, target=target,
                       error="El nombre debe tener al menos 2 caracteres.", usuario=usuario, rol=usuario.rol)
    if rol_nuevo.lower() not in roles_validos:
        return _render("editar_usuario.html", request, target=target,
                       error="Rol inválido.", usuario=usuario, rol=usuario.rol)
    target.nombre = nombre.strip()
    target.rol = rol_nuevo.lower()
    return RedirectResponse(url="/usuarios/?success=Usuario+actualizado+correctamente", status_code=303)


# --- US-06: Desactivar usuario (vista HTML) ---
@router.post("/usuarios/{email}/desactivar")
def desactivar_usuario_form(request: Request, email: str):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    if email == usuario.email:
        return RedirectResponse(url="/usuarios/?error=No+puedes+desactivar+tu+propio+usuario", status_code=303)
    target = next((u for u in mock_usuarios if u.email == email), None)
    if not target or not target.activo:
        return RedirectResponse(url="/usuarios/?error=Usuario+no+encontrado+o+ya+inactivo", status_code=303)
    target.activo = False
    return RedirectResponse(url="/usuarios/?success=Usuario+desactivado+correctamente", status_code=303)


# --- US-06: Activar usuario (vista HTML) ---
@router.post("/usuarios/{email}/activar")
def activar_usuario_form(request: Request, email: str):
    usuario = get_usuario_actual(request)
    if not usuario or usuario.rol != "administrador":
        return RedirectResponse(url="/", status_code=303)
    target = next((u for u in mock_usuarios if u.email == email), None)
    if not target or target.activo:
        return RedirectResponse(url="/usuarios/?error=Usuario+no+encontrado+o+ya+activo", status_code=303)
    target.activo = True
    return RedirectResponse(url="/usuarios/?success=Usuario+activado+correctamente", status_code=303)
