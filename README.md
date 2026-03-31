# LogiTrack (SFGLD) — Grupo 10

**Universidad Nacional de General Sarmiento (UNGS)**  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software

![CI](https://github.com/thiagov2a/logitrack-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)
![Tests](https://img.shields.io/badge/Tests-22%20passed-brightgreen)
![Linter](https://img.shields.io/badge/Linter-Flake8-yellow)
[![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7)](https://logitrack-api-6nj5.onrender.com/)

---

## Descripción

LogiTrack es el **Paquete Base** del Sistema Federal de Gestión de Logística y Distribución (SFGLD). En esta iteración (Sprint 2) se desarrolló una Mock API REST con interfaz web que simula el registro, seguimiento y cambio de estados de envíos logísticos. En futuras etapas se integrará un modelo de Machine Learning para predecir la prioridad de los envíos y una base de datos PostgreSQL.

## Stack Tecnológico

| Herramienta | Versión | Uso |
|---|---|---|
| Python | 3.11 | Lenguaje principal |
| FastAPI | 0.135 | Framework web / API REST |
| Uvicorn | 0.42 | Servidor ASGI |
| Pydantic | 2.x | Modelado y validación de datos |
| Jinja2 | 3.x | Templates HTML |
| Tailwind CSS | CDN | Estilos de la interfaz web |
| Pytest + HTTPX | — | Testing automatizado |
| Flake8 | — | Linter |
| GitHub Actions | — | Pipeline CI/CD |

## Estructura del Repositorio

```
/
├── .github/
│   └── workflows/
│       └── ci.yml          # Pipeline de CI (linter + tests)
├── docs/
│   ├── TRAZABILIDAD.md     # Matriz Historia ↔ Test ↔ Commit
│   ├── ADRs.md             # Decisiones de arquitectura
│   └── NFRs.md             # Atributos de calidad
├── src/
│   ├── models/             # Entidades de dominio
│   │   ├── envio.py
│   │   ├── cliente.py
│   │   ├── tracking.py
│   │   └── enums.py
│   └── routers/            # Endpoints y vistas
│       ├── envios.py       # API REST
│       └── views.py        # Vistas HTML
├── templates/              # Templates Jinja2
│   ├── base.html
│   ├── envios.html
│   ├── detalle.html
│   └── nuevo_envio.html
├── tests/
│   └── test_envios.py      # 22 tests automatizados
├── main.py                 # Punto de entrada
├── CONTRIBUTING.md         # Guía de contribución
└── requirements.txt        # Dependencias
```

## Instalación y ejecución

```bash
git clone https://github.com/thiagov2a/logitrack-api.git
cd logitrack-api
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

| URL | Descripción |
|---|---|
| `http://127.0.0.1:8000` | Interfaz web |
| `http://127.0.0.1:8000/docs` | Swagger / OpenAPI |
| `http://127.0.0.1:8000/redoc` | ReDoc |

## Interfaz Web

La aplicación incluye una interfaz web con selector de rol simulado:

- `http://127.0.0.1:8000/?rol=operador` — Vista de Operador
- `http://127.0.0.1:8000/?rol=supervisor` — Vista de Supervisor (incluye panel de cambio de estado)

## API REST — Endpoints

| Método | Ruta | Descripción | Rol | US |
|---|---|---|---|---|
| `POST` | `/api/envios/` | Registrar nuevo envío | Ambos | US-07 |
| `GET` | `/api/envios/` | Listar envíos con filtros opcionales | Ambos | US-11/14/15 |
| `GET` | `/api/envios/{tracking_id}` | Buscar envío por Tracking ID | Ambos | US-12 |
| `GET` | `/api/envios/{tracking_id}/detalles` | Detalle completo con historial | Ambos | US-13 |
| `GET` | `/api/envios/{tracking_id}/historial_estado` | Historial de estados | Ambos | US-19 |
| `PATCH` | `/api/envios/{tracking_id}` | Editar datos en estado INICIADO | Operador | US-09 |
| `PATCH` | `/api/envios/{tracking_id}/cancelar` | Cancelar envío en estado INICIADO | Operador | US-10 |
| `PATCH` | `/api/envios/{tracking_id}/estado` | Cambiar estado | Supervisor | US-08/16/18/20 |

### Filtros disponibles en `GET /api/envios/`

```
?estados=INICIADO
?estados=INICIADO&estados=EN_SUCURSAL
?fecha_desde=2026-01-01T00:00:00
?fecha_hasta=2026-12-31T23:59:59
```

## Roles

| Rol | Header API | Permisos |
|---|---|---|
| Operador | `X-Rol: operador` | Registrar, listar, buscar, editar, cancelar |
| Supervisor | `X-Rol: supervisor` | Todo lo anterior + cambiar estado |

## Estados del envío

```
INICIADO → EN_SUCURSAL → EN_TRANSITO → ENTREGADO
                                    ↘
                                  CANCELADO (solo desde INICIADO)
```

## Ejemplo de uso

**Registrar un envío:**
```bash
curl -X POST http://127.0.0.1:8000/api/envios/ \
  -H "Content-Type: application/json" \
  -d '{
    "origen": "Buenos Aires",
    "destino": "Córdoba",
    "remitente": {"dni": "12345678", "nombre": "Juan Pérez"},
    "destinatario": {"dni": "87654321", "nombre": "María López"}
  }'
```

**Cambiar estado (Supervisor):**
```bash
curl -X PATCH http://127.0.0.1:8000/api/envios/TRK-XXXXXXXX/estado \
  -H "Content-Type: application/json" \
  -H "X-Rol: supervisor" \
  -d '{"nuevo_estado": "EN_TRANSITO", "ubicacion": "Córdoba", "observaciones": "En camino"}'
```

## Tests

```bash
pytest tests/ -v
```

22 tests automatizados cubriendo todas las historias de usuario implementadas. Ver `docs/TRAZABILIDAD.md` para el detalle completo.

## Documentación adicional

| Documento | Descripción |
|---|---|
| `docs/TRAZABILIDAD.md` | Matriz Historia ↔ Caso de Prueba ↔ Commit/PR |
| `docs/ADRs.md` | Decisiones de arquitectura (ADR-001 a ADR-003) |
| `docs/NFRs.md` | Atributos de calidad |
| [Plan de Pruebas](https://docs.google.com/spreadsheets/d/1v310kejrffdqwqZR1RJRPvTJB3oT0CWtliUTe_sKkAk/edit?gid=0#gid=0) | Plan de pruebas en formato Given/When/Then |
| [Registro de Riesgos](https://docs.google.com/spreadsheets/d/1v310kejrffdqwqZR1RJRPvTJB3oT0CWtliUTe_sKkAk/edit?gid=115120055#gid=115120055) | Matriz de riesgos con probabilidad, impacto y respuesta |
| `CONTRIBUTING.md` | Guía de contribución y flujo de trabajo |

## Equipo de Desarrollo

| Nombre | DNI | Rol |
|---|---|---|
| Mauricio Santiago Quevedo | 46.340.138 | Desarrollador |
| Pablo Ariel Rodriguez | 39.109.268 | Desarrollador |
| Thiago Joel Vildosa | 45.815.384 | Desarrollador |
