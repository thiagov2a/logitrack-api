from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models.envio import Envio, Dimensiones
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio, PrioridadEnvio
from src.ml.predictor import predecir_prioridad
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envios"])


# --- Modelos de request ---

class CambioEstadoRequest(BaseModel):
    nuevo_estado: EstadoEnvio
    ubicacion: str
    observaciones: Optional[str] = None


class RemitenteUpdate(BaseModel):
    dni: Optional[str] = None
    nombre: Optional[str] = None
    anonimizado: Optional[bool] = None


class EnvioUpdate(BaseModel):
    origen: Optional[str] = None
    destino: Optional[str] = None
    consentimiento: Optional[bool] = None
    remitente: Optional[RemitenteUpdate] = None


class ConfirmacionCancelacion(BaseModel):
    confirmar: bool


# --- Helpers ---

FLUJO_ESTADOS = [
    EstadoEnvio.INICIADO,
    EstadoEnvio.EN_SUCURSAL,
    EstadoEnvio.EN_TRANSITO,
    EstadoEnvio.ENTREGADO,
]


def _estado_actual(envio: Envio) -> EstadoEnvio:
    if envio.historial:
        return envio.historial[-1].estado_actual
    return EstadoEnvio.INICIADO


def _buscar_envio(tracking_id: str) -> Envio:
    envio = next(
        (e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontro ningun envio con el codigo {tracking_id}",
        )
    return envio


# --- Datos semilla ---

def _crear_semilla(
    origen: str,
    destino: str,
    dni: str,
    nombre: str,
    estado: EstadoEnvio,
    peso: float = None,
    largo: float = None,
    ancho: float = None,
    alto: float = None
) -> Envio:

    dims = None
    if largo is not None and ancho is not None and alto is not None:
        dims = Dimensiones(largo_cm=largo, ancho_cm=ancho, alto_cm=alto)

    envio = Envio(
        trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        origen=origen,
        destino=destino,
        peso_kg=peso,
        dimensiones=dims,
        remitente=Cliente(dni=dni, nombre=nombre),
    )

    envio.historial.append(
        EventoTracking(trackingId=envio.trackingId,
                       estado_actual=EstadoEnvio.INICIADO, ubicacion=origen)
    )

    if estado != EstadoEnvio.INICIADO:
        envio.historial.append(
            EventoTracking(trackingId=envio.trackingId,
                           estado_actual=estado, ubicacion=destino)
        )

    return envio


mock_db_envios = [
    _crear_semilla("Buenos Aires", "Cordoba", "12345678",
                   "Ana Gomez", EstadoEnvio.EN_TRANSITO),
    _crear_semilla("Rosario", "Mendoza", "87654321",
                   "Luis Perez", EstadoEnvio.EN_SUCURSAL),
    _crear_semilla("La Plata", "Tucuman", "11223344",
                   "Maria Lopez", EstadoEnvio.INICIADO),
]


# --- Endpoints ---

# US-07/25: Registrar envio y asignarle una prioridad
@router.post("/", status_code=201)
def registrar_envio(nuevo_envio: Envio):
    """US-07: Registro individual de envio con Tracking ID autogenerado."""
    nuevo_envio.trackingId = f"TRK-{uuid.uuid4().hex[:8].upper()}"

    dims = nuevo_envio.dimensiones
    pred = predecir_prioridad(
        peso_kg=nuevo_envio.peso_kg,
        largo_cm=dims.largo_cm if dims else None,
        ancho_cm=dims.ancho_cm if dims else None,
        alto_cm=dims.alto_cm if dims else None,
    )
    nuevo_envio.prioridad_ml = PrioridadEnvio(pred)

    nuevo_envio.historial.append(EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=nuevo_envio.origen,
        observaciones="Envio registrado en el sistema por el Operador.",
    ))
    mock_db_envios.append(nuevo_envio)
    return {"mensaje": "Envio registrado con exito", "trackingId": nuevo_envio.trackingId, "envio": nuevo_envio}


