from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from pydantic import BaseModel
from models.envio import Envio
from models.enums import EstadoEnvio
from models.tracking import EventoTracking
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envíos"])

# Base de datos simulada en memoria
mock_db_envios = []


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


def obtener_estado_actual(envio: Envio):
    """
    Devuelve el estado actual del envío tomando el último evento del historial.
    Si no hay historial, se considera INICIADO por defecto.
    """
    if envio.historial and len(envio.historial) > 0:
        return envio.historial[-1].estado_actual
    return EstadoEnvio.INICIADO


# --- 1. ALTA DE ENVÍO (US-07) ---
@router.post("/", status_code=201)
def registrar_envio(nuevo_envio: Envio):
    """
    US07: Registro individual de envío con Tracking ID
    """
    # 1. Autogenerar Tracking ID
    codigo_unico = uuid.uuid4().hex[:8].upper()
    nuevo_envio.trackingId = f"TRK-{codigo_unico}"

    # 2. Inicializar estado
    evento_inicial = EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=nuevo_envio.origen,
        observaciones="Envío registrado en el sistema por el Operador.",
    )

    # 3. Guardar evento en el historial del envío
    nuevo_envio.historial.append(evento_inicial)

    # 4. Guardar en la base de datos de mentira
    mock_db_envios.append(nuevo_envio)

    return {
        "mensaje": "Envío registrado con éxito",
        "trackingId": nuevo_envio.trackingId,
        "envio": nuevo_envio,
    }


# --- 2. LISTADO GENERAL (US-11) ---
@router.get("/")
def listar_envios():
    """
    US-11: Listado general de envíos.
    Retorna todos los envíos que están en la memoria.
    """
    return mock_db_envios


# --- 3. BÚSQUEDA BÁSICA (US-12) ---
@router.get("/{tracking_id}")
def buscar_resumen_envio(tracking_id: str):
    """
    US-12: Búsqueda de envío por Tracking ID.
    Devuelve solo la información principal y el estado actual del paquete.
    """
    envio_encontrado = next(
        (envio for envio in mock_db_envios if envio.trackingId == tracking_id), None
    )

    if not envio_encontrado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún envío con el código {tracking_id}",
        )

    # Buscamos el estado actual mirando el último evento de la lista de historial
    estado_actual = (
        envio_encontrado.historial[-1].estado_actual
        if envio_encontrado.historial
        else "DESCONOCIDO"
    )

    return {
        "trackingId": envio_encontrado.trackingId,
        "origen": envio_encontrado.origen,
        "destino": envio_encontrado.destino,
        "estado_actual": estado_actual,
    }


# --- 4. DETALLE COMPLETO Y TRACKING (US-13) ---
@router.get("/{tracking_id}/detalles")
def buscar_detalle_envio(tracking_id: str):
    """
    US-13: Visualización de detalle completo de envío.
    Devuelve absolutamente toda la información: remitente, fechas y el historial completo de eventos.
    """
    envio_encontrado = next(
        (envio for envio in mock_db_envios if envio.trackingId == tracking_id), None
    )

    if not envio_encontrado:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ningún envío con el código {tracking_id}",
        )

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


# --- 6. CAMBIO DE ESTADO INDIVIDUAL (US-16,18 y 20) ---
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
    indice_actual = FLUJO_ESTADOS.index(estado_actual)

    # 3. Verificar si ya llegó al estado final (ENTREGADO)
    if indice_actual == len(FLUJO_ESTADOS) - 1:
        raise HTTPException(
            status_code=400,
            detail="Operación no permitida: El envío ya ha sido ENTREGADO y no puede avanzar más."
        )

    # 4. Determinar automáticamente el siguiente estado
    nuevo_estado = FLUJO_ESTADOS[indice_actual + 1]

    # 5. Crear el nuevo registro para el historial
    nuevo_evento = EventoTracking(
        estado_actual=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
        trackingId=tracking_id
    )

    # 6. Agregar el nuevo evento
    envio_encontrado.historial.append(nuevo_evento)

    return {
        "mensaje": f"Estado avanzado exitosamente a '{nuevo_estado.value}'",
        "envio": envio_encontrado
    }