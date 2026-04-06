from fastapi import APIRouter, HTTPException, Query, Header, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from src.models.envio import Envio, Dimensiones
from src.models.cliente import Cliente
from src.models.tracking import EventoTracking
from src.models.enums import EstadoEnvio, PrioridadEnvio
from src.ml.predictor import predecir_prioridad
import uuid
import io
import csv

router = APIRouter(prefix="/api/envios", tags=["Envios"])


# --- Modelos de request ---

class CambioPrioridadRequest(BaseModel):
    nueva_prioridad: PrioridadEnvio


class CambioEstadoRequest(BaseModel):
    nuevo_estado: EstadoEnvio
    ubicacion: str
    observaciones: Optional[str] = None


class CambioEstadoMasivoRequest(BaseModel):
    tracking_ids: List[str]
    nuevo_estado: EstadoEnvio
    ubicacion: str
    observaciones: Optional[str] = None


class RemitenteUpdate(BaseModel):
    dni: Optional[str] = None
    nombre: Optional[str] = None
    anonimizado: Optional[bool] = None


class EnvioUpdate(BaseModel):
    origen: Optional[str] = None
    destino: Optional[str] = None
    consentimiento: Optional[bool] = None
    remitente: Optional[RemitenteUpdate] = None


class ConfirmacionCancelacion(BaseModel):
    confirmar: bool


class ConfirmacionAnonimizacion(BaseModel):
    confirmar: bool


# --- Helpers ---

FLUJO_ESTADOS = [
    EstadoEnvio.INICIADO,
    EstadoEnvio.EN_SUCURSAL,
    EstadoEnvio.EN_TRANSITO,
    EstadoEnvio.ENTREGADO,
]

ESTADOS_TERMINALES = [
    EstadoEnvio.ENTREGADO,
    EstadoEnvio.CANCELADO,
]


def _estado_actual(envio: Envio) -> EstadoEnvio:
    if envio.historial:
        return envio.historial[-1].estado_actual
    return EstadoEnvio.INICIADO


def _buscar_envio(tracking_id: str) -> Envio:
    envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)
    if not envio:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontro ningun envio con el codigo {tracking_id}",
        )
    return envio


def _es_estado_terminal(estado: EstadoEnvio) -> bool:
    return estado in ESTADOS_TERMINALES


def _esta_finalizado(envio: Envio) -> bool:
    return _estado_actual(envio) in [EstadoEnvio.ENTREGADO, EstadoEnvio.CANCELADO]


def _cliente_tiene_datos(cliente) -> bool:
    if not cliente:
        return False

    return any([
        getattr(cliente, "dni", None),
        getattr(cliente, "nombre", None),
        getattr(cliente, "direccion", None),
    ])


# --- Datos semilla ---

def _crear_semilla(
    origen: str,
    destino: str,
    dni: str,
    nombre: str,
    estado: EstadoEnvio,
    peso: float = None,
    largo: float = None,
    ancho: float = None,
    alto: float = None
) -> Envio:

    dims = None
    if largo is not None and ancho is not None and alto is not None:
        dims = Dimensiones(largo_cm=largo, ancho_cm=ancho, alto_cm=alto)

    envio = Envio(
        trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
        origen=origen,
        destino=destino,
        peso_kg=peso,
        dimensiones=dims,
        remitente=Cliente(dni=dni, nombre=nombre),
        destinatario=Cliente(dni="00000000", nombre="Destinatario Ejemplo"),
    )

    envio.historial.append(
        EventoTracking(
            trackingId=envio.trackingId,
            estado_actual=EstadoEnvio.INICIADO,
            ubicacion=origen
        )
    )

    if estado != EstadoEnvio.INICIADO:
        envio.historial.append(
            EventoTracking(
                trackingId=envio.trackingId,
                estado_actual=estado,
                ubicacion=destino
            )
        )

    dims = envio.dimensiones
    pred = predecir_prioridad(
        peso_kg=envio.peso_kg,
        largo_cm=dims.largo_cm if dims else None,
        ancho_cm=dims.ancho_cm if dims else None,
        alto_cm=dims.alto_cm if dims else None,
    )
    envio.prioridad_ml = PrioridadEnvio(pred)

    return envio


