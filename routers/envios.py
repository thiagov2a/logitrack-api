from fastapi import APIRouter, HTTPException, Body, Query
from typing import Optional, List
from datetime import date
from models.envio import Envio
from pydantic import BaseModel
from models.cliente import Cliente
from models.tracking import EventoTracking
from models.enums import EstadoEnvio
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envios"])


# Modelo para editar datos del remitente
class RemitenteUpdate(BaseModel):
    dni: Optional[str] = None
    nombre: Optional[str] = None
    anonimizado: Optional[bool] = None


# Modelo para editar datos del envío
class EnvioUpdate(BaseModel):
    origen: Optional[str] = None
    destino: Optional[str] = None
    consentimiento: Optional[bool] = None
    remitente: Optional[RemitenteUpdate] = None


# Modelo para confirmar cancelación
class ConfirmacionCancelacion(BaseModel):
    confirmar: bool


def obtener_estado_actual(envio: Envio):
    """
    Devuelve el estado actual del envío tomando el último evento del historial.
    Si no hay historial, se considera INICIADO por defecto.
    """
    if envio.historial and len(envio.historial) > 0:
        return envio.historial[-1].estado_actual
    return EstadoEnvio.INICIADO


# --- 1. ALTA DE ENVÍO (US-07) ---
class CambioEstadoRequest(BaseModel):
    nuevo_estado: EstadoEnvio
    ubicacion: str
    observaciones: Optional[str] = None


# --- Datos semilla ---
def _crear_envio_semilla(origen, destino, dni, nombre, estado) -> Envio:
    envio = Envio(
        trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        origen=origen,
        destino=destino,
        remitente=Cliente(dni=dni, nombre=nombre),
    )
    envio.historial.append(
        EventoTracking(trackingId=envio.trackingId, estado_actual=EstadoEnvio.INICIADO, ubicacion=origen)
    )
    if estado != EstadoEnvio.INICIADO:
        envio.historial.append(
            EventoTracking(trackingId=envio.trackingId, estado_actual=estado, ubicacion=destino)
        )
    return envio


mock_db_envios = [
    _crear_envio_semilla("Buenos Aires", "Cordoba", "12345678", "Ana Gomez", EstadoEnvio.EN_TRANSITO),
    _crear_envio_semilla("Rosario", "Mendoza", "87654321", "Luis Perez", EstadoEnvio.EN_SUCURSAL),
    _crear_envio_semilla("La Plata", "Tucuman", "11223344", "Maria Lopez", EstadoEnvio.INICIADO),
]

FLUJO_ESTADOS = [
    EstadoEnvio.INICIADO,
    EstadoEnvio.EN_SUCURSAL,
    EstadoEnvio.EN_TRANSITO,
    EstadoEnvio.ENTREGADO,
]


# --- 1. ALTA DE ENVIO (US-07) ---
@router.post("/", status_code=201)
def registrar_envio(nuevo_envio: Envio):
    """US-07: Registro individual de envio con Tracking ID"""
    nuevo_envio.trackingId = f"TRK-{uuid.uuid4().hex[:8].upper()}"
    nuevo_envio.historial.append(EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=nuevo_envio.origen,
        observaciones="Envio registrado en el sistema por el Operador.",
    ))
    mock_db_envios.append(nuevo_envio)
    return {"mensaje": "Envio registrado con exito", "trackingId": nuevo_envio.trackingId, "envio": nuevo_envio}


# --- 2. LISTADO GENERAL, FILTRADO POR ESTADO Y RANGO DE FECHAS (US-11, US-14 y US-15) ---
@router.get("/")
def listar_envios(
    estados: Optional[List[EstadoEnvio]] = Query(None),
    desde: Optional[date] = Query(None, description="Fecha desde en formato YYYY-MM-DD"),
    hasta: Optional[date] = Query(None, description="Fecha hasta en formato YYYY-MM-DD")
):
    """
    US-11: Listado general de envíos.
    Retorna todos los envíos que están en la memoria.

    US-14: Filtrar envíos por estado actual.
    Permite filtrar por uno o varios estados usando query params.

    US-15: Filtrar envíos por rango de fechas.
    Permite traer solo los envíos cuya fecha de creación esté entre 'desde' y 'hasta'.
    """
    # 1. Validar rango de fechas
    if desde and hasta and desde > hasta:
        raise HTTPException(
            status_code=400,
            detail="La fecha 'Desde' no puede ser mayor a la fecha 'Hasta'"
        )

    # 2. Empezamos con todos los envíos
    envios_filtrados = mock_db_envios

    # 3. Filtrar por estado actual si se envía el parámetro
    if estados:
        envios_filtrados = [
            envio for envio in envios_filtrados
            if obtener_estado_actual(envio) in estados
        ]

    # 4. Filtrar por fecha desde
    if desde:
        envios_filtrados = [
            envio for envio in envios_filtrados
            if envio.fechaCreacion.date() >= desde
        ]

    # 5. Filtrar por fecha hasta
    if hasta:
        envios_filtrados = [
            envio for envio in envios_filtrados
            if envio.fechaCreacion.date() <= hasta
        ]

    return envios_filtrados


