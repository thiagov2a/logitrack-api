from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from src.models.enums import EstadoEnvio


class EventoTracking(BaseModel):
    fecha: datetime = Field(default_factory=datetime.now)
    ubicacion: str = Field(..., description="Ubicación donde ocurre el evento")
    observaciones: Optional[str] = None
    estado_actual: EstadoEnvio
    trackingId: Optional[str] = (
        None  # Opcional para que el usuario no tenga que mandarlo
    )
