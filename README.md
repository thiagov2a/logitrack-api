# LogiTrack (SFGLD) - Grupo 10

**Universidad Nacional de General Sarmiento (UNGS)**  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software

![CI](https://github.com/thiagov2a/logitrack-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)

---

## Descripción

LogiTrack es el **Paquete Base** del Sistema Federal de Gestión de Logística y Distribución (SFGLD). En esta iteración (Sprint 2) se desarrolló una Mock API que simula el registro, seguimiento y cambio de estados de envíos logísticos. En futuras etapas se integrará un modelo de Machine Learning para predecir la prioridad de los envíos.

## Stack Tecnológico

| Herramienta | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| FastAPI | Framework web |
| Uvicorn | Servidor ASGI |
| Pydantic | Modelado y validación de datos |
| Pytest + HTTPX | Testing |
| Flake8 | Linter |
| GitHub Actions | CI/CD |

## Estructura del Repositorio

```
/
├── .github/workflows/  # Pipeline de CI
├── docs/               # Documentación (Trazabilidad, Plan de Pruebas, Ley 25.326)
├── src/
│   ├── models/         # Entidades de dominio (Envio, Cliente, Tracking, Enums)
│   └── routers/        # Endpoints de la API
├── tests/              # Tests automatizados
├── main.py             # Punto de entrada
├── CONTRIBUTING.md     # Guía de contribución
└── requirements.txt    # Dependencias
```

## Instalación y ejecución

```bash
git clone https://github.com/thiagov2a/logitrack-api.git
cd logitrack-api
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py
```

La API queda disponible en `http://127.0.0.1:8000`.  
Documentación interactiva (Swagger): `http://127.0.0.1:8000/docs`

## Endpoints

| Método | Ruta | Descripción | Rol | US |
|---|---|---|---|---|
| `POST` | `/api/envios/` | Registrar nuevo envío | Operador | US-07 |
| `GET` | `/api/envios/` | Listar envíos (filtros opcionales por estado y fecha) | Operador | US-11/14/15 |
| `GET` | `/api/envios/{tracking_id}` | Buscar envío por Tracking ID | Operador | US-12 |
| `GET` | `/api/envios/{tracking_id}/detalles` | Detalle completo con historial | Operador | US-13 |
| `GET` | `/api/envios/{tracking_id}/historial_estado` | Ver historial de estados | Operador | US-19 |
| `PATCH` | `/api/envios/{tracking_id}` | Editar datos en estado INICIADO | Operador | US-09 |
| `PATCH` | `/api/envios/{tracking_id}/cancelar` | Cancelar envío en estado INICIADO | Operador | US-10 |
| `PATCH` | `/api/envios/{tracking_id}/estado` | Cambiar estado (requiere `X-Rol: supervisor`) | Supervisor | US-08/16/18/20 |

## Roles

| Rol | Header | Permisos |
|---|---|---|
| Operador | `X-Rol: operador` | Registrar, listar, buscar, editar, cancelar |
| Supervisor | `X-Rol: supervisor` | Todo lo anterior + cambiar estado |

## Estados del envío

```
INICIADO → EN_SUCURSAL → EN_TRANSITO → ENTREGADO
```

## Tests

```bash
pytest tests/ -v
```

## Equipo de Desarrollo

- Mauricio Santiago **Quevedo** — 46.340.138
- Pablo Ariel **Rodriguez** — 39.109.268
- Thiago Joel **Vildosa** — 45.815.384
