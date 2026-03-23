from pydantic import BaseModel

class Envio(BaseModel):
    id: str
    origen: str
    destino: str
    peso_kg: float
    estado: str