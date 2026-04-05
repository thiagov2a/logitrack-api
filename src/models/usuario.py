from pydantic import BaseModel


class Usuario(BaseModel):
    email: str
    password: str
    nombre: str
    rol: str  # operador, supervisor, administrador
    activo: bool = True
