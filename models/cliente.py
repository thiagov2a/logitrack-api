from pydantic import BaseModel, Field
from typing import Optional

class Cliente(BaseModel):
    dni: str = Field(..., description="DNI del remitente obligatorio")
    nombre: Optional[str] = None
    anonimizado: bool = False