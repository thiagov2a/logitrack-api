# NFRs — Atributos de Calidad

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software  
**Sprint:** 3

---

## Rendimiento (Performance)

**NFR-01 — Tiempo de respuesta** `SFGLD-35`  
*El sistema debe resolver las consultas de búsqueda de un envío por su Tracking ID en un tiempo máximo de 2 segundos bajo condiciones normales de red.*

**Estado: ✅ Implementado**  
La búsqueda por Tracking ID (`GET /api/envios/{tracking_id}`) opera sobre una lista en memoria sin I/O de disco ni red. El tiempo de respuesta es inferior a 100ms en condiciones normales. La búsqueda desde la vista HTML es server-side con filtro directo sobre `mock_db_envios`.

---

**NFR-02 — Procesamiento masivo** `SFGLD-36`  
*El procesamiento del archivo CSV para la carga masiva de envíos no debe bloquear la interfaz de usuario, y el backend debe procesar un archivo de hasta 500 registros en menos de 10 segundos.*

**Estado: ✅ Implementado**  
El endpoint `POST /api/envios/importar-csv` es `async`, lo que evita bloquear el event loop de FastAPI. El procesamiento fila por fila con manejo de errores individuales permite continuar ante filas inválidas. Para 500 registros en memoria el tiempo estimado es inferior a 2 segundos.

---

## Usabilidad (Usability)

**NFR-05 — Diseño responsivo** `SFGLD-39`  
*La interfaz web debe adaptarse sin pérdida de funcionalidad a resoluciones de escritorio y a dispositivos móviles.*

**Estado: ✅ Implementado**  
Todos los templates usan Tailwind CSS con clases responsivas (`flex-wrap`, `grid-cols-1 sm:grid-cols-2`, `lg:grid-cols-3`). Los formularios y tablas se adaptan a pantallas pequeñas sin pérdida de funcionalidad.

---

**NFR-06 — Prevención de errores** `SFGLD-40`  
*Todos los formularios de alta deben realizar validaciones mostrando mensajes de error claros antes de enviar la petición.*

**Estado: ✅ Implementado**  
- Formulario de nuevo envío: validaciones HTML5 (`required`, `pattern`, `minlength`, `maxlength`) en todos los campos. Mensajes de error renderizados server-side en caso de fallo de validación Pydantic.  
- Formulario de nuevo usuario: validación de email duplicado y campos obligatorios.  
- Importación CSV: validación de columnas requeridas con mensaje descriptivo de qué columnas faltan.  
- Filtros de fecha: el backend valida que `fecha_desde` no sea mayor que `fecha_hasta` (HTTP 400).

---

## Soporte y Mantenibilidad (Supportability)

**NFR-07 — Integración continua** `SFGLD-41`  
*Todo código subido a la rama principal (`main`) debe pasar automáticamente el pipeline de GitHub Actions con linter (Flake8) y tests automatizados (Pytest).*

**Estado: ✅ Implementado**  
El archivo `.github/workflows/ci.yml` ejecuta en cada push/PR a `main`:
1. Instalación de dependencias (`pip install -r requirements.txt`)
2. Linter: `flake8 . --max-line-length=120 --exclude=venv,analysis`
3. Tests: `pytest tests/ -v`

El pipeline falla si cualquiera de los pasos retorna código de error distinto de 0.

---

**NFR-08 — Estándar de comunicación** `SFGLD-42`  
*Toda la comunicación entre el frontend y la Mock API (backend) debe realizarse estrictamente mediante el formato JSON (`application/json`).*

**Estado: ✅ Implementado con extensión CSV**  
La API REST usa JSON como formato base para todos los endpoints (`/api/envios/`, `/api/usuarios/`). FastAPI serializa automáticamente los modelos Pydantic a JSON y los modelos de respuesta (`EnvioResumen`, `EnvioDetalle`, `ClientePublico`) garantizan contratos de datos estables.

Sin embargo, **CSV es el formato más utilizado en las funcionalidades principales del proyecto**:
- `POST /api/envios/importar-csv` — carga masiva de envíos desde archivo `.csv`
- `GET /api/envios/{id}/exportar-cliente` — exportación de datos personales en `.csv` (Derecho de Acceso, Ley 25.326)
- Importación desde la interfaz web (`/envios/nuevo`) mediante formulario multipart con archivo `.csv`

Las vistas HTML usan formularios HTML estándar (server-side rendering), lo cual es el comportamiento correcto para ese canal.

---

## Seguridad y Legales (Security & Legal)

**NFR-03 — Cifrado de credenciales** `SFGLD-37`  
*Las contraseñas de los usuarios nunca deben almacenarse en texto plano; deben estar protegidas mediante un algoritmo de hashing.*

**Estado: ✅ Implementado**  
Las contraseñas se hashean con **bcrypt** (`bcrypt.hashpw()`) al inicializar `mock_usuarios`. La verificación en el login usa `bcrypt.checkpw()`, nunca comparación en texto plano. El campo `password` está marcado con `Field(exclude=True)` en el modelo Pydantic para que nunca aparezca en respuestas JSON.

---

**NFR-04 — Enmascaramiento Ley 25.326** `SFGLD-38`  
*En la vista pública o general de seguimiento, el sistema debe ofuscar los datos personales del remitente y destinatario para proteger su privacidad.*

**Estado: ✅ Implementado**  
Los endpoints públicos de la API REST usan modelos de respuesta que excluyen el DNI:
- `EnvioResumen` (listado): expone solo `nombre` y `anonimizado`, nunca el DNI.
- `EnvioDetalle` (detalle): ídem mediante `ClientePublico`.
- El DNI completo solo es accesible vía `GET /api/envios/{id}/exportar-cliente`, restringido exclusivamente al rol **Administrador**.
- Los datos anonimizados (`***`) se muestran con indicador visual 🛡️ en la interfaz.
