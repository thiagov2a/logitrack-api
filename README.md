# LogiTrack - API (Grupo 10)

**Universidad Nacional de General Sarmiento (UNGS)**
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software

---

## Descripción del Proyecto
Este repositorio contiene el código fuente del MVP (Mínimo Producto Viable) de LogiTrack, correspondiente al TP Inicial. 

En esta iteración (Sprint 1), desarrollamos una Mock API que simula el registro, seguimiento y cambio de estados de envíos logísticos. Esta arquitectura funciona como el "Paquete Base" sobre el cual, en futuras etapas, se integrará el modelo de Machine Learning para predecir la prioridad de los envíos.

## Stack Tecnológico
* **Lenguaje:** Python
* **Framework Web:** FastAPI
* **Servidor:** Uvicorn
* **Modelado de Datos:** Pydantic
* **Control de Versiones y CI:** Git / GitHub Actions

## Estructura del Repositorio
El proyecto sigue una arquitectura separada por responsabilidades para evitar importaciones circulares:

```text
/
├── docs/           # Documentación formal (ADRs, NFRs, Análisis Ley 25.326)
├── models/         # Entidades de dominio (Envio, Cliente, Tracking, Enums)
├── routers/        # Controladores y endpoints de la API
└── main.py         # Punto de entrada de la aplicación
