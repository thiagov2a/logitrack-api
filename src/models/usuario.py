from pydantic import BaseModel, Field


class Usuario(BaseModel):
    email: str
    password: str = Field(exclude=True)
    nombre: str
    rol: str
    activo: bool = True
