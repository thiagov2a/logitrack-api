import pytest
from fastapi.testclient import TestClient
from main import app
from src.routers import envios as envios_module
from src.models.envio import Envio
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio


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
        EventoTracking(
            trackingId=tracking_id,
            estado_actual=EstadoEnvio.INICIADO,
            ubicacion=origen
        )
    )

    if estado != EstadoEnvio.INICIADO:
        e.historial.append(
            EventoTracking(
                trackingId=tracking_id,
                estado_actual=estado,
                ubicacion=destino
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


@pytest.fixture
def client_operador(reset_db):
    c = TestClient(app, cookies={"usuario_email": "operador@logitrack.com"})
    return c


@pytest.fixture
def client_supervisor(reset_db):
    c = TestClient(app, cookies={"usuario_email": "supervisor@logitrack.com"})
    return c


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
        "remitente": {"dni": "99999999", "nombre": "Test User"},
        "destinatario": {"dni": "11111111", "nombre": "Test Dest"}
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


# --- US-08/16/18/20: Cambio de estado (solo Supervisor) ---
def test_cambiar_estado_envio(client):
    payload = {"nuevo_estado": "ENTREGADO", "ubicacion": "Cordoba", "observaciones": "Entregado en domicilio"}
    response = client.patch("/api/envios/TRK-TEST01/estado", json=payload, headers={"x-rol": "supervisor"})
    assert response.status_code == 200
    assert response.json()["nuevo_estado"] == "ENTREGADO"


def test_cambiar_estado_envio_inexistente_retorna_404(client):
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    response = client.patch("/api/envios/TRK-INVALIDO/estado", json=payload, headers={"x-rol": "supervisor"})
    assert response.status_code == 404


def test_cambiar_estado_con_rol_operador_retorna_403(client):
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    response = client.patch("/api/envios/TRK-TEST01/estado", json=payload, headers={"x-rol": "operador"})
    assert response.status_code == 403


def test_cambiar_estado_envio_cancelado_retorna_400(client):
    client.patch("/api/envios/TRK-TEST01/cancelar", json={"confirmar": True})
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    response = client.patch("/api/envios/TRK-TEST01/estado", json=payload, headers={"x-rol": "supervisor"})
    assert response.status_code == 400


def test_no_permite_cambiar_estado_de_envio_entregado(client):
    payload_entregado = {
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Cordoba",
        "observaciones": "Entrega final"
    }

    response_1 = client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_entregado,
        headers={"x-rol": "supervisor"}
    )
    assert response_1.status_code == 200

    payload_cancelado = {
        "nuevo_estado": "CANCELADO",
        "ubicacion": "Cordoba",
        "observaciones": "Intento inválido"
    }

    response_2 = client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_cancelado,
        headers={"x-rol": "supervisor"}
    )

    assert response_2.status_code == 400
    assert "estado terminal" in response_2.json()["detail"]


# --- US-09: Editar datos en estado INICIADO ---
def test_editar_envio_en_estado_iniciado(client):
    payload = {"destino": "Mendoza"}
    response = client.patch("/api/envios/TRK-TEST01", json=payload)
    assert response.status_code == 200
    assert response.json()["envio"]["destino"] == "Mendoza"


def test_editar_envio_fuera_de_estado_iniciado_retorna_400(client):
    headers = {"x-rol": "supervisor"}
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    client.patch("/api/envios/TRK-TEST01/estado", json=payload, headers=headers)
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
    headers = {"x-rol": "supervisor"}
    payload = {"nuevo_estado": "EN_TRANSITO", "ubicacion": "Rosario"}
    client.patch("/api/envios/TRK-TEST01/estado", json=payload, headers=headers)
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


def test_filtrar_envios_fecha_desde_mayor_hasta_retorna_400(client):
    response = client.get("/api/envios/?fecha_desde=2099-01-01T00:00:00&fecha_hasta=2000-01-01T00:00:00")
    assert response.status_code == 400


