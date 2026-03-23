# routers/tracking.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
try:
    from models.tracking import find_by_tracking_id  # si ya existe
except Exception:
    from models.data_shipments import find_by_tracking_id  # fallback a data_shipments

router = APIRouter()

class ShipmentResponse(BaseModel):
    tracking_id: str
    origin: str
    destination: str
    status: str

@router.get("/track/{tracking_id}", response_model=ShipmentResponse)
async def track_by_id(tracking_id: str):
    result = find_by_tracking_id(tracking_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No se encontraron envíos con ese código")
    return ShipmentResponse(
        tracking_id=result["tracking_id"],
        origin=result["origin"],
        destination=result["destination"],
        status=result["status"],
    )