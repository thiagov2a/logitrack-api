from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class Cliente(BaseModel):
    dni: str = Field(..., description="DNI del remitente obligatorio")
    nombre: Optional[str] = None
    anonimizado: bool = False

    @field_validator("dni")
    @classmethod
    def validar_dni(cls, v):
        if not re.fullmatch(r"\d{7,8}", v):
            raise ValueError("El DNI debe contener entre 7 y 8 dígitos numéricos.")
        return v

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        if v is not None:
            if len(v.strip()) < 2:
                raise ValueError("El nombre debe tener al menos 2 caracteres.")
            if not re.fullmatch(r"[a-zA-Zà-ÿ\s]+", v):
                raise ValueError("El nombre solo puede contener letras y espacios.")
        return v
