import pytest
from fastapi.testclient import TestClient
from main import app
from src.routers import envios as envios_module
from src.routers import auth as auth_module
from src.routers.auth import _hash
from src.models.envio import Envio
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio
from src.models.usuario import Usuario

USUARIOS_INICIALES = [
    Usuario(email="operador@logitrack.com", password=_hash("operador123"), nombre="Juan Pérez", rol="operador"),
    Usuario(email="supervisor@logitrack.com", password=_hash("supervisor123"), nombre="María López", rol="supervisor"),
    Usuario(email="admin@logitrack.com", password=_hash("admin123"), nombre="Carlos García", rol="administrador"),
]


def _seed():
    e = Envio(
        trackingId="TRK-TEST01", origen="Buenos Aires", destino="Cordoba",
        remitente=Cliente(dni="12345678", nombre="Ana"),
        destinatario=Cliente(dni="87654321", nombre="Carlos"),
    )
    e.historial.append(
        EventoTracking(trackingId="TRK-TEST01", estado_actual=EstadoEnvio.INICIADO, ubicacion="Buenos Aires")
    )
    return e


def _seed_con_tracking(tracking_id: str, origen: str, destino: str, nombre: str, estado: EstadoEnvio):
    e = Envio(
        trackingId=tracking_id,
        origen=origen,
        destino=destino,
        remitente=Cliente(dni="99999999", nombre=nombre),
        destinatario=Cliente(dni="00000000", nombre="Destinatario Test"),
    )
    e.historial.append(
        EventoTracking(trackingId=tracking_id, estado_actual=EstadoEnvio.INICIADO, ubicacion=origen)
    )
    if estado != EstadoEnvio.INICIADO:
        e.historial.append(
            EventoTracking(trackingId=tracking_id, estado_actual=estado, ubicacion=destino)
        )
    return e


@pytest.fixture(autouse=True)
def reset_db():
    envios_module.mock_db_envios.clear()
    envios_module.mock_db_envios.append(_seed())
    auth_module.mock_usuarios.clear()
    auth_module.mock_usuarios.extend([
        Usuario(email=u.email, password=u.password, nombre=u.nombre, rol=u.rol)
        for u in USUARIOS_INICIALES
    ])
    yield
    envios_module.mock_db_envios.clear()
    auth_module.mock_usuarios.clear()


@pytest.fixture
def client(reset_db):
    return TestClient(app)


@pytest.fixture
def client_operador(reset_db):
    return TestClient(app, cookies={"usuario_email": "operador@logitrack.com"})


@pytest.fixture
def client_supervisor(reset_db):
    return TestClient(app, cookies={"usuario_email": "supervisor@logitrack.com"})


@pytest.fixture
def client_admin(reset_db):
    return TestClient(app, cookies={"usuario_email": "admin@logitrack.com"})
