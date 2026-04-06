# LogiTrack (SFGLD) — Grupo 10

**Universidad Nacional de General Sarmiento (UNGS)**  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software

![CI](https://github.com/thiagov2a/logitrack-api/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)
![Tests](https://img.shields.io/badge/Tests-86%20passed-brightgreen)
![Linter](https://img.shields.io/badge/Linter-Flake8-yellow)
[![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7)](https://logitrack-api-6nj5.onrender.com/)

---

## Descripción

LogiTrack es el **Paquete Base** del Sistema Federal de Gestión de Logística y Distribución (SFGLD). En esta iteración (Sprint 3) se desarrolló una Mock API REST con interfaz web que simula el registro, seguimiento y cambio de estados de envíos logísticos, con autenticación por sesión, roles diferenciados y un modelo de Machine Learning para predecir la prioridad de los envíos.

## Stack Tecnológico

| Herramienta | Versión | Uso |
|---|---|---|
| Python | 3.11 | Lenguaje principal |
| FastAPI | 0.135 | Framework web / API REST |
| Uvicorn | 0.42 | Servidor ASGI |
| Pydantic | 2.x | Modelado y validación de datos |
| Jinja2 | 3.x | Templates HTML |
| Tailwind CSS | CDN | Estilos de la interfaz web |
| scikit-learn | — | Modelo de ML (Random Forest) |
| pandas | — | Procesamiento de datos para ML |
| Pytest + HTTPX | — | Testing automatizado |
| Flake8 | — | Linter |
| GitHub Actions | — | Pipeline CI/CD |

## Estructura del Repositorio

```
/
├── .github/
│   └── workflows/
│       └── ci.yml              # Pipeline de CI (linter + tests)
├── analysis/
│   ├── dataset_envios_ml.csv   # Dataset de entrenamiento
│   └── entrenar_modelo.py      # Script de entrenamiento
├── docs/
│   ├── TRAZABILIDAD.md         # Matriz Historia ↔ Test ↔ Commit
│   ├── ADRs.md                 # Decisiones de arquitectura
│   └── NFRs.md                 # Atributos de calidad
├── src/
│   ├── ml/
│   │   ├── predictor.py        # Módulo de predicción de prioridad
│   │   ├── imputer.pkl             # Imputer serializado
│   │   └── modelo_prioridad.pkl    # Modelo Random Forest serializado
│   ├── models/
│   │   ├── envio.py
│   │   ├── cliente.py
│   │   ├── tracking.py
│   │   ├── enums.py
│   │   └── usuario.py
│   └── routers/
│       ├── auth.py             # Login / Logout
│       ├── envios.py           # API REST
│       └── views.py            # Vistas HTML
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── envios.html
│   ├── detalle.html
│   ├── nuevo_envio.html
│   ├── usuarios.html
│   ├── nuevo_usuario.html
│   └── editar_usuario.html
├── tests/
│   ├── conftest.py             # Fixtures compartidas
│   ├── test_envios.py          # Tests de envíos (US-07 a US-25)
│   └── test_usuarios.py        # Tests de usuarios (US-01 a US-06)
├── main.py                     # Punto de entrada
├── CONTRIBUTING.md             # Guía de contribución
└── requirements.txt            # Dependencias
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
| `http://127.0.0.1:8000` | Interfaz web (redirige al login) |
| `http://127.0.0.1:8000/docs` | Swagger / OpenAPI |
| `http://127.0.0.1:8000/redoc` | ReDoc |

## Usuarios de prueba

| Email | Contraseña | Rol |
|---|---|---|
| `operador@logitrack.com` | `operador123` | Operador |
| `supervisor@logitrack.com` | `supervisor123` | Supervisor |
| `admin@logitrack.com` | `admin123` | Administrador |

## API REST — Endpoints

| Método | Ruta | Descripción | Rol | US |
|---|---|---|---|---|
| `POST` | `/api/envios/` | Registrar nuevo envío | Ambos | US-07 |
| `POST` | `/api/envios/importar-csv` | Importar envíos desde CSV | Ambos | US-08 |
| `GET` | `/api/envios/` | Listar envíos con filtros opcionales | Ambos | US-11/14/15 |
| `GET` | `/api/envios/{tracking_id}` | Buscar envío por Tracking ID | Ambos | US-12 |
| `GET` | `/api/envios/{tracking_id}/detalles` | Detalle completo con historial | Ambos | US-13 |
| `GET` | `/api/envios/{tracking_id}/historial_estado` | Historial de estados | Ambos | US-19 |
| `GET` | `/api/envios/{tracking_id}/exportar-cliente` | Exportar datos de cliente (CSV) | Administrador | US-23 |
| `PATCH` | `/api/envios/{tracking_id}` | Editar datos en estado INICIADO | Operador | US-09 |
| `PATCH` | `/api/envios/{tracking_id}/cancelar` | Cancelar envío en estado INICIADO | Operador | US-10 |
| `PATCH` | `/api/envios/{tracking_id}/estado` | Cambiar estado | Supervisor | US-08/16/18/20 |
| `PATCH` | `/api/envios/estado-masivo` | Cambio de estado masivo | Supervisor | US-17 |
| `PATCH` | `/api/envios/{tracking_id}/anonimizar` | Anonimizar datos personales | Supervisor | US-22 |
| `GET` | `/api/usuarios/` | Listar usuarios | Administrador | US-04 |
| `PATCH` | `/api/usuarios/{email}` | Editar nombre y rol de usuario | Administrador | US-05 |
| `PATCH` | `/api/usuarios/{email}/desactivar` | Baja lógica de usuario | Administrador | US-06 |
| `PATCH` | `/api/usuarios/{email}/activar` | Reactivar usuario | Administrador | US-06 |

## Roles

| Rol | Permisos |
|---|---|
| Operador | Registrar, listar, buscar, editar, cancelar |
| Supervisor | Todo lo anterior + cambiar estado, cambio masivo, anonimizar |
| Administrador | Todo lo anterior + exportar CSV, gestión de usuarios (alta, edición, baja lógica) |

## Estados del envío

```
INICIADO → EN_SUCURSAL → EN_TRANSITO → ENTREGADO
                                    ↘
                                  CANCELADO (solo desde INICIADO)
```

## Machine Learning

El modelo Random Forest predice automáticamente la prioridad del envío (ALTA/MEDIA/BAJA) al registrarlo, basándose en peso y dimensiones del paquete.

## Tests

```bash
pytest tests/ -v
```

86 tests automatizados cubriendo todas las historias de usuario implementadas.

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