# --- 3. BUSQUEDA BASICA (US-12) ---
@router.get("/{tracking_id}")
def buscar_resumen_envio(tracking_id: str):
    """US-12: Busqueda de envio por Tracking ID."""
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun envio con el codigo {tracking_id}")
    estado_actual = envio.historial[-1].estado_actual if envio.historial else "DESCONOCIDO"
    return {
        "trackingId": envio.trackingId, "origen": envio.origen,
        "destino": envio.destino, "estado_actual": estado_actual,
    }


# --- 4. DETALLE COMPLETO (US-13) ---
@router.get("/{tracking_id}/detalles")
def buscar_detalle_envio(tracking_id: str):
    """US-13: Visualizacion de detalle completo de envio."""
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun envio con el codigo {tracking_id}")
    return envio


    # Devolvemos el objeto completo tal cual está en la base de datos simulada
    return envio_encontrado


# --- 5. EDICIÓN DE DATOS DE ENVÍO EN ESTADO INICIAL (US-09) ---
@router.patch("/{tracking_id}")
def editar_envio(tracking_id: str, datos_actualizados: EnvioUpdate):
    """
    US-09: Permite editar los datos de un envío solo si el estado actual es INICIADO.
    """
    # 1. Buscar el envío
    envio_encontrado = next(
        (envio for envio in mock_db_envios if envio.trackingId == tracking_id), None
    )

    if not envio_encontrado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún envío con el código {tracking_id}",
        )

    # 2. Obtener el estado actual
    estado_actual = obtener_estado_actual(envio_encontrado)

    # 3. Validar que solo se pueda editar si está INICIADO
    if estado_actual != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede editar un envío en estado INICIADO",
        )

    # 4. Actualizar solo los campos enviados
    if datos_actualizados.origen is not None:
        envio_encontrado.origen = datos_actualizados.origen

    if datos_actualizados.destino is not None:
        envio_encontrado.destino = datos_actualizados.destino

    if datos_actualizados.consentimiento is not None:
        envio_encontrado.consentimiento = datos_actualizados.consentimiento

    if datos_actualizados.remitente is not None:
        if datos_actualizados.remitente.dni is not None:
            envio_encontrado.remitente.dni = datos_actualizados.remitente.dni

        if datos_actualizados.remitente.nombre is not None:
            envio_encontrado.remitente.nombre = datos_actualizados.remitente.nombre

        if datos_actualizados.remitente.anonimizado is not None:
            envio_encontrado.remitente.anonimizado = (
                datos_actualizados.remitente.anonimizado
            )

    return {
        "mensaje": "Envío editado con éxito",
        "envio": envio_encontrado,
    }


# --- 6. CANCELAR ENVÍO INGRESADO (US-10) ---
@router.patch("/{tracking_id}/cancelar")
def cancelar_envio(tracking_id: str, confirmacion: ConfirmacionCancelacion):
    """
    US-10: Permite cancelar un envío solo si está en estado INICIADO.
    Cambia el estado a CANCELADO y lo saca del flujo logístico activo.
    """
    # 1. Buscar el envío
    envio_encontrado = next(
        (envio for envio in mock_db_envios if envio.trackingId == tracking_id), None
    )

    if not envio_encontrado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún envío con el código {tracking_id}",
        )

    # 2. Verificar confirmación
    if not confirmacion.confirmar:
        raise HTTPException(
            status_code=400,
            detail="La cancelación debe ser confirmada explícitamente.",
        )

    # 3. Obtener el estado actual
    estado_actual = obtener_estado_actual(envio_encontrado)

    # 4. Validar que solo se pueda cancelar si está INICIADO
    if estado_actual != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede cancelar un envío en estado INICIADO",
        )

    # 5. Crear el nuevo registro para el historial
    evento_cancelacion = EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio.CANCELADO,
        ubicacion=envio_encontrado.origen,
        observaciones="Envío cancelado por el Operador.",
    )

    # 6. Agregar el nuevo evento
    envio_encontrado.historial.append(evento_cancelacion)

    return {
        "mensaje": "Envío cancelado con éxito",
        "envio": envio_encontrado,
    }