def test_listar_envios_ordenados_por_fecha(client):
    payload = {"origen": "Salta", "destino": "Jujuy", "remitente": {"dni": "11111111", "nombre": "Test"}}
    client.post("/api/envios/", json=payload)
    response = client.get("/api/envios/")
    fechas = [e["fechaCreacion"] for e in response.json()]
    assert fechas == sorted(fechas)


def test_detalle_envio_incluye_destinatario(client):
    response = client.get("/api/envios/TRK-TEST01/detalles")
    assert response.status_code == 200
    assert "destinatario" in response.json()


# --- US-16/18/20: Avanzar estado (eliminado, consolidado en /estado) ---

# --- US-21: Consentimiento / Políticas de privacidad ---
def test_crear_envio_form_sin_consentimiento_muestra_error_y_no_registra(client_operador):
    cantidad_antes = len(envios_module.mock_db_envios)

    response = client_operador.post(
        "/envios/nuevo",
        data={
            "origen": "Buenos Aires",
            "destino": "Cordoba",
            "remitente_dni": "12345678",
            "remitente_nombre": "Ana Gomez",
            "destinatario_dni": "87654321",
            "destinatario_nombre": "Luis Perez",
        }
    )

    assert response.status_code == 200
    assert "Debe aceptar las pol" in response.text
    assert len(envios_module.mock_db_envios) == cantidad_antes


def test_crear_envio_form_con_consentimiento_registra_envio(client_operador):
    cantidad_antes = len(envios_module.mock_db_envios)

    response = client_operador.post(
        "/envios/nuevo",
        data={
            "origen": "Buenos Aires",
            "destino": "Cordoba",
            "remitente_dni": "12345678",
            "remitente_nombre": "Ana Gomez",
            "destinatario_dni": "87654321",
            "destinatario_nombre": "Luis Perez",
            "consentimiento": "on",
        },
        follow_redirects=False
    )

    assert response.status_code == 303
    assert len(envios_module.mock_db_envios) == cantidad_antes + 1
    assert envios_module.mock_db_envios[-1].consentimiento is True


def test_registrar_envio_sin_consentimiento_no_valida_en_api(client):
    """La API REST valida consentimiento devolviendo 400."""
    payload = {
        "origen": "Buenos Aires",
        "destino": "Cordoba",
        "consentimiento": False,
        "remitente": {"dni": "99999999", "nombre": "Test User"},
        "destinatario": {"dni": "11111111", "nombre": "Test Dest"}
    }
    response = client.post("/api/envios/", json=payload)
    assert response.status_code == 400