# US-11 / US-14 / US-15: Listar envios con filtros opcionales
@router.get("/")
def listar_envios(
    estados: Optional[List[EstadoEnvio]] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    """
    US-11: Listado general de envios.
    US-14: Filtrar por uno o varios estados. Ejemplo: ?estados=INICIADO&estados=EN_SUCURSAL
    US-15: Filtrar por rango de fecha de creacion. Ejemplo: ?fecha_desde=2024-01-01&fecha_hasta=2024-12-31
    """
    resultado = list(mock_db_envios)

    if estados:
        resultado = [e for e in resultado if _estado_actual(e) in estados]

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400, detail="fecha_desde no puede ser mayor a fecha_hasta.")

    if fecha_desde:
        resultado = [e for e in resultado if e.fechaCreacion >= fecha_desde]

    if fecha_hasta:
        resultado = [e for e in resultado if e.fechaCreacion <= fecha_hasta]

    return sorted(resultado, key=lambda e: e.fechaCreacion.replace(tzinfo=None))


# US-12: Buscar envio por Tracking ID
@router.get("/{tracking_id}")
def buscar_resumen_envio(tracking_id: str):
    """US-12: Devuelve informacion principal y estado actual del envio."""
    envio = _buscar_envio(tracking_id)
    return {
        "trackingId": envio.trackingId,
        "origen": envio.origen,
        "destino": envio.destino,
        "estado_actual": _estado_actual(envio),
    }


# US-13: Detalle completo con historial
@router.get("/{tracking_id}/detalles")
def buscar_detalle_envio(tracking_id: str):
    """US-13: Devuelve toda la informacion del envio incluyendo historial de eventos."""
    return _buscar_envio(tracking_id)


# US-19: Historial de estados
@router.get("/{tracking_id}/historial_estado")
def historial_envio(tracking_id: str):
    """US-19: Devuelve el historial completo de eventos del envio."""
    return _buscar_envio(tracking_id).historial


# US-08 / US-16 / US-18 / US-20: Cambio de estado (solo Supervisor)
@router.patch("/{tracking_id}/estado")
def cambiar_estado_envio(tracking_id: str, body: CambioEstadoRequest, x_rol: str = Header(...)):
    """US-08/16/18/20: Cambia el estado del envio. Solo accesible para Supervisor."""
    if x_rol.lower() != "supervisor":
        raise HTTPException(
            status_code=403, detail="Acceso denegado: se requiere rol Supervisor.")
    envio = _buscar_envio(tracking_id)
    if _estado_actual(envio) == EstadoEnvio.CANCELADO:
        raise HTTPException(
            status_code=400, detail="El envio esta CANCELADO y no puede cambiar de estado.")
    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=body.nuevo_estado,
        ubicacion=body.ubicacion,
        observaciones=body.observaciones,
    ))
    return {"mensaje": "Estado actualizado con exito", "trackingId": tracking_id, "nuevo_estado": body.nuevo_estado}


# US-09: Editar datos del envio en estado INICIADO
@router.patch("/{tracking_id}")
def editar_envio(tracking_id: str, datos: EnvioUpdate):
    """US-09: Permite editar datos del envio solo si esta en estado INICIADO."""
    envio = _buscar_envio(tracking_id)

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400, detail="Solo se puede editar un envio en estado INICIADO.")

    if datos.origen is not None:
        envio.origen = datos.origen
    if datos.destino is not None:
        envio.destino = datos.destino
    if datos.consentimiento is not None:
        envio.consentimiento = datos.consentimiento
    if datos.remitente is not None:
        if datos.remitente.dni is not None:
            envio.remitente.dni = datos.remitente.dni
        if datos.remitente.nombre is not None:
            envio.remitente.nombre = datos.remitente.nombre
        if datos.remitente.anonimizado is not None:
            envio.remitente.anonimizado = datos.remitente.anonimizado

    return {"mensaje": "Envio editado con exito", "envio": envio}


# US-10: Cancelar envio en estado INICIADO
@router.patch("/{tracking_id}/cancelar")
def cancelar_envio(tracking_id: str, confirmacion: ConfirmacionCancelacion):
    """US-10: Cancela el envio si esta en estado INICIADO y se confirma la accion."""
    envio = _buscar_envio(tracking_id)

    if not confirmacion.confirmar:
        raise HTTPException(
            status_code=400, detail="La cancelacion debe ser confirmada explicitamente.")

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400, detail="Solo se puede cancelar un envio en estado INICIADO.")

    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio.CANCELADO,
        ubicacion=envio.origen,
        observaciones="Envio cancelado por el Operador.",
    ))
    return {"mensaje": "Envio cancelado con exito", "envio": envio}
