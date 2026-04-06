# NFRs — Atributos de Calidad

**Proyecto:** LogiTrack (SFGLD) — Grupo 10  
**Materia:** Proyecto Profesional I / Laboratorio de Construcción de Software  
**Sprint:** 3

---

## Rendimiento (Performance)

**NFR-01 — Tiempo de respuesta**  
El sistema debe resolver las consultas de búsqueda de un envío por su Tracking ID en un tiempo máximo de 2 segundos bajo condiciones normales de red.

**NFR-02 — Procesamiento masivo**  
El procesamiento del archivo CSV para la carga masiva de envíos no debe bloquear la interfaz de usuario, y el backend debe procesar un archivo de hasta 500 registros en menos de 10 segundos.

---

## Usabilidad (Usability)

**NFR-05 — Diseño responsivo**  
La interfaz web debe adaptarse sin pérdida de funcionalidad a resoluciones de escritorio y a dispositivos móviles.

**NFR-06 — Prevención de errores**  
Todos los formularios de alta deben realizar validaciones mostrando mensajes de error claros antes de enviar la petición.

---

## Soporte y Mantenibilidad (Supportability)

**NFR-07 — Integración continua**  
Todo código subido a la rama principal (`main`) debe pasar automáticamente el pipeline de GitHub Actions con linter (Flake8) y tests automatizados (Pytest) para asegurar la calidad del código.

**NFR-08 — Control de acceso por rol**  
Las operaciones de cambio de estado están restringidas a los roles **Supervisor** y **Administrador** (jerarquía acumulativa: el Administrador hereda todos los permisos del Supervisor). Un Operador que intente cambiar el estado recibe un error `403 Forbidden`.

---

## Seguridad y Legales (Security & Legal)

**NFR-03 — Cifrado de credenciales**  
Las contraseñas de los usuarios se almacenan hasheadas con **bcrypt** mediante `passlib`. La comparación en el login usa `pwd_context.verify()`, nunca texto plano. El campo `password` está marcado con `Field(exclude=True)` en el modelo Pydantic para que nunca aparezca en respuestas JSON.

**NFR-04 — Enmascaramiento Ley 25.326**  
Los endpoints públicos de la API REST usan modelos de respuesta (`EnvioResumen`, `EnvioDetalle`, `ClientePublico`) que excluyen el DNI del remitente y destinatario. El DNI solo es accesible mediante el endpoint de exportación CSV (`/exportar-cliente`), restringido exclusivamente al rol Administrador.
