# data_shipments.py
#from typing import List, Dict, Optional

# Ejemplo en memoria (ajusta a tu estructura real)
#shipments: List[Dict[str, str]] = [
 #   {"tracking_id": "ABC123", "origin": "SF", "destination": "LA", "status": "Iniciado"},
  #  {"tracking_id": "XYZ789", "origin": "NYC", "destination": "SF", "status": "En tránsito"},
#]

#def find_by_tracking_id(tracking_id: str, data: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
 #   dataset = data if data is not None else shipments
  #  for shipment in dataset:
   #     if shipment.get("tracking_id") == tracking_id:
    #        return shipment
    #return None
    

from typing import List, Dict, Optional, Any

_shipments: List[Dict[str, Any]] = [
    {
        "tracking_id": "ABC123",
        "origin": "SF",
        "destination": "LA",
        "status": "Iniciado",
        "created_at": "2025-01-22T02:24:00",
        "sender": {"name": "ACME Corp", "address": "123 Main St"},
        "recipient": {"name": "Juan Perez", "address": "456 Elm St"},
    },
    {
        "tracking_id": "XYZ789",
        "origin": "NYC",
        "destination": "SF",
        "status": "En tránsito",
        "created_at": "2025-01-23T10:15:00",
        "sender": {"name": "Globex", "address": "789 Market Ave"},
        "recipient": {"name": "Ana Gomez", "address": "987 Pine Rd"},
    },
]

def find_by_tracking_id(tracking_id: str, data=None):
    dataset = data if data is not None else _shipments
    for s in dataset:
        if s.get("tracking_id") == tracking_id:
            return s
    return None