import pytest
from datetime import datetime
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
        EventoTracking(
            trackingId="TRK-TEST01",
            estado_actual=EstadoEnvio.INICIADO,
            ubicacion="Buenos Aires"
        )
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

# --- US-16: Cambio de estado de envio ---


def test_us16_avanzar_flujo_logico(client):
    tracking_id = "TRK-TEST01"

    # 1. Avanzamos a EN_SUCURSAL
    res1 = client.patch(f"/{tracking_id}/avanzar_estado",
                        json={"ubicacion": "Sucursal Origen"})
    assert res1.status_code == 200
    assert res1.json()[
        "envio"]["historial"][-1]["estado_actual"] == "EN_SUCURSAL"

    # 2. Avanzamos a EN_TRANSITO
    res2 = client.patch(f"/{tracking_id}/avanzar_estado",
                        json={"ubicacion": "Ruta 9"})
    assert res2.status_code == 200
    assert res2.json()[
        "envio"]["historial"][-1]["estado_actual"] == "EN_TRANSITO"

    # 3. Avanzamos a ENTREGADO
    res3 = client.patch(f"/{tracking_id}/avanzar_estado",
                        json={"ubicacion": "Casa del cliente"})
    assert res3.status_code == 200
    assert res3.json()[
        "envio"]["historial"][-1]["estado_actual"] == "ENTREGADO"

    # 4. Verificamos que ya no se pueda avanzar más (Error 400 esperado)
    res_error = client.patch(
        f"/{tracking_id}/avanzar_estado", json={"ubicacion": "Extra"})
    assert res_error.status_code == 400
    assert "no puede avanzar más" in res_error.json()["detail"]

# --- US-18: Registrar automáticamente la fecha y hora ---


def test_us18_registrar_fecha_hora(client):
    tracking_id = "TRK-TEST01"
    payload = {"ubicacion": "Sucursal Centro"}

    tiempo_antes = datetime.now()

    response = client.patch(f"/{tracking_id}/avanzar_estado", json=payload)
    assert response.status_code == 200

    data = response.json()
    ultimo_evento = data["envio"]["historial"][-1]

    # Verificamos que el campo 'fecha' exista
    assert "fecha" in ultimo_evento

    # Convertimos el string ISO a datetime y comprobamos que sea reciente
    fecha_registrada = datetime.fromisoformat(ultimo_evento["fecha"])
    assert fecha_registrada >= tiempo_antes


# --- US-20: Permitir agregar una observación al estado ---
def test_us20_agregar_observacion_al_estado(client):
    tracking_id = "TRK-TEST01"  # Arranca en INICIADO

    payload = {
        "ubicacion": "Sucursal Despacho",
        "observaciones": "El paquete llegó con la etiqueta arrugada"
    }

    response = client.patch(f"/{tracking_id}/avanzar_estado", json=payload)
    assert response.status_code == 200

    data = response.json()
    historial = data["envio"]["historial"]

    # El evento anterior (índice -2) es el "INICIADO" que acabamos de dejar
    evento_anterior = historial[-2]
    # El evento nuevo (índice -1) es el "EN_SUCURSAL" que acabamos de crear
    evento_nuevo = historial[-1]

    # Verificamos que la observación se guardó en el estado anterior
    assert evento_anterior["estado_actual"] == "INICIADO"
    assert "etiqueta arrugada" in evento_anterior["observaciones"]

    # Verificamos que el nuevo estado nace limpio de observaciones
    assert evento_nuevo["estado_actual"] == "EN_SUCURSAL"
    assert evento_nuevo["observaciones"] is None
