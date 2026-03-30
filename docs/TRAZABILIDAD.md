# Matriz de Trazabilidad — LogiTrack

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software  
**Sprint:** 1

---

## Historia ↔ Caso de Prueba ↔ Commit / PR

| ID | Historia de Usuario | Caso de Prueba | Archivo | Commit / PR |
|---|---|---|---|---|
| US-07 | Como Operador, quiero registrar un envío para generar el Tracking ID y comenzar el seguimiento | `test_registrar_envio_genera_tracking_id` | `tests/test_envios.py` | PR #1 — `feat/US-07-registro-envio` (`08c3aee`) |
| US-08 | Como Supervisor, quiero cambiar el estado del envío registrando fecha/hora de auditoría | `test_cambiar_estado_envio` | `tests/test_envios.py` | `feat/roles-operador-supervisor` |
| US-08 | Como Supervisor, quiero recibir error al cambiar estado de un envío inexistente | `test_cambiar_estado_envio_inexistente_retorna_404` | `tests/test_envios.py` | `feat/roles-operador-supervisor` |
| US-08 | Como Operador, quiero recibir error 403 al intentar cambiar el estado | `test_cambiar_estado_con_rol_operador_retorna_403` | `tests/test_envios.py` | `feat/roles-operador-supervisor` |
| US-08 | Como Supervisor, no debo poder cambiar el estado de un envío cancelado | `test_cambiar_estado_envio_cancelado_retorna_400` | `tests/test_envios.py` | `feat/roles-operador-supervisor` |
| US-09 | Como Operador, quiero editar datos del envío solo si está en estado INICIADO | `test_editar_envio_en_estado_iniciado` | `tests/test_envios.py` | PR #14 — `feat/US-09-editar-datos-envio-estado-inicial` |
| US-09 | Como Operador, no debo poder editar un envío fuera del estado INICIADO | `test_editar_envio_fuera_de_estado_iniciado_retorna_400` | `tests/test_envios.py` | PR #14 — `feat/US-09-editar-datos-envio-estado-inicial` |
| US-10 | Como Operador, quiero cancelar un envío en estado INICIADO con confirmación | `test_cancelar_envio_en_estado_iniciado` | `tests/test_envios.py` | PR #15 — `feat/us-10-cancelar-envio-ingresado` |
| US-10 | Como Operador, no debo poder cancelar sin confirmar la acción | `test_cancelar_envio_sin_confirmacion_retorna_400` | `tests/test_envios.py` | PR #15 — `feat/us-10-cancelar-envio-ingresado` |
| US-10 | Como Operador, no debo poder cancelar un envío fuera del estado INICIADO | `test_cancelar_envio_fuera_de_estado_iniciado_retorna_400` | `tests/test_envios.py` | PR #15 — `feat/us-10-cancelar-envio-ingresado` |
| US-11 | Como Operador, quiero listar todos los envíos ordenados por fecha de creación | `test_listar_envios_retorna_semilla` `test_listar_envios_ordenados_por_fecha` | `tests/test_envios.py` | PR #2 — `feat/US-11-lista-de-envios` (`6d77f67`) |
| US-12 | Como Operador, quiero buscar un envío por Tracking ID | `test_buscar_envio_existente` | `tests/test_envios.py` | PR #3 — `feat/US-12-busqueda-de-envio-por-tracking-ID` (`282fbaa`) |
| US-12 | Como Operador, quiero recibir error al buscar un Tracking ID inexistente | `test_buscar_envio_inexistente_retorna_404` | `tests/test_envios.py` | PR #3 — `feat/US-12-busqueda-de-envio-por-tracking-ID` (`282fbaa`) |
| US-13 | Como Operador, quiero ver el detalle completo del envío incluyendo remitente, destinatario e historial | `test_detalle_envio_incluye_historial` `test_detalle_envio_incluye_destinatario` | `tests/test_envios.py` | PR #4 — `feat/US-13-visualizacion-de-detalle-completo-de-envio` |
| US-14 | Como Operador, quiero filtrar envíos por estado actual | `test_filtrar_envios_por_estado` | `tests/test_envios.py` | PR #16 — `feat/us-14-filtrar-envios-por-estado` |
| US-15 | Como Operador, quiero filtrar envíos por rango de fecha de creación | `test_filtrar_envios_por_fecha_desde` `test_filtrar_envios_fecha_futura_retorna_vacio` | `tests/test_envios.py` | PR #12 — `feat/us-15-filtrar-envios-por-rango-fecha` |
| US-15 | Como Operador, quiero recibir error si fecha_desde es mayor a fecha_hasta | `test_filtrar_envios_fecha_desde_mayor_hasta_retorna_400` | `tests/test_envios.py` | `feat/roles-operador-supervisor` |
| US-16/18/20 | Como Supervisor, quiero cambiar el estado siguiendo el flujo lógico con auditoría y observaciones | `test_cambiar_estado_envio` | `tests/test_envios.py` | PR #6 — `feat/us-16-cambiar-estado-individual-de-envío` (`e5b83c7`) |
| US-19 | Como Operador, quiero ver el historial completo de estados de un envío | `test_historial_envio_retorna_lista` `test_historial_envio_inexistente_retorna_404` | `tests/test_envios.py` | PR #7 — `feat/us-19-historial-de-estados-en-detalle` (`711fe5f`) |

---

## Cobertura por Historia

| ID | Historia | Tests | Estado |
|---|---|---|---|
| US-07 | Registro de envío | 1 | ✅ Cubierta |
| US-08 | Cambio de estado (solo Supervisor) | 4 | ✅ Cubierta |
| US-09 | Editar datos en estado INICIADO | 2 | ✅ Cubierta |
| US-10 | Cancelar envío | 3 | ✅ Cubierta |
| US-11 | Listado de envíos ordenado | 2 | ✅ Cubierta |
| US-12 | Búsqueda por Tracking ID | 2 | ✅ Cubierta |
| US-13 | Detalle completo con destinatario e historial | 2 | ✅ Cubierta |
| US-14 | Filtrar por estado | 1 | ✅ Cubierta |
| US-15 | Filtrar por rango de fecha con validación | 3 | ✅ Cubierta |
| US-16/18/20 | Cambio de estado con auditoría y observaciones | 1 | ✅ Cubierta |
| US-19 | Historial de estados | 2 | ✅ Cubierta |
