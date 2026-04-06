from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import PrioridadEnvio
import re


class Dimensiones(BaseModel):
    largo_cm: float = Field(..., gt=0,
                            description="Largo del paquete en centímetros")
    ancho_cm: float = Field(..., gt=0,
                            description="Ancho del paquete en centímetros")
    alto_cm: float = Field(..., gt=0,
                           description="Alto del paquete en centímetros")


class Envio(BaseModel):
    trackingId: Optional[str] = None
    origen: str = Field(..., description="Origen obligatorio")
    destino: str = Field(..., description="Destino obligatorio")
    fechaCreacion: datetime = Field(default_factory=datetime.now)
    peso_kg: Optional[float] = Field(
        default=None,
        gt=0,
        description="Peso total del envío en kilogramos (Opcional)"
    )
    dimensiones: Optional[Dimensiones] = Field(
        default=None,
        description="Dimensiones físicas del paquete (Opcional)"
    )
    consentimiento: bool = True
    prioridad_ml: Optional[PrioridadEnvio] = Field(
        default=None,
        description="Prioridad clasificada automáticamente por el modelo ML"
    )

    @field_validator("origen", "destino")
    @classmethod
    def validar_ciudad(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("El campo debe tener al menos 2 caracteres.")
        if not re.fullmatch(r"[a-zA-Zà-ÿ\s]+", v):
            raise ValueError("Solo se permiten letras y espacios.")
        return v.strip()

    # Clientes (Relacion 1 a 1)
    remitente: Cliente
    destinatario: Cliente

    # Lista de Eventos (Relacion 1 a Muchos)
    historial: List[EventoTracking] = Field(
        default_factory=list, description="Historial de estados del paquete"
    )
