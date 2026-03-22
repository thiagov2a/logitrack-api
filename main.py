from fastapi import FastAPI

app = FastAPI(
    title="LogiTrack API",
    description="Mock API para el MVP de Logística",
    version="1.0.0"
)

@app.get("/")
def estado_del_servidor():
    return {"mensaje": "¡El servidor de LogiTrack está vivo y funcionando!", "estado": "OK"}