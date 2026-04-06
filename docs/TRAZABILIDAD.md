# Matriz de Trazabilidad — LogiTrack

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software  
**Sprint:** 3

---

## Historia ↔ Caso de Prueba ↔ Commit / PR

| ID | Historia de Usuario | Caso de Prueba | Archivo | Commit / PR |
|---|---|---|---|---|
| US-01 | Como Usuario, quiero iniciar sesión para acceder a las funcionalidades de mi rol | `test_login_exitoso_redirige_al_inicio` `test_login_con_password_incorrecta_retorna_error` `test_login_con_usuario_no_registrado_retorna_error` | `tests/test_usuarios.py` | PR #29 — `feat/US-01-02-login-logout` |
| US-02 | Como Usuario, quiero cerrar sesión de forma segura | `test_logout_elimina_cookie_y_redirige_al_login` | `tests/test_usuarios.py` | PR #29 — `feat/US-01-02-login-logout` |
| US-03 | Como Administrador, quiero registrar un nuevo usuario | `test_crear_usuario_nuevo_exitosamente` `test_crear_usuario_con_email_duplicado_retorna_error` `test_crear_usuario_sin_ser_admin_redirige` | `tests/test_usuarios.py` | PR #35 — `feat/US-06-baja-logica-usuario` |
| US-04 | Como Administrador, quiero listar los usuarios del sistema | `test_listar_usuarios_api_como_administrador` `test_listar_usuarios_api_con_rol_invalido_retorna_403` | `tests/test_usuarios.py` | PR #35 — `feat/US-06-baja-logica-usuario` |
| US-05 | Como Administrador, quiero editar datos y rol de un usuario | `test_editar_usuario_api_actualiza_nombre_y_rol` `test_editar_usuario_api_con_rol_invalido_retorna_403` `test_editar_usuario_api_inexistente_retorna_404` `test_editar_usuario_api_nombre_muy_corto_retorna_400` `test_editar_usuario_api_rol_invalido_retorna_400` `test_editar_usuario_form_admin_actualiza_datos` `test_editar_usuario_form_sin_ser_admin_redirige` `test_editar_usuario_form_nombre_corto_muestra_error` | `tests/test_usuarios.py` | PR #35 — `feat/US-06-baja-logica-usuario` |
| US-06 | Como Administrador, quiero dar de baja lógica a un usuario | `test_desactivar_usuario_api_exitosamente` `test_desactivar_usuario_api_con_rol_invalido_retorna_403` `test_desactivar_usuario_api_inexistente_retorna_404` `test_desactivar_usuario_ya_inactivo_retorna_400` `test_usuario_inactivo_no_puede_iniciar_sesion` `test_activar_usuario_inactivo_exitosamente` `test_activar_usuario_ya_activo_retorna_400` `test_desactivar_usuario_form_admin_exitosamente` `test_desactivar_usuario_form_propio_usuario_no_permitido` `test_activar_usuario_form_admin_exitosamente` `test_desactivar_usuario_form_sin_ser_admin_redirige` | `tests/test_usuarios.py` | PR #35 — `feat/US-06-baja-logica-usuario` |
| US-07 | Como Operador, quiero registrar un envío para generar el Tracking ID | `test_registrar_envio_genera_tracking_id` | `tests/test_envios.py` | PR #1 — `feat/US-07-registro-envio` |
| US-08 | Como Supervisor, quiero cambiar el estado del envío registrando fecha/hora | `test_cambiar_estado_envio` `test_cambiar_estado_envio_inexistente_retorna_404` `test_cambiar_estado_con_rol_operador_retorna_403` `test_cambiar_estado_envio_cancelado_retorna_400` `test_no_permite_cambiar_estado_de_envio_entregado` | `tests/test_envios.py` | PR #6 — `feat/us-16-cambiar-estado-individual-de-envío` |
| US-09 | Como Operador, quiero editar datos del envío solo si está en estado INICIADO | `test_editar_envio_en_estado_iniciado` `test_editar_envio_fuera_de_estado_iniciado_retorna_400` `test_detalle_operador_en_iniciado_muestra_formulario_editable` `test_detalle_operador_fuera_de_iniciado_muestra_solo_lectura` `test_editar_envio_form_operador_en_iniciado_actualiza_datos` `test_editar_envio_form_operador_fuera_de_iniciado_no_actualiza` `test_editar_envio_form_con_rol_invalido_no_permite` | `tests/test_envios.py` | PR #14 — `feat/US-09-editar-datos-envio-estado-inicial` |
| US-10 | Como Operador, quiero cancelar un envío en estado INICIADO | `test_cancelar_envio_en_estado_iniciado` `test_cancelar_envio_sin_confirmacion_retorna_400` `test_cancelar_envio_fuera_de_estado_iniciado_retorna_400` `test_detalle_operador_en_iniciado_muestra_panel_cancelacion` `test_detalle_operador_fuera_de_iniciado_muestra_mensaje_no_disponible` `test_cancelar_envio_form_operador_en_iniciado_cancela_envio` `test_cancelar_envio_form_sin_confirmacion_muestra_error_y_no_cancela` `test_cancelar_envio_form_fuera_de_iniciado_no_cancela` `test_cancelar_envio_form_con_rol_invalido_no_permite` | `tests/test_envios.py` | PR #15 — `feat/us-10-cancelar-envio-ingresado` |
| US-11 | Como Operador, quiero listar todos los envíos ordenados por fecha | `test_listar_envios_retorna_semilla` `test_listar_envios_ordenados_por_fecha` | `tests/test_envios.py` | PR #2 — `feat/US-11-lista-de-envios` |
| US-12 | Como Operador, quiero buscar un envío por Tracking ID | `test_buscar_envio_existente` `test_buscar_envio_inexistente_retorna_404` | `tests/test_envios.py` | PR #3 — `feat/US-12-busqueda-de-envio-por-tracking-ID` |
| US-13 | Como Operador, quiero ver el detalle completo del envío | `test_detalle_envio_incluye_historial` `test_detalle_envio_incluye_destinatario` | `tests/test_envios.py` | PR #4 — `feat/US-13-visualizacion-de-detalle-completo-de-envio` |
| US-14 | Como Operador, quiero filtrar envíos por estado actual | `test_filtrar_envios_por_estado` | `tests/test_envios.py` | PR #16 — `feat/us-14-filtrar-envios-por-estado` |
| US-15 | Como Operador, quiero filtrar envíos por rango de fecha | `test_filtrar_envios_por_fecha_desde` `test_filtrar_envios_fecha_futura_retorna_vacio` `test_filtrar_envios_fecha_desde_mayor_hasta_retorna_400` | `tests/test_envios.py` | PR #12 — `feat/us-15-filtrar-envios-por-rango-fecha` |
| US-17 | Como Supervisor, quiero cambiar el estado de múltiples envíos en lote | `test_cambio_estado_masivo_supervisor_actualiza_solo_seleccionados` `test_cambio_estado_masivo_con_rol_operador_retorna_403` `test_cambio_estado_masivo_sin_seleccion_retorna_400` `test_cambio_estado_masivo_omite_envio_cancelado` `test_cambio_masivo_omite_envio_entregado` | `tests/test_envios.py` | PR #27 — `feat/cambio-masivo-de-estado-y-consentimiento` |
| US-19 | Como Operador, quiero ver el historial completo de estados | `test_historial_envio_retorna_lista` `test_historial_envio_inexistente_retorna_404` | `tests/test_envios.py` | PR #7 — `feat/us-19-historial-de-estados-en-detalle` |
| US-21 | Como Operador, quiero registrar el consentimiento informado al crear un envío | `test_crear_envio_form_sin_consentimiento_muestra_error_y_no_registra` `test_crear_envio_form_con_consentimiento_registra_envio` `test_registrar_envio_sin_consentimiento_no_valida_en_api` | `tests/test_envios.py` | PR #27 — `feat/cambio-masivo-de-estado-y-consentimiento` |
| US-22 | Como Supervisor, quiero anonimizar datos personales de un envío finalizado | `test_anonimizar_envio_finalizado_reemplaza_datos_personales` `test_anonimizar_envio_no_finalizado_retorna_400` `test_anonimizar_envio_con_rol_invalido_retorna_403` `test_anonimizar_envio_sin_confirmacion_retorna_400` `test_anonimizar_envio_mantiene_historial_intacto` | `tests/test_envios.py` | PR #30 — `feat-us-22-anonimizacion-de-datos` |
| US-23 | Como Administrador, quiero exportar datos de un cliente en CSV | `test_exportar_datos_remitente_csv_como_administrador` `test_exportar_datos_destinatario_csv_como_administrador` `test_exportar_datos_cliente_con_rol_invalido_retorna_403` `test_exportar_datos_cliente_inexistente_retorna_404` `test_exportar_datos_destinatario_inexistente_retorna_404` `test_exportar_datos_cliente_con_tipo_invalido_retorna_400` | `tests/test_envios.py` | PR #32 — `feat-us-23-exportacion-datos-cliente` |
| US-25 | Como Operador, quiero que la IA sugiera la prioridad del envío automáticamente | Integrado en `test_registrar_envio_genera_tracking_id` | `tests/test_envios.py` | PR #34 — `feat-machine-learning` |