# --- 7. CAMBIO DE ESTADO INDIVIDUAL (US-16,18 y 20) ---
# Definimos el flujo lógico estricto como una lista
FLUJO_ESTADOS = [
    EstadoEnvio.INICIADO,
    EstadoEnvio.EN_SUCURSAL,
    EstadoEnvio.EN_TRANSITO,
    EstadoEnvio.ENTREGADO
]

@router.patch("/{tracking_id}/avanzar_estado")
def avanzar_estado_envio(
    tracking_id: str,
    ubicacion: str = Body(..., embed=True, description="Ubicación donde ocurre el evento"),
    observaciones: Optional[str] = Body(None, embed=True, description="Observaciones opcionales")
):
    """
    US-16,18 y 20: Avanza automáticamente el estado del envío al siguiente en el flujo lógico, guarda la fecha y usuarioque realizo el cambio y permite dejar observaciones
    (Si ya está ENTREGADO, no hace nada)
    """
    # 1. Buscar el envío
    envio_encontrado = next(
        (envio for envio in mock_db_envios if envio.trackingId == tracking_id), None
    )

    if not envio_encontrado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún envío con el código {tracking_id}",
        )

    # 2. Obtener el estado actual (último evento)
    if not envio_encontrado.historial:
        raise HTTPException(
            status_code=500,
            detail="Error interno: El envío no tiene un historial inicial válido."
        )

    estado_actual = envio_encontrado.historial[-1].estado_actual

    # 3. Verificar si el envío fue cancelado
    if estado_actual == EstadoEnvio.CANCELADO:
        raise HTTPException(
            status_code=400,
            detail="Operación no permitida: El envío está CANCELADO y no puede avanzar en el flujo logístico."
        )

    indice_actual = FLUJO_ESTADOS.index(estado_actual)

    # 4. Verificar si ya llegó al estado final (ENTREGADO)
    if indice_actual == len(FLUJO_ESTADOS) - 1:
        raise HTTPException(
            status_code=400,
            detail="Operación no permitida: El envío ya ha sido ENTREGADO y no puede avanzar más."
        )

    # 5. Determinar automáticamente el siguiente estado
    nuevo_estado = FLUJO_ESTADOS[indice_actual + 1]

    # 6. Crear el nuevo registro para el historial
    nuevo_evento = EventoTracking(
        estado_actual=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
        trackingId=tracking_id
    )

    # 7. Agregar el nuevo evento
    envio_encontrado.historial.append(nuevo_evento)

    return {
        "mensaje": f"Estado avanzado exitosamente a '{nuevo_estado.value}'",
        "envio": envio_encontrado
    }
# --- 5. CAMBIO DE ESTADO (US-08) ---
@router.patch("/{tracking_id}/estado")
def cambiar_estado_envio(tracking_id: str, body: CambioEstadoRequest):
    """US-08: Cambio de estado de un envio existente."""
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun envio con el codigo {tracking_id}")
    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=body.nuevo_estado,
        ubicacion=body.ubicacion,
        observaciones=body.observaciones,
    ))
    return {"mensaje": "Estado actualizado con exito", "trackingId": tracking_id,
            "nuevo_estado": body.nuevo_estado}


# --- 6. AVANZAR ESTADO (US-16, 18, 20) ---
@router.patch("/{tracking_id}/avanzar_estado")
def avanzar_estado_envio(
    tracking_id: str,
    ubicacion: str = Body(..., embed=True),
    observaciones: Optional[str] = Body(None, embed=True),
):
    """US-16/18/20: Avanza automaticamente al siguiente estado en el flujo logico."""
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun envio con el codigo {tracking_id}")
    if not envio.historial:
        raise HTTPException(status_code=500, detail="Error interno: el envio no tiene historial inicial.")
    estado_actual = envio.historial[-1].estado_actual
    indice_actual = FLUJO_ESTADOS.index(estado_actual)
    if indice_actual == len(FLUJO_ESTADOS) - 1:
        raise HTTPException(status_code=400, detail="El envio ya fue ENTREGADO y no puede avanzar mas.")
    nuevo_estado = FLUJO_ESTADOS[indice_actual + 1]
    envio.historial.append(EventoTracking(
        trackingId=tracking_id, estado_actual=nuevo_estado,
        ubicacion=ubicacion, observaciones=observaciones,
    ))
    return {"mensaje": f"Estado avanzado a '{nuevo_estado.value}'", "envio": envio}


# --- 7. HISTORIAL DE ESTADOS (US-19) ---
@router.get("/{tracking_id}/historial_estado")
def historial_envio(tracking_id: str):
    """US-19: Historial de estados en detalle."""
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(status_code=404, detail=f"No se encontro ningun envio con el codigo {tracking_id}")
    return envio.historial
