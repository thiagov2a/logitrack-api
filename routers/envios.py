import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from models.envio import Envio

# Instanciamos el router
router = APIRouter()

# Calculamos la ruta exacta a enviosprueba.json basándonos en dónde está este archivo
# __file__ es envios.py -> parent es routers -> parent es app -> luego entramos a data
BASE_DIR = Path(__file__).resolve().parent.parent
ARCHIVO_ENVIOS = BASE_DIR / "data" / "enviosprueba.json"

@router.get("/envios/", response_model=list[Envio])
def listar_envios():
    """
    Retorna la lista de todos los envíos desde el archivo JSON de prueba.
    """
    if not ARCHIVO_ENVIOS.exists():
        return {"mensaje":"El archivo no existe"}
    try:
        with open(ARCHIVO_ENVIOS, "r", encoding="utf-8") as f:
            envios_lista = json.load(f)
        return envios_lista
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=500, 
            content={"mensaje":"Error interno del servidor: El archivo de datos de envíos está corrupto, vacio o no tiene un formato JSON válido."}
        )