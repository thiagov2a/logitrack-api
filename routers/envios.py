from fastapi import APIRouter, HTTPException, Body
from models.envio import Envio
from models.enums import EstadoEnvio
from models.tracking import EventoTracking
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envíos"])

# Base de datos simulada en memoria
mock_db_envios = []


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


# --- 5. CAMBIO DE ESTADO INDIVIDUAL (US-16) ---
# Definimos el flujo lógico estricto como una lista
FLUJO_ESTADOS = [
    EstadoEnvio.INICIADO,
    EstadoEnvio.EN_SUCURSAL,
    EstadoEnvio.EN_TRANSITO,
    EstadoEnvio.ENTREGADO
]

@router.patch("/{tracking_id}/estado")
def cambiar_estado_envio(
    tracking_id: str, 
    nuevo_estado: EstadoEnvio = Body(..., embed=True, description="El nuevo estado del envío"),
    ubicacion: str = Body(..., embed=True, description="Ubicación donde ocurre el evento"),
    observaciones: str = Body(None, embed=True, description="Observaciones opcionales")
):
    """
    US-16: El sistema debe respetar el flujo lógico.
    Se agrega un nuevo evento al historial validando el estado anterior.
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

    # 2. Obtener el estado actual (es el último evento en el historial)
    if not envio_encontrado.historial:
        raise HTTPException(
            status_code=500,
            detail="Error interno: El envío no tiene un historial inicial válido."
        )
    
    estado_actual = envio_encontrado.historial[-1].estado_actual

    # 3. Validar el flujo lógico
    indice_actual = FLUJO_ESTADOS.index(estado_actual)
    indice_nuevo = FLUJO_ESTADOS.index(nuevo_estado)

    if indice_nuevo == indice_actual:
        return {"mensaje": "El envío ya se encuentra en este estado.", "envio": envio_encontrado}

    if indice_nuevo != indice_actual + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Transición no permitida. No se puede pasar de '{estado_actual.value}' a '{nuevo_estado.value}'."
        )

    # 4. Crear el nuevo registro para el historial
    nuevo_evento = EventoTracking(
        estado_actual=nuevo_estado,
        ubicacion=ubicacion,
        observaciones=observaciones,
        trackingId=tracking_id
    )

    # 5. Agregar el nuevo evento a la lista del historial del envío
    envio_encontrado.historial.append(nuevo_evento)

    return {
        "mensaje": "Estado actualizado y evento registrado exitosamente",
        "envio": envio_encontrado
    }