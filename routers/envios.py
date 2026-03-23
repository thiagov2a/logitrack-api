from fastapi import APIRouter
from models.envio import Envio
from models.tracking import EventoTracking
from models.enums import EstadoEnvio
import uuid

router = APIRouter(prefix="/api/envios", tags=["Envíos"])

# Base de datos simulada en memoria
mock_db_envios = []

@router.post("/", status_code=201)
def registrar_envio(nuevo_envio: Envio):
    """
    US07: Registro individual de envío con Tracking ID
    """
    # 1. Criterio de Aceptación: Generar Tracking ID único
    codigo_unico = uuid.uuid4().hex[:8].upper()
    nuevo_envio.trackingId = f"TRK-{codigo_unico}"

    # 2. Criterio de Aceptación: Inicializar estado en "INICIADO"
    evento_inicial = EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=nuevo_envio.origen,
        observaciones="Envío registrado en el sistema por el Operador.",
    )

    # 3. Guardamos el evento adentro de la lista del envío
    nuevo_envio.historial.append(evento_inicial)

    # 4. Guardamos el envío en la base de datos de mentira
    mock_db_envios.append(nuevo_envio)

    return {
        "mensaje": "Envío registrado con éxito",
        "trackingId": nuevo_envio.trackingId,
        "envio": nuevo_envio,
    }
