# Seguridad Pléyade — cierre 1 oct 2026

Leer [el informe](../../auditoria/seguridad_pleyade_2026-10-01.md) antes de ampliar cuotas, reactivar Gradio/Realtime o cambiar el almacenamiento.

- Código del servidor publicado: `5128df0`; Space `b60a6cfe0416130d3ed8df40c1f2f169f4e54e0e`, RUNNING, `/api/salud` JSON `0.3.0-seguridad`.
- Vercel: `main-D2L26KL7.js`, SHA256 `5e76cb2444ceee2e3beebf761a5c03f71857c1e26ba57ef2f3f33fab91b0ee7d`, igual al build local.
- 71/71 API, 38/38 seguridad, 505/505 front; 53 checks de producción, sin audio de pago. Los datos y la contraseña modificada de pruebas sobrevivieron a un reinicio del Space.
- Presupuesto efectivo: 500 centavos USD/día UTC y 2.000 acumulados desde este control. SQLite en `/data/seguridad.sqlite3` reserva antes de cada llamada; no borrar/restaurar para recargar. Cuotas de acciones máximo 100; heredado 0 significa 100.
- Cuenta bearer 8 h, recuperación 15 min/un uso, archivos generados con capacidades 15 min. `X-Lector` no autentica cuentas. El secreto de cuentas sintéticas se retiró y su archivo local se eliminó.
- `LITERALEVEL_ADMIN_USUARIOS` quedó sin configurar, como antes. Pendiente que Miguel indique el usuario exacto para habilitar recuperación web de cuentas reales. No adivinarlo ni asignar privilegios por nombre supuesto.
- Conversar, lectura en vivo y acceso público a Gradio cerrados. GET/HEAD raíz y GET `startup-events` devuelven JSON inocuo para que Gradio arranque; no abren eventos/cola.
- Dependencias: Angular 22.2.1; mínimos pypdf 6.19, urllib3 2.8, Pillow 12.3, setuptools 83, Pygments 2.20. OSV local (102) y paquetes enumerados por build (92) sin advisories conocidos; no hay SBOM completo de imagen base.
- Pendientes: administrador, retención/eliminación/respaldos, abuso de invitados, calidad y factura real de audio, verificación humana visual. Recomendación: beta pública limitada con los cierres actuales.

No se incluyeron cambios ajenos de README, corpus, vídeo, angular.json ni del HANDOFF principal, que estaban sucios al empezar. No se mataron procesos de Eos/vídeo ni se desplegó desde un worktree.
