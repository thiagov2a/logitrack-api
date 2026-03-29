from fastapi import FastAPI
from routers import envios
import uvicorn

app = FastAPI(
    title="LogiTrack API", description="Mock API para el TP (Sprint 1)", version="1.0.0"
)

# Conectamos las rutas de envíos
app.include_router(envios.router, prefix="/envios", tags=["Envios"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