mock_db_envios = [
    _crear_semilla("Buenos Aires", "Cordoba", "12345678", "Ana Gomez", EstadoEnvio.EN_TRANSITO,
                   peso=25.0, largo=80, ancho=60, alto=50),
    _crear_semilla("Rosario", "Mendoza", "87654321", "Luis Perez", EstadoEnvio.EN_SUCURSAL,
                   peso=8.0, largo=40, ancho=30, alto=25),
    _crear_semilla("La Plata", "Tucuman", "11223344", "Maria Lopez", EstadoEnvio.INICIADO,
                   peso=1.0, largo=10, ancho=10, alto=5),
]


# --- Endpoints ---

# US 08: Importar envios desde CSV
@router.post("/importar-csv", status_code=201)
async def importar_envios_csv(archivo: UploadFile = File(...)):
    """Importa envios masivamente desde un archivo CSV."""
    if not archivo.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV.")

    contenido = await archivo.read()
    texto = contenido.decode("utf-8")
    reader = csv.DictReader(io.StringIO(texto))

    campos_requeridos = {
        "origen", "destino", "remitente_dni", "remitente_nombre",
        "destinatario_dni", "destinatario_nombre",
    }
    if not campos_requeridos.issubset(set(reader.fieldnames or [])):
        raise HTTPException(
            status_code=400,
            detail=f"El CSV debe contener las columnas: {', '.join(campos_requeridos)}"
        )

    importados = []
    errores = []

    for i, fila in enumerate(reader, start=2):
        try:
            dims = None
            largo = fila.get("largo_cm", "").strip()
            ancho = fila.get("ancho_cm", "").strip()
            alto = fila.get("alto_cm", "").strip()
            if largo and ancho and alto:
                dims = Dimensiones(
                    largo_cm=float(largo),
                    ancho_cm=float(ancho),
                    alto_cm=float(alto)
                )

            peso = fila.get("peso_kg", "").strip()
            peso_kg = float(peso) if peso else None

            envio = Envio(
                trackingId=f"TRK-{uuid.uuid4().hex[:8].upper()}",
                origen=fila["origen"].strip(),
                destino=fila["destino"].strip(),
                peso_kg=peso_kg,
                dimensiones=dims,
                consentimiento=True,
                remitente=Cliente(
                    dni=fila["remitente_dni"].strip(),
                    nombre=fila["remitente_nombre"].strip()
                ),
                destinatario=Cliente(
                    dni=fila["destinatario_dni"].strip(),
                    nombre=fila["destinatario_nombre"].strip()
                ),
            )

            pred = predecir_prioridad(
                peso_kg=peso_kg,
                largo_cm=dims.largo_cm if dims else None,
                ancho_cm=dims.ancho_cm if dims else None,
                alto_cm=dims.alto_cm if dims else None,
            )
            envio.prioridad_ml = PrioridadEnvio(pred)

            envio.historial.append(EventoTracking(
                trackingId=envio.trackingId,
                estado_actual=EstadoEnvio.INICIADO,
                ubicacion=envio.origen,
                observaciones="Envio importado desde CSV.",
            ))

            mock_db_envios.append(envio)
            importados.append(envio.trackingId)

        except Exception as e:
            errores.append({"fila": i, "error": str(e)})

    return {
        "mensaje": f"{len(importados)} envio(s) importado(s) correctamente.",
        "importados": importados,
        "errores": errores,
    }