---

## Cobertura por Historia

| ID | Historia | Tests | Estado |
|---|---|---|---|
| US-01 | Inicio de sesión | 3 | ✅ Cubierta |
| US-02 | Cierre de sesión | 1 | ✅ Cubierta |
| US-03 | Alta de usuario | 3 | ✅ Cubierta |
| US-04 | Listado de usuarios | 2 | ✅ Cubierta |
| US-05 | Editar datos y rol de usuario | 8 | ✅ Cubierta |
| US-06 | Baja lógica de usuario | 11 | ✅ Cubierta |
| US-07 | Registro de envío con ML | 1 | ✅ Cubierta |
| US-08 | Cambio de estado (solo Supervisor) | 5 | ✅ Cubierta |
| US-09 | Editar datos en estado INICIADO | 7 | ✅ Cubierta |
| US-10 | Cancelar envío | 9 | ✅ Cubierta |
| US-11 | Listado de envíos ordenado | 2 | ✅ Cubierta |
| US-12 | Búsqueda por Tracking ID | 2 | ✅ Cubierta |
| US-13 | Detalle completo con destinatario e historial | 2 | ✅ Cubierta |
| US-14 | Filtrar por estado | 1 | ✅ Cubierta |
| US-15 | Filtrar por rango de fecha con validación | 3 | ✅ Cubierta |
| US-17 | Cambio de estado masivo | 5 | ✅ Cubierta |
| US-19 | Historial de estados | 2 | ✅ Cubierta |
| US-21 | Consentimiento informado | 3 | ✅ Cubierta |
| US-22 | Anonimización de datos (Supervisor) | 5 | ✅ Cubierta |
| US-23 | Exportación CSV de cliente (Administrador) | 6 | ✅ Cubierta |
| US-25 | Prioridad sugerida por IA | 1 | ✅ Cubierta |
