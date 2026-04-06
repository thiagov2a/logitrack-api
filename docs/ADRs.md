# ADRs — Decisiones de Arquitectura

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software

---

## ADR-001: Elección de Python sobre Java para el desarrollo del modelo de ML

**Fecha:** 22 de marzo de 2026 | **Estado:** Aceptado

**Contexto:**  
Se debía decidir si mantener el stack conocido (Java) o migrar a Python para el núcleo de Machine Learning del sistema.

**Decisión:**  
Utilizar Python como lenguaje principal del proyecto.

**Justificación:**  
La especialización de Python en datos (Pandas, Scikit-Learn) supera las capacidades de Java para este fin. La falta de experiencia inicial se compensará con mayor eficiencia final.

**Consecuencias:**
- Positivas: Acceso a un ecosistema robusto, facilidad de prototipado rápido y adquisición de una competencia muy demandada en el mercado.
- Riesgos: Curva de aprendizaje lenta en el Sprint 1.
- Mitigación: Crash course inicial de 8 horas y uso de linters estrictos (Flake8).

---

## ADR-002: Selección del Algoritmo de Clasificación para Predicción de Prioridad

**Fecha:** 22 de marzo de 2026 | **Estado:** Implementado

**Contexto:**  
Se necesita clasificar automáticamente la prioridad de cada envío (ALTA / MEDIA / BAJA) al momento del registro, basándose en sus características físicas (peso y dimensiones). Se evaluaron Regresión Logística, Random Forest y Naïve Bayes.

**Decisión:**  
Utilizar Random Forest como algoritmo de clasificación.

**Justificación:**  
Captura naturalmente la no-linealidad entre peso/volumen y prioridad logística, maneja bien variables con valores faltantes mediante imputación de medianas, y permite generar gráficos de "Feature Importance" vitales para el negocio.

**Features utilizadas:** `peso_kg`, `largo_cm`, `ancho_cm`, `alto_cm`  
**Clases de salida:** `ALTA`, `MEDIA`, `BAJA`  
**Dataset:** `analysis/dataset_envios_ml.csv` con etiquetas asignadas manualmente por criterio de negocio.

**Consecuencias:**
- Positivas: Mayor precisión (F1-Score), robustez ante outliers y mitigación del overfitting.
- Riesgos: Mayor costo computacional y peso del modelo exportado.
- El modelo se exporta como `modelo_prioridad.pkl` + `imputer.pkl` y se carga una sola vez al iniciar la API.

---

## ADR-003: Elección de API y contrato de datos para el servicio de ML

**Fecha:** 22 de marzo de 2026 | **Estado:** Aprobado

**Contexto:**  
El servicio de ML será un microservicio REST. Se requiere un contrato estable para la integración con el frontend y otros servicios.

**Decisión:**  
FastAPI + OpenAPI 3.0 (Python).

**Justificación:**  
Aporta validación automática, tipado estricto y generación de documentación en tiempo real, alineándose con el ADR-001.

**Consecuencias:**
- Positivas: Evita errores en producción por contratos mal formados; facilita pruebas y futuras integraciones de UI.
- Seguridad: Permite fácil implementación de JWT y auditorías (Ley 25.326).
- Riesgos: Curva de aprendizaje de FastAPI.
- Mitigación: Ejemplos de payloads y documentación autogenerada en `/docs` y `/redoc`.