# US-07/25: Registrar envio y asignarle una prioridad
@router.post("/", status_code=201)
def registrar_envio(nuevo_envio: Envio):
    """US-07: Registro individual de envio con Tracking ID autogenerado."""
    if not getattr(nuevo_envio, "consentimiento", False):
        raise HTTPException(
            status_code=400,
            detail="Debe aceptar las politicas de privacidad para registrar el envío."
        )

    nuevo_envio.trackingId = f"TRK-{uuid.uuid4().hex[:8].upper()}"

    dims = nuevo_envio.dimensiones
    pred = predecir_prioridad(
        peso_kg=nuevo_envio.peso_kg,
        largo_cm=dims.largo_cm if dims else None,
        ancho_cm=dims.ancho_cm if dims else None,
        alto_cm=dims.alto_cm if dims else None,
    )
    nuevo_envio.prioridad_ml = PrioridadEnvio(pred)

    nuevo_envio.historial.append(EventoTracking(
        trackingId=nuevo_envio.trackingId,
        estado_actual=EstadoEnvio.INICIADO,
        ubicacion=nuevo_envio.origen,
        observaciones="Envio registrado en el sistema por el Operador.",
    ))
    mock_db_envios.append(nuevo_envio)
    return {
        "mensaje": "Envio registrado con exito",
        "trackingId": nuevo_envio.trackingId,
        "envio": nuevo_envio
    }


# US-11 / US-14 / US-15: Listar envios con filtros opcionales
@router.get("/")
def listar_envios(
    estados: Optional[List[EstadoEnvio]] = Query(None),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    """
    US-11: Listado general de envios.
    US-14: Filtrar por uno o varios estados. Ejemplo: ?estados=INICIADO&estados=EN_SUCURSAL
    US-15: Filtrar por rango de fecha de creacion. Ejemplo: ?fecha_desde=2024-01-01&fecha_hasta=2024-12-31
    """
    resultado = list(mock_db_envios)

    if estados:
        resultado = [e for e in resultado if _estado_actual(e) in estados]

    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="fecha_desde no puede ser mayor a fecha_hasta."
        )

    if fecha_desde:
        resultado = [e for e in resultado if e.fechaCreacion >= fecha_desde]

    if fecha_hasta:
        resultado = [e for e in resultado if e.fechaCreacion <= fecha_hasta]

    return sorted(resultado, key=lambda e: e.fechaCreacion.replace(tzinfo=None))


# US-17: Cambio de estado masivo (solo Supervisor)
@router.patch("/estado-masivo")
def cambiar_estado_masivo(
    body: CambioEstadoMasivoRequest,
    x_rol: str = Header(...)
):
    """US-17: Permite cambiar el estado de multiples envios seleccionados. Solo accesible para Supervisor."""
    if x_rol.lower() != "supervisor":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requiere rol Supervisor."
        )

    if not body.tracking_ids:
        raise HTTPException(
            status_code=400,
            detail="Debe seleccionar al menos un envio."
        )

    actualizados = []
    no_encontrados = []
    omitidos = []

    for tracking_id in body.tracking_ids:
        envio = next((e for e in mock_db_envios if e.trackingId == tracking_id), None)

        if not envio:
            no_encontrados.append(tracking_id)
            continue

        estado_actual = _estado_actual(envio)

        if _es_estado_terminal(estado_actual):
            omitidos.append({
                "trackingId": tracking_id,
                "motivo": f"El envio esta en estado terminal ({estado_actual.value}) y no puede cambiar de estado.",
            })
            continue

        envio.historial.append(EventoTracking(
            trackingId=tracking_id,
            estado_actual=body.nuevo_estado,
            ubicacion=body.ubicacion,
            observaciones=body.observaciones or "Cambio masivo realizado por Supervisor.",
        ))
        actualizados.append(tracking_id)

    return {
        "mensaje": "Cambio masivo procesado con exito",
        "nuevo_estado": body.nuevo_estado,
        "actualizados": actualizados,
        "no_encontrados": no_encontrados,
        "omitidos": omitidos,
        "total_actualizados": len(actualizados),
    }


