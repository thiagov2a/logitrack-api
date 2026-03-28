import pytest
from fastapi.testclient import TestClient
from main import app
from routers import envios as envios_module
from models.envio import Envio
from models.cliente import Cliente
from models.tracking import EventoTracking
from models.enums import EstadoEnvio


def _seed():
    e = Envio(trackingId="TRK-TEST01", origen="Buenos Aires", destino="Cordoba", remitente=Cliente(dni="12345678", nombre="Ana"))
    e.historial.append(EventoTracking(trackingId="TRK-TEST01", estado_actual=EstadoEnvio.INICIADO, ubicacion="Buenos Aires"))
    return e


@pytest.fixture(autouse=True)
def reset_db():
    envios_module.mock_db_envios.clear()
    envios_module.mock_db_envios.append(_seed())
    yield
    envios_module.mock_db_envios.clear()


@pytest.fixture
def client(reset_db):
    return TestClient(app)


# --- US-11: Listar envios ---
def test_listar_envios_retorna_semilla(client):
    response = client.get("/api/envios/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


# --- US-07: Registrar envio ---
def test_registrar_envio_genera_tracking_id(client):
    payload = {
        "origen": "Buenos Aires",
        "destino": "Cordoba",
        "remitente": {"dni": "99999999", "nombre": "Test User"}
    }
    response = client.post("/api/envios/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["trackingId"].startswith("TRK-")
    assert data["envio"]["historial"][0]["estado_actual"] == "INICIADO"


# --- US-12: Buscar envio por tracking ID ---
def test_buscar_envio_existente(client):
    response = client.get("/api/envios/TRK-TEST01")
    assert response.status_code == 200
    assert response.json()["trackingId"] == "TRK-TEST01"


def test_buscar_envio_inexistente_retorna_404(client):
    response = client.get("/api/envios/TRK-INVALIDO")
    assert response.status_code == 404


# --- US-13: Detalle completo ---
def test_detalle_envio_incluye_historial(client):
    response = client.get("/api/envios/TRK-TEST01/detalles")
    assert response.status_code == 200
    assert "historial" in response.json()


# --- US-08: Cambio de estado ---
def test_cambiar_estado_envio(client):
    payload = {"nuevo_estado": "ENTREGADO", "ubicacion": "Cordoba", "observaciones": "Entregado en domicilio"}
    response = client.patch("/api/envios/TRK-TEST01/estado", json=payload)
    assert response.status_code == 200
    assert response.json()["nuevo_estado"] == "ENTREGADO"


def test_cambiar_estado_envio_inexistente_retorna_404(client):
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    response = client.patch("/api/envios/TRK-INVALIDO/estado", json=payload)
    assert response.status_code == 404
