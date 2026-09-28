# GPT-Live en Pléyade — contexto de implementación

**Fecha:** 27 de septiembre de 2026
**Estado:** integrado en `master` local (`f5c1fa8`); traspaso registrado en `624821b`. **No publicado.**

## Encargo

Miguel pidió incorporar un agente de voz GPT-Live con esta configuración de inicio, sin añadir campos para que los omitidos conserven los valores por defecto del servidor:

```json
{
  "model": "gpt-live-1",
  "audio": {
    "output": {
      "voice": "gleam"
    }
  },
  "delegation": {
    "type": "responses",
    "responses": {
      "parallel_tool_calls": false,
      "model": "gpt-6-astra",
      "reasoning": {
        "effort": "medium"
      },
      "tools": [
        {
          "type": "web_search"
        }
      ]
    }
  }
}
```

El archivo que manda es [`app/gpt_live_session.json`](../../app/gpt_live_session.json). El agente nuevo es independiente de la lectura guiada D5, que sigue usando `gpt-live-transcribe` y otro protocolo.

## Flujo implementado

1. La pantalla `#/conversar` pide el micrófono desde el clic del usuario, prepara WebRTC y crea el canal de datos `oai-events` antes de generar la oferta SDP.
2. Angular envía solo `{ "sdp": "..." }` a `POST /api/gpt-live/sesion`, con la identidad habitual `X-Lector`.
3. La API aplica la puerta de cuenta, el límite horario de voz y un uso de la cuenta. Desde el servidor envía a OpenAI `POST /v1/live/sessions` con `{ "session": <JSON exacto>, "transport": { "type": "webrtc", "sdp": "..." } }`, autenticado con la clave del proyecto.
4. La API devuelve únicamente `session.id` (tratado como opaco) y `transport.sdp`; nunca devuelve la clave.
5. El navegador aplica el SDP de respuesta, recibe la voz en la pista remota y espera `session.started`. No envía otra configuración de inicio.
6. La pantalla muestra los fragmentos exactos de `session.input_transcript.delta` y `session.output_transcript.delta`. Los agrupa por hablante y cercanía de `start_ms`/`end_ms`; conserva el texto, espacios, repeticiones e intervalos originales. No supone turnos completos.
7. Al terminar, el navegador envía `session.close` y mantiene micrófono, audio, canal y WebRTC hasta `session.closed`. Si llega el evento, muestra el uso final. Si hay desconexión o pasan 15 segundos, informa **finalización incompleta** y libera recursos.

## Archivos

| Archivo | Responsabilidad |
| --- | --- |
| `app/gpt_live_session.json` | Configuración de inicio exacta. |
| `app/api.py` | Creación de sesión Live, autorización, cobro/devolución si falla el alta y respuesta SDP. |
| `app/config.py` | Permite leer un archivo de claves externo mediante `LITERALEVEL_CLAVES_RUTA`. |
| `front/src/app/nucleo/api.ts` | Cliente de la nueva ruta HTTP. |
| `front/src/app/compartido/gpt-live/conexion.ts` | WebRTC, audio, eventos y cierre. |
| `front/src/app/compartido/gpt-live/transcripcion.ts` | Agrupación temporal de deltas sin alterar su texto. |
| `front/src/app/pantallas/conversar.ts` | Pantalla de conversación y estados visibles. |
| `front/src/app/app.routes.ts`, `front/src/app/pantallas/inicio.ts` | Ruta y entrada desde Inicio. |
| `pruebas_api.py`, `front/src/app/compartido/gpt-live/*.spec.ts` | Pruebas simuladas del contrato y del ciclo de vida. |

## Clave y entorno

La clave nueva se creó para el proyecto elegido por Miguel y se guardó **fuera del repositorio**, en el archivo de OneDrive que él indicó. No se imprimió ni se añadió a Git. La variable de usuario de Windows `LITERALEVEL_CLAVES_RUTA` apunta a ese archivo para los **procesos nuevos**; un servidor que ya estaba abierto necesita reiniciarse. En un servidor desplegado se debe configurar `OPENAI_API_KEY` como secreto del entorno: la ruta local de OneDrive no existe allí.

## Verificación realizada

- **CONFIRMADO:** prueba HTTP simulada: JSON de inicio y transporte, URL, autenticación, ID opaco, SDP, ausencia de clave en la respuesta y devolución del uso ante error.
- **CONFIRMADO:** 3 pruebas del front para deltas exactos, agrupación temporal, espera de `session.closed` y vencimiento del cierre.
- **CONFIRMADO:** `npx tsc --noEmit -p tsconfig.app.json` y `npm run build` desde `front/` (el build solo informó una advertencia previa sobre el presupuesto CSS de Pronunciar).
- **CONFIRMADO:** pantalla abierta en navegador local a ancho móvil cercano a 390 px, con enlace desde Inicio y estado inicial legible. En esa revisión no había backend local abierto; el aviso de motor dormido era esperado.
- **CONFIRMADO:** el lector de configuración local detectó la clave en el archivo externo, sin mostrar su valor.

## Pendiente y límites

- **NO VERIFICADO:** conversación real con micrófono, audio remoto, solapamiento de voces, permisos efectivos del proyecto para los modelos y `session.closed` real. No se inició una sesión pagada durante las pruebas.
- **NO INTEGRADO EN PRODUCCIÓN:** publicar API y front juntos, y verificar la revisión efectiva del Space y el despliegue del front. El código local no demuestra despliegue.
- El cierre automático a los 3 minutos está en la interfaz. La API limita altas por cuenta y hora, pero no impone un corte de duración del lado del servidor; revisar ese control antes de abrir la función a más usuarios.
- La nueva conversación cobra un uso de la cuenta por alta. Los costes de voz y del backend delegado son independientes; comprobar el consumo real en el piloto.

## Próximo paso recomendado

Hacer **un piloto supervisado** con la voz y el móvil de Miguel: comprobar respuesta audible, transcripción simultánea con tiempos, cierre confirmado y gasto. Si pasa, revisar el control de duración y publicar API y front como una sola unidad. Mantener el estado de producción como no verificado hasta comprobarlo por contenido y respuesta de `/api/salud`.

## Referencias de protocolo

- [OpenAI: WebRTC para GPT-Live](https://developers.openai.com/api/docs/guides/voice-webrtc)
- [OpenAI: transcripciones y cierre de sesiones](https://developers.openai.com/api/docs/guides/live-conversations)