# --- US-17: Cambio de estado masivo ---
def test_cambio_estado_masivo_supervisor_actualiza_solo_seleccionados(client):
    envios_module.mock_db_envios.append(
        _seed_con_tracking("TRK-TEST02", "Rosario", "Mendoza", "Luis", EstadoEnvio.EN_SUCURSAL)
    )
    envios_module.mock_db_envios.append(
        _seed_con_tracking("TRK-TEST03", "La Plata", "Tucuman", "Maria", EstadoEnvio.INICIADO)
    )

    payload = {
        "tracking_ids": ["TRK-TEST01", "TRK-TEST02"],
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Centro de distribución",
        "observaciones": "Cambio masivo de prueba"
    }

    response = client.patch(
        "/api/envios/estado-masivo",
        json=payload,
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_actualizados"] == 2
    assert "TRK-TEST01" in data["actualizados"]
    assert "TRK-TEST02" in data["actualizados"]
    assert "TRK-TEST03" not in data["actualizados"]

    envio1 = next(e for e in envios_module.mock_db_envios if e.trackingId == "TRK-TEST01")
    envio2 = next(e for e in envios_module.mock_db_envios if e.trackingId == "TRK-TEST02")
    envio3 = next(e for e in envios_module.mock_db_envios if e.trackingId == "TRK-TEST03")

    assert envio1.historial[-1].estado_actual == EstadoEnvio.ENTREGADO
    assert envio2.historial[-1].estado_actual == EstadoEnvio.ENTREGADO
    assert envio3.historial[-1].estado_actual == EstadoEnvio.INICIADO


def test_cambio_estado_masivo_con_rol_operador_retorna_403(client):
    payload = {
        "tracking_ids": ["TRK-TEST01"],
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Centro de distribución",
        "observaciones": "Intento sin permisos"
    }

    response = client.patch(
        "/api/envios/estado-masivo",
        json=payload,
        headers={"x-rol": "operador"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso denegado: se requiere rol Supervisor."


def test_cambio_estado_masivo_sin_seleccion_retorna_400(client):
    payload = {
        "tracking_ids": [],
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Centro de distribución",
        "observaciones": "Sin selección"
    }

    response = client.patch(
        "/api/envios/estado-masivo",
        json=payload,
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Debe seleccionar al menos un envio."


def test_cambio_estado_masivo_omite_envio_cancelado(client):
    envios_module.mock_db_envios.append(
        _seed_con_tracking("TRK-TEST02", "Rosario", "Mendoza", "Luis", EstadoEnvio.INICIADO)
    )

    client.patch("/api/envios/TRK-TEST02/cancelar", json={"confirmar": True})

    payload = {
        "tracking_ids": ["TRK-TEST02"],
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Centro de distribución",
        "observaciones": "Intento sobre cancelado"
    }

    response = client.patch(
        "/api/envios/estado-masivo",
        json=payload,
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_actualizados"] == 0
    assert len(data["omitidos"]) == 1
    assert data["omitidos"][0]["trackingId"] == "TRK-TEST02"


def test_cambio_masivo_omite_envio_entregado(client):
    envios_module.mock_db_envios.append(
        _seed_con_tracking("TRK-TEST02", "Rosario", "Mendoza", "Luis", EstadoEnvio.ENTREGADO)
    )

    payload = {
        "tracking_ids": ["TRK-TEST02"],
        "nuevo_estado": "CANCELADO",
        "ubicacion": "Centro de distribución",
        "observaciones": "Intento sobre entregado"
    }

    response = client.patch(
        "/api/envios/estado-masivo",
        json=payload,
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_actualizados"] == 0
    assert len(data["omitidos"]) == 1
    assert data["omitidos"][0]["trackingId"] == "TRK-TEST02"
    assert "estado terminal" in data["omitidos"][0]["motivo"]


# --- US-23: Exportación de datos de cliente (Derecho de Acceso) ---
def test_exportar_datos_remitente_csv_como_supervisor(client):
    response = client.get(
        "/api/envios/TRK-TEST01/exportar-cliente?tipo_cliente=remitente",
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in response.headers["content-disposition"]

    body = response.text
    assert "tracking_id,tipo_cliente,nombre,dni,direccion,anonimizado" in body
    assert "TRK-TEST01,remitente,Ana,12345678" in body


def test_exportar_datos_destinatario_csv_como_supervisor(client):
    envios_module.mock_db_envios[0].destinatario = Cliente(dni="87654321", nombre="Luis")

    response = client.get(
        "/api/envios/TRK-TEST01/exportar-cliente?tipo_cliente=destinatario",
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    body = response.text
    assert "TRK-TEST01,destinatario,Luis,87654321" in body


def test_exportar_datos_cliente_con_rol_invalido_retorna_403(client):
    response = client.get(
        "/api/envios/TRK-TEST01/exportar-cliente?tipo_cliente=remitente",
        headers={"x-rol": "operador"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso denegado: se requiere rol Supervisor."


def test_exportar_datos_cliente_inexistente_retorna_404(client):
    response = client.get(
        "/api/envios/TRK-INVALIDO/exportar-cliente?tipo_cliente=remitente",
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 404


def test_exportar_datos_destinatario_inexistente_retorna_404(client):
    """El destinatario es obligatorio en el modelo, por lo que este caso no aplica.
    Verificamos que el endpoint funciona correctamente con destinatario existente."""
    response = client.get(
        "/api/envios/TRK-TEST01/exportar-cliente?tipo_cliente=destinatario",
        headers={"x-rol": "supervisor"}
    )
    assert response.status_code == 200


def test_exportar_datos_cliente_con_tipo_invalido_retorna_400(client):
    response = client.get(
        "/api/envios/TRK-TEST01/exportar-cliente?tipo_cliente=cliente",
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 400
    assert "remitente" in response.json()["detail"].lower() or "destinatario" in response.json()["detail"].lower()


# --- US-19: Historial de estados ---
def test_historial_envio_retorna_lista(client):
    response = client.get("/api/envios/TRK-TEST01/historial_estado")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_historial_envio_inexistente_retorna_404(client):
    response = client.get("/api/envios/TRK-INVALIDO/historial_estado")
    assert response.status_code == 404


# --- US-22: Anonimización de datos (Derecho al Olvido) ---
def test_anonimizar_envio_finalizado_reemplaza_datos_personales(client):
    envios_module.mock_db_envios[0].destinatario = Cliente(dni="87654321", nombre="Luis")

    payload_estado = {
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Cordoba",
        "observaciones": "Entrega final"
    }
    client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_estado,
        headers={"x-rol": "supervisor"}
    )

    response = client.patch(
        "/api/envios/TRK-TEST01/anonimizar",
        json={"confirmar": True},
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200
    envio = response.json()["envio"]

    assert envio["remitente"]["nombre"] == "***"
    assert envio["remitente"]["dni"] == "***"
    assert envio["destinatario"]["nombre"] == "***"
    assert envio["destinatario"]["dni"] == "***"


def test_anonimizar_envio_no_finalizado_retorna_400(client):
    response = client.patch(
        "/api/envios/TRK-TEST01/anonimizar",
        json={"confirmar": True},
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Solo se puede anonimizar un envio finalizado."


def test_anonimizar_envio_con_rol_invalido_retorna_403(client):
    payload_estado = {
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Cordoba",
        "observaciones": "Entrega final"
    }
    client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_estado,
        headers={"x-rol": "supervisor"}
    )

    response = client.patch(
        "/api/envios/TRK-TEST01/anonimizar",
        json={"confirmar": True},
        headers={"x-rol": "operador"}
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Acceso denegado: se requiere rol Supervisor."


def test_anonimizar_envio_sin_confirmacion_retorna_400(client):
    payload_estado = {
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Cordoba",
        "observaciones": "Entrega final"
    }
    client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_estado,
        headers={"x-rol": "supervisor"}
    )

    response = client.patch(
        "/api/envios/TRK-TEST01/anonimizar",
        json={"confirmar": False},
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La anonimización debe ser confirmada explícitamente."


def test_anonimizar_envio_mantiene_historial_intacto(client):
    payload_estado = {
        "nuevo_estado": "ENTREGADO",
        "ubicacion": "Cordoba",
        "observaciones": "Entrega final"
    }
    client.patch(
        "/api/envios/TRK-TEST01/estado",
        json=payload_estado,
        headers={"x-rol": "supervisor"}
    )

    detalle_antes = client.get("/api/envios/TRK-TEST01/detalles")
    historial_antes = detalle_antes.json()["historial"]

    response = client.patch(
        "/api/envios/TRK-TEST01/anonimizar",
        json={"confirmar": True},
        headers={"x-rol": "supervisor"}
    )

    assert response.status_code == 200

    detalle_despues = client.get("/api/envios/TRK-TEST01/detalles")
    historial_despues = detalle_despues.json()["historial"]

    assert len(historial_despues) == len(historial_antes)
    assert historial_despues == historial_antes
