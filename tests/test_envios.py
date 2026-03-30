import pytest
from fastapi.testclient import TestClient
from main import app
from routers import envios as envios_module
from models.envio import Envio
from models.cliente import Cliente
from models.tracking import EventoTracking
from models.enums import EstadoEnvio


def _seed():
    e = Envio(
        trackingId="TRK-TEST01", origen="Buenos Aires", destino="Cordoba",
        remitente=Cliente(dni="12345678", nombre="Ana"),
    )
    e.historial.append(
        EventoTracking(trackingId="TRK-TEST01", estado_actual=EstadoEnvio.INICIADO, ubicacion="Buenos Aires")
    )
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


# --- US-09: Editar datos en estado INICIADO ---
def test_editar_envio_en_estado_iniciado(client):
    payload = {"destino": "Mendoza"}
    response = client.patch("/api/envios/TRK-TEST01", json=payload)
    assert response.status_code == 200
    assert response.json()["envio"]["destino"] == "Mendoza"


def test_editar_envio_fuera_de_estado_iniciado_retorna_400(client):
    client.patch("/api/envios/TRK-TEST01/estado", json={"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"})
    response = client.patch("/api/envios/TRK-TEST01", json={"destino": "Mendoza"})
    assert response.status_code == 400


# --- US-10: Cancelar envio ---
def test_cancelar_envio_en_estado_iniciado(client):
    response = client.patch("/api/envios/TRK-TEST01/cancelar", json={"confirmar": True})
    assert response.status_code == 200
    estados = [e["estado_actual"] for e in response.json()["envio"]["historial"]]
    assert "CANCELADO" in estados


def test_cancelar_envio_sin_confirmacion_retorna_400(client):
    response = client.patch("/api/envios/TRK-TEST01/cancelar", json={"confirmar": False})
    assert response.status_code == 400


def test_cancelar_envio_fuera_de_estado_iniciado_retorna_400(client):
    client.patch("/api/envios/TRK-TEST01/estado", json={"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"})
    response = client.patch("/api/envios/TRK-TEST01/cancelar", json={"confirmar": True})
    assert response.status_code == 400


# --- US-14: Filtrar por estado ---
def test_filtrar_envios_por_estado(client):
    response = client.get("/api/envios/?estados=INICIADO")
    assert response.status_code == 200
    for envio in response.json():
        assert envio["historial"][-1]["estado_actual"] == "INICIADO"


# --- US-15: Filtrar por rango de fecha ---
def test_filtrar_envios_por_fecha_desde(client):
    response = client.get("/api/envios/?fecha_desde=2000-01-01T00:00:00")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_filtrar_envios_fecha_futura_retorna_vacio(client):
    response = client.get("/api/envios/?fecha_desde=2099-01-01T00:00:00")
    assert response.status_code == 200
    assert len(response.json()) == 0


# --- US-16/18/20: Avanzar estado ---
def test_avanzar_estado_envio(client):
    payload = {"ubicacion": "Cordoba"}
    response = client.patch("/api/envios/TRK-TEST01/avanzar_estado", json=payload)
    assert response.status_code == 200
    historial = response.json()["envio"]["historial"]
    assert historial[-1]["estado_actual"] == "EN_SUCURSAL"


def test_avanzar_estado_envio_cancelado_retorna_400(client):
    client.patch("/api/envios/TRK-TEST01/cancelar", json={"confirmar": True})
    response = client.patch("/api/envios/TRK-TEST01/avanzar_estado", json={"ubicacion": "Cordoba"})
    assert response.status_code == 400


def test_avanzar_estado_envio_entregado_retorna_400(client):
    client.patch("/api/envios/TRK-TEST01/estado", json={"nuevo_estado": "ENTREGADO", "ubicacion": "Cordoba"})
    response = client.patch("/api/envios/TRK-TEST01/avanzar_estado", json={"ubicacion": "Cordoba"})
    assert response.status_code == 400


# --- US-19: Historial de estados ---
def test_historial_envio_retorna_lista(client):
    response = client.get("/api/envios/TRK-TEST01/historial_estado")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_historial_envio_inexistente_retorna_404(client):
    response = client.get("/api/envios/TRK-INVALIDO/historial_estado")
    assert response.status_code == 404
