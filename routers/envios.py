from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
from models.envio import Envio
from models.cliente import Cliente
from models.tracking import EventoTracking
from models.enums import EstadoEnvio
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envios"])


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


# --- 2. LISTADO GENERAL (US-11) ---
@router.get("/")
def listar_envios():
    """US-11: Listado general de envios."""
    return mock_db_envios


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
