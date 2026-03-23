from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from .data_shipments import find_by_tracking_id

# Modelos de respuesta
class ShipmentSummary(BaseModel):
    tracking_id: str
    origin: str
    destination: str
    status: str

class Party(BaseModel):
    name: str
    address: str

class ShipmentDetailResponse(BaseModel):
    tracking_id: str
    origin: str
    destination: str
    status: str
    created_at: Optional[str] = None
    sender: Party
    recipient: Party

router = APIRouter()

@router.get("/track/{tracking_id}", response_model=ShipmentSummary)
async def Busqueda_de_envio_por_Tracking_ID(tracking_id: str):
    result = find_by_tracking_id(tracking_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No se encontraron envíos con ese código")
    return ShipmentSummary(
        tracking_id=result["tracking_id"],
        origin=result["origin"],
        destination=result["destination"],
        status=result["status"],
    )

@router.get("/track/{tracking_id}/details", response_model=ShipmentDetailResponse)
async def Visualizacion_de_detalle_completo_de_envio(tracking_id: str):
    result = find_by_tracking_id(tracking_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No se encontraron envíos con ese código")
    return ShipmentDetailResponse(
        tracking_id=result["tracking_id"],
        origin=result["origin"],
        destination=result["destination"],
        status=result["status"],
        created_at=result.get("created_at"),
        sender=Party(name=result["sender"]["name"], address=result["sender"]["address"]),
        recipient=Party(name=result["recipient"]["name"], address=result["recipient"]["address"]),
    )