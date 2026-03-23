from enum import Enum


class EstadoEnvio(str, Enum):
    INICIADO = "INICIADO"
    EN_SUCURSAL = "EN_SUCURSAL"
    EN_TRANSITO = "EN_TRANSITO"
    ENTREGADO = "ENTREGADO"


class PrioridadEnvio(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
