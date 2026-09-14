# Cierre acotado: temporal de voz antes del cobro

Se corrige exclusivamente el hallazgo 3 de
`codex_api_relevo_2026-09-13.md`, que describe el estado base `f1cfb5d` y se
conserva sin reescribir su historia. Encargo de implementacion separado de
la auditoria de solo lectura, autorizado por la sesion coordinadora.

## Cambio

- `app/api.py`, solo `practicar`: crear y escribir el temporal antes del tope
  horario y de `_puede_pagar`. Fallos locales de disco devuelven 500 generico
  sin consumir cuota ni entrar en `voz.practicar`.
- Un finally exterior limpia el temporal tambien ante 403, 429, ausencia de
  clave y excepciones. Si falla `fdopen`, cierra el descriptor aun sin objeto
  archivo. No cambia la politica de devoluciones tras iniciar el motor.
- Sin cambios de firma, JSON de exito, UI, voz, autenticacion ni otras rutas.
- Los otros tres hallazgos del informe no se corrigen en este encargo.

## Verificacion

Prueba nueva `voz_prepara_temporal_antes_de_cobrar` en `pruebas_api.py`, tambien
registrada en su bateria. Se ejecuto mediante el runner reproducible
`pruebas_api_voz_temporal.py`, que extrae por AST las funciones reales, sin
importar los modulos de la app ni cargar claves/modelo. Usa HTTP multipart
real con Starlette y dobles de pago y proveedor.

```powershell
& 'C:/Users/laura/AppData/Roaming/uv/tools/colab-mcp/Scripts/python.exe' -B -X utf8 pruebas_api_voz_temporal.py --comparar f1cfb5d
```

Resultado: crear/escribir devuelven 500 sin reserva; cuota denegada devuelve
403; temporales borrados; cero llamadas al motor. La misma prueba detecta
el manejador anterior de `f1cfb5d` como regresion. `git diff --check` limpio
(solo aviso de conversion LF/CRLF propio del checkout).

Limitacion: no hay un entorno descubierto con FastAPI/Gradio y el stack
completo; no se instalo nada. El runner verifica este manejador y el parseo
multipart de Starlette, no la integracion completa FastAPI/Gradio ni el Space.
Pendiente ejecutar `pruebas_api.py` en el entorno completo antes de desplegar.
No hubo llamadas de red, proveedor, pagos ni despliegue.
