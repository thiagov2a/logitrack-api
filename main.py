from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.routers import envios, views
import uvicorn

app = FastAPI(
    title="LogiTrack API", description="Mock API para el TP (Sprint 2)", version="2.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(views.router)
app.include_router(envios.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