# US-12: Buscar envio por Tracking ID
@router.get("/{tracking_id}")
def buscar_resumen_envio(tracking_id: str):
    """US-12: Devuelve informacion principal y estado actual del envio."""
    envio = _buscar_envio(tracking_id)
    return {
        "trackingId": envio.trackingId,
        "origen": envio.origen,
        "destino": envio.destino,
        "estado_actual": _estado_actual(envio),
    }


# US-13: Detalle completo con historial
@router.get("/{tracking_id}/detalles")
def buscar_detalle_envio(tracking_id: str):
    """US-13: Devuelve toda la informacion del envio incluyendo historial de eventos."""
    return _buscar_envio(tracking_id)


# US-19: Historial de estados
@router.get("/{tracking_id}/historial_estado")
def historial_envio(tracking_id: str):
    """US-19: Devuelve el historial completo de eventos del envio."""
    return _buscar_envio(tracking_id).historial


# US-08 / US-16 / US-18 / US-20: Cambio de estado (solo Supervisor)
@router.patch("/{tracking_id}/estado")
def cambiar_estado_envio(
    tracking_id: str,
    body: CambioEstadoRequest,
    x_rol: str = Header(...)
):
    """US-08/16/18/20: Cambia el estado del envio. Solo accesible para Supervisor."""
    if x_rol.lower() != "supervisor":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requiere rol Supervisor."
        )

    envio = _buscar_envio(tracking_id)
    estado_actual = _estado_actual(envio)

    if _es_estado_terminal(estado_actual):
        raise HTTPException(
            status_code=400,
            detail=f"El envio esta en estado terminal ({estado_actual.value}) y no puede cambiar de estado."
        )

    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=body.nuevo_estado,
        ubicacion=body.ubicacion,
        observaciones=body.observaciones,
    ))

    return {
        "mensaje": "Estado actualizado con exito",
        "trackingId": tracking_id,
        "nuevo_estado": body.nuevo_estado
    }


# Cambio de prioridad manual (solo Supervisor)
@router.patch("/{tracking_id}/prioridad")
def cambiar_prioridad(tracking_id: str, body: CambioPrioridadRequest, x_rol: str = Header(...)):
    """Permite al Supervisor sobreescribir la prioridad asignada por el modelo ML."""
    if x_rol.lower() != "supervisor":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol Supervisor.")
    envio = _buscar_envio(tracking_id)
    envio.prioridad_ml = body.nueva_prioridad
    return {
        "mensaje": "Prioridad actualizada con exito",
        "trackingId": tracking_id,
        "prioridad_ml": body.nueva_prioridad
    }


# US-09: Editar datos del envio en estado INICIADO
@router.patch("/{tracking_id}")
def editar_envio(tracking_id: str, datos: EnvioUpdate):
    """US-09: Permite editar datos del envio solo si esta en estado INICIADO."""
    envio = _buscar_envio(tracking_id)

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede editar un envio en estado INICIADO."
        )

    if datos.origen is not None:
        envio.origen = datos.origen
    if datos.destino is not None:
        envio.destino = datos.destino
    if datos.consentimiento is not None:
        envio.consentimiento = datos.consentimiento
    if datos.remitente is not None:
        if datos.remitente.dni is not None:
            envio.remitente.dni = datos.remitente.dni
        if datos.remitente.nombre is not None:
            envio.remitente.nombre = datos.remitente.nombre
        if datos.remitente.anonimizado is not None:
            envio.remitente.anonimizado = datos.remitente.anonimizado

    return {"mensaje": "Envio editado con exito", "envio": envio}


