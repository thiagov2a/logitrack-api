# Matriz de Trazabilidad — LogiTrack

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software  
**Sprint:** 1

---

## Historia ↔ Caso de Prueba ↔ Commit / PR

| ID | Historia de Usuario | Caso de Prueba | Archivo | Commit / PR |
|---|---|---|---|---|
| US-07 | Como Operador, quiero registrar un envío para generar el Tracking ID y comenzar el seguimiento | `test_registrar_envio_genera_tracking_id` | `tests/test_envios.py` | PR #1 — `feat/US-07-registro-envio` (`08c3aee`) |
| US-08 | Como Supervisor, quiero cambiar el estado del envío registrando fecha/hora de auditoría | `test_cambiar_estado_envio` | `tests/test_envios.py` | `feat/semana3-ci-pipeline` (`78afafd`) |
| US-08 | Como Supervisor, quiero recibir error al cambiar estado de un envío inexistente | `test_cambiar_estado_envio_inexistente_retorna_404` | `tests/test_envios.py` | `feat/semana3-ci-pipeline` (`78afafd`) |
| US-11 | Como Operador, quiero listar todos los envíos registrados en el sistema | `test_listar_envios_retorna_semilla` | `tests/test_envios.py` | PR #2 — `feat/US-11-lista-de-envios` (`6d77f67`) |
| US-12 | Como Operador, quiero buscar un envío por Tracking ID para acceder rápidamente a su estado | `test_buscar_envio_existente` | `tests/test_envios.py` | PR #3 — `feat/US-12-busqueda-de-envio-por-tracking-ID` (`282fbaa`) |
| US-12 | Como Operador, quiero recibir un error claro al buscar un Tracking ID inexistente | `test_buscar_envio_inexistente_retorna_404` | `tests/test_envios.py` | PR #3 — `feat/US-12-busqueda-de-envio-por-tracking-ID` (`282fbaa`) |
| US-13 | Como Operador, quiero ver el detalle completo de un envío incluyendo su historial de estados | `test_detalle_envio_incluye_historial` | `tests/test_envios.py` | PR #4 — `feat/US-13-visualizacion-de-detalle-completo-de-envio` (`1f78e4c`) |
| US-16/18/20 | Como Supervisor, quiero avanzar automáticamente el estado del envío al siguiente en el flujo | — | `routers/envios.py` | PR #6 — `feat/us-16-cambiar-estado-individual-de-envío` (`e5b83c7`) |
| US-19 | Como Operador, quiero ver el historial completo de estados de un envío | — | `routers/envios.py` | PR #7 — `feat/us-19-historial-de-estados-en-detalle` (`711fe5f`) |

---

## Cobertura por Historia

| ID | Historia | Tests | Estado |
|---|---|---|---|
| US-07 | Registro de envío | 1 | ✅ Cubierta |
| US-08 | Cambio de estado | 2 | ✅ Cubierta |
| US-11 | Listado de envíos | 1 | ✅ Cubierta |
| US-12 | Búsqueda por Tracking ID | 2 | ✅ Cubierta |
| US-13 | Detalle completo | 1 | ✅ Cubierta |
| US-16/18/20 | Avanzar estado automáticamente | — | ⚠️ Sin test automatizado |
| US-19 | Historial de estados | — | ⚠️ Sin test automatizado |
