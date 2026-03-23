# data_shipments.py
from typing import List, Dict, Optional

# Ejemplo en memoria (ajusta a tu estructura real)
shipments: List[Dict[str, str]] = [
    {"tracking_id": "ABC123", "origin": "SF", "destination": "LA", "status": "Iniciado"},
    {"tracking_id": "XYZ789", "origin": "NYC", "destination": "SF", "status": "En tránsito"},
]

def find_by_tracking_id(tracking_id: str, data: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
    dataset = data if data is not None else shipments
    for shipment in dataset:
        if shipment.get("tracking_id") == tracking_id:
            return shipment
    return None