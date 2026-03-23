from fastapi import FastAPI
from routers import envios

app = FastAPI(
    title="LogiTrack API",
    description="Mock API para el TP (Sprint 1)",
    version="1.0.0"
)

# Conectamos las rutas de envíos
app.include_router(envios.router)

# --- MAGIA PARA QUE FUNCIONE EL BOTÓN PLAY ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