# US-10: Cancelar envio en estado INICIADO
@router.patch("/{tracking_id}/cancelar")
def cancelar_envio(tracking_id: str, confirmacion: ConfirmacionCancelacion):
    """US-10: Cancela el envio si esta en estado INICIADO y se confirma la accion."""
    envio = _buscar_envio(tracking_id)

    if not confirmacion.confirmar:
        raise HTTPException(
            status_code=400,
            detail="La cancelacion debe ser confirmada explicitamente."
        )

    if _estado_actual(envio) != EstadoEnvio.INICIADO:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede cancelar un envio en estado INICIADO."
        )

    envio.historial.append(EventoTracking(
        trackingId=tracking_id,
        estado_actual=EstadoEnvio.CANCELADO,
        ubicacion=envio.origen,
        observaciones="Envio cancelado por el Operador.",
    ))

    return {"mensaje": "Envio cancelado con exito", "envio": envio}


# US-22: Anonimización de datos (Derecho al Olvido)
@router.patch("/{tracking_id}/anonimizar")
def anonimizar_envio(
    tracking_id: str,
    confirmacion: ConfirmacionAnonimizacion,
    x_rol: str = Header(...)
):
    """US-22: Anonimiza irreversiblemente los datos personales de un envio finalizado. Solo Supervisor."""
    if x_rol.lower() != "supervisor":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requiere rol Supervisor."
        )

    if not confirmacion.confirmar:
        raise HTTPException(
            status_code=400,
            detail="La anonimización debe ser confirmada explícitamente."
        )

    envio = _buscar_envio(tracking_id)

    if not _esta_finalizado(envio):
        raise HTTPException(
            status_code=400,
            detail="Solo se puede anonimizar un envio finalizado."
        )

    if envio.remitente:
        envio.remitente.nombre = "***"
        envio.remitente.dni = "***"
        if hasattr(envio.remitente, "direccion"):
            envio.remitente.direccion = "***"
        if hasattr(envio.remitente, "anonimizado"):
            envio.remitente.anonimizado = True

    if getattr(envio, "destinatario", None):
        envio.destinatario.nombre = "***"
        envio.destinatario.dni = "***"
        if hasattr(envio.destinatario, "direccion"):
            envio.destinatario.direccion = "***"
        if hasattr(envio.destinatario, "anonimizado"):
            envio.destinatario.anonimizado = True

    return {
        "mensaje": "Datos personales anonimizados con exito",
        "trackingId": tracking_id,
        "envio": envio
    }


# US-23: Exportación de datos de cliente (Derecho de Acceso)
@router.get("/{tracking_id}/exportar-cliente")
def exportar_datos_cliente(
    tracking_id: str,
    tipo_cliente: str = Query(..., description="remitente o destinatario"),
    x_rol: str = Header(...)
):
    """US-23: Exporta en CSV los datos personales almacenados de un cliente. Solo Administrador."""
    if x_rol.lower() != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: se requiere rol Administrador."
        )

    envio = _buscar_envio(tracking_id)

    tipo_normalizado = tipo_cliente.lower()
    if tipo_normalizado not in ["remitente", "destinatario"]:
        raise HTTPException(
            status_code=400,
            detail="tipo_cliente debe ser 'remitente' o 'destinatario'."
        )

    cliente = envio.remitente if tipo_normalizado == "remitente" else envio.destinatario

    if not _cliente_tiene_datos(cliente):
        raise HTTPException(
            status_code=404,
            detail=f"El envio no tiene {tipo_normalizado} registrado."
        )

    output = io.StringIO()
    writer = csv.writer(
        output,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_ALL,
        lineterminator="\n"
    )

    writer.writerow([
        "tracking_id",
        "tipo_cliente",
        "nombre",
        "dni",
        "direccion",
        "anonimizado"
    ])

    writer.writerow([
        envio.trackingId,
        tipo_normalizado,
        getattr(cliente, "nombre", "") or "",
        getattr(cliente, "dni", "") or "",
        getattr(cliente, "direccion", "") or "",
        str(getattr(cliente, "anonimizado", False)),
    ])

    output.seek(0)

    filename = f"{tracking_id}_{tipo_normalizado}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
