from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking


class Envio(BaseModel):
    trackingId: Optional[str] = None
    origen: str = Field(..., description="Origen obligatorio")
    destino: str = Field(..., description="Destino obligatorio")
    fechaCreacion: datetime = Field(default_factory=datetime.now)
    consentimiento: bool = True
    prioridadManual: bool = False
    activo: bool = True

    # Clientes (Relacion 1 a 1)
    remitente: Cliente
    destinatario: Optional[Cliente] = None

    # Lista de Eventos (Relacion 1 a Muchos)
    historial: List[EventoTracking] = Field(
        default_factory=list, description="Historial de estados del paquete"
    )
