# Guía de Contribución — LogiTrack

## Requisitos previos

- Python 3.11+
- Git
- pip

## Configuración del entorno

```bash
git clone https://github.com/thiagov2a/logitrack-api.git
cd logitrack-api
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload
```

## Arquitectura del proyecto

```
src/
├── models/       # Entidades de dominio (Pydantic)
│   ├── envio.py      → Modelo principal con historial
│   ├── cliente.py    → Remitente / Destinatario
│   ├── tracking.py   → Evento de tracking
│   └── enums.py      → EstadoEnvio, PrioridadEnvio
└── routers/
    ├── envios.py     → API REST (/api/envios/*)
    └── views.py      → Vistas HTML (/, /envios/*)
```

La API REST y las vistas HTML comparten la misma `mock_db_envios` en memoria. En futuras iteraciones se reemplazará por una base de datos PostgreSQL.

## Estrategia de ramas

| Rama | Uso |
|---|---|
| `main` | Código estable, solo se actualiza via PR |
| `feat/US-XX-descripcion` | Nueva funcionalidad |
| `fix/descripcion` | Corrección de bug |
| `refactor/descripcion` | Refactorización sin cambio funcional |
| `docs/descripcion` | Documentación |
| `test/descripcion` | Tests |

## Convención de commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: descripción corta
fix: descripción corta
refactor: descripción corta
docs: descripción corta
test: descripción corta
chore: descripción corta
```

Ejemplos:
```
feat: agrega endpoint de cambio de estado (US-08)
fix: corrige filtro de fechas en vistas
test: agrega tests para US-12
docs: actualiza matriz de trazabilidad
refactor: consolida US-11/14/15 en un solo endpoint
```

## Flujo de trabajo

1. Crear rama desde `main`:
   ```bash
   git checkout -b feat/US-XX-descripcion
   ```
2. Desarrollar y commitear con la convención de commits
3. Correr linter y tests antes de pushear:
   ```bash
   flake8 . --max-line-length=120 --exclude=venv
   pytest tests/ -v
   ```
4. Abrir Pull Request hacia `main`
5. El pipeline de CI debe pasar antes de hacer merge

## Agregar un nuevo endpoint

1. Definir el modelo de request en `src/routers/envios.py` si es necesario
2. Implementar el endpoint con su docstring referenciando la US
3. Agregar tests en `tests/test_envios.py`
4. Actualizar `docs/TRAZABILIDAD.md`
5. Actualizar el README si cambia la tabla de endpoints

## Agregar una nueva vista

1. Crear el template en `templates/`
2. Agregar la ruta en `src/routers/views.py`
3. Propagar el parámetro `rol` en todos los links

## Equipo

| Nombre | DNI |
|---|---|
| Mauricio Santiago **Quevedo** | 46.340.138 |
| Pablo Ariel **Rodriguez** | 39.109.268 |
| Thiago Joel **Vildosa** | 45.815.384 |
