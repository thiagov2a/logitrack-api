from fastapi import FastAPI, Request
from fastapi.responses import Response
from src.routers import envios, views, auth, usuarios
import uvicorn

app = FastAPI(
    title="LogiTrack API", description="Mock API para el TP (Sprint 3)", version="3.0.0"
)


@app.middleware("http")
async def no_cache_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


app.include_router(auth.router)
app.include_router(views.router)
app.include_router(usuarios.router)
app.include_router(envios.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
