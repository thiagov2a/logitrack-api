from fastapi import FastAPI
from routers import envios

app = FastAPI(
    title="LogiTrack API",
    description="Mock API para el MVP de Logística",
    version="1.0.0"
)

app.include_router(envios.router)

@app.get("/")
def estado_del_servidor():
    return {"mensaje": "¡El servidor de LogiTrack está vivo y funcionando!", "estado": "OK"}