---
name: conectar-google
description: Diagnosticar antes de intentar conectar Colab, Google Drive, Gmail o cualquier conector de Google desde Claude Code en esta máquina — qué no repetir y cuándo el problema no tiene arreglo local. Úsala antes de llamar a open_colab_browser_connection, tocar el conector de Drive/Gmail de claude.ai, o usar chrome-devtools para algo que pase por una cuenta de Google.
---

# Conectar con Google (Colab, Drive, Gmail) desde aquí

> **La regla que lo ordena todo:** ninguno de estos fallos se arregla reintentando
> la misma llamada. Si el primer intento no conecta, el segundo tampoco —
> diagnostica primero con los comandos de la sección 3, o para y pide la
> alternativa de diez segundos.

---

## 1. La regla que ahorra la hora

**No hagas esto:**
- Llamar `open_colab_browser_connection` más de una vez seguida esperando que
  "a la segunda funcione". El 8 sep 2026 se probó cuatro veces con token
  fresco cada vez; las cuatro terminaron igual.
- Esperar a que el conector de Google Drive de claude.ai se arregle solo
  reiniciando el ordenador, la sesión o el chat. No lo arregla.
- Reutilizar una pestaña de Colab abierta en un intento anterior. El puerto y
  el token rotan en cada arranque del servidor MCP; esa pestaña ya es basura.
- Insistir cuando `open_colab_browser_connection` no responde. Se ha colgado
  30 minutos dos veces y tumbado el servidor MCP otras dos. Ninguna de las
  cuatro veces se resolvió esperando.

**Haz esto en su lugar (diez segundos):** pídele al usuario que copie y pegue
en el chat el código de la celda, o su salida. Es más lento para él que un
Colab conectado, pero infinitamente más rápido que una hora perdida en
reconexión. Si lo que hace falta es leer un archivo de Drive, pide el
contenido pegado o el archivo exportado; no dependas del conector si ya
falló una vez en esta sesión.

---

## 2. Árbol de diagnóstico

| Síntoma observado | Qué comprobar | Qué significa |
|---|---|---|
| `connection open` seguido de `connection closed` en el mismo segundo, en el log | Las dos líneas `server listening on` al arrancar: ¿un puerto en `[::1]` (IPv6) y otro distinto en `127.0.0.1` (IPv4)? | Verificado en esta máquina: **siempre** aparecen dos puertos distintos, y el WebSocket se anuncia solo en el de IPv6. Es un bug de fondo del servidor, no de tu conexión. No hay arreglo por el lado del usuario; ver §5. |
| `open_colab_browser_connection` no responde tras ~60 s | Si sigue "pensando", es el mismo bloqueo ya visto dos veces (se cuelga 30 min de verdad). | No esperes. Cancela, comprueba con `tasklist`/`Get-Process` si el proceso `colab-mcp` sigue vivo, y si sí, mátalo antes de reintentar. |
| El servidor MCP entero cae con `Connection closed` justo después de usar la herramienta | Log más reciente: busca `Closing WebSocket server` cerca de la hora del fallo. | La propia llamada tumbó el servidor (pasó dos veces el 8 sep). Hace falta reiniciar el MCP (reiniciar la sesión de Claude Code), no reintentar en caliente: el proceso ya no existe. |
| Pestaña de Colab vieja muestra "Disconnected from the local Colab MCP server" | Compara el puerto en la URL de esa pestaña (`...&mcpProxyPort=NNNNN`) contra el puerto `server listening on 127.0.0.1:NNNNN` del log **más reciente**. | Si no coinciden, la pestaña pertenece a una sesión anterior del MCP. Ciérrala; no sirve para nada, cada arranque rota puerto y token. |
| Drive/Gmail devuelven `Operation is not implemented, or supported, or enabled` | ¿Aparece Drive en el aviso de sistema de "servidores que requieren autenticación"? | Si **no** aparece pero igual falla, no es sesión caducada — el conector está deshabilitado o restringido del lado de claude.ai. Reiniciar no lo arregla; solo el usuario puede tocarlo en claude.ai → Ajustes → Conectores. |
| chrome-devtools no ve ni cierra las pestañas del usuario | ¿Puertos 9222/9223/9333 abiertos en el Chrome del usuario? | En esta máquina están cerrados los tres: chrome-devtools controla un Chrome **aislado**, no el del usuario. No vas a poder gestionar sus pestañas reales desde ahí. |

---

## 3. Comandos exactos

**Encontrar el log más reciente y ver solo lo que importa** (Git Bash):

```bash
LOGDIR=$(ls -td "/c/Users/$USER/AppData/Local/Temp"/colab-mcp-logs-*/ 2>/dev/null | head -1)
LOGFILE=$(ls -t "$LOGDIR"*.log | head -1)
echo "$LOGFILE"
grep -E "listening on|connection open|connection closed|Closing WebSocket|server closed" "$LOGFILE"
```

La primera línea del log da el puerto vivo, ej. `server listening on
127.0.0.1:51970`. Ese es el puerto real de **esta** sesión del servidor —
cualquier pestaña de Colab que no lo tenga en su URL está muerta.

**Comprobar si el proceso sigue en pie** (PowerShell):

```powershell
Get-Process colab-mcp -ErrorAction SilentlyContinue | Select Id,StartTime
```

Más de una fila = instancias huérfanas de sesiones anteriores compitiendo por
puertos. Mátalas antes de reintentar:

```powershell
Get-Process colab-mcp -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Ver qué versión de colab-mcp hay instalada y dónde está `uv`** (verificado
en esta máquina, 8 sep 2026):

- Ejecutable: `C:\Users\laura\.local\bin\colab-mcp.exe`
- Instalado con: `uv tool install git+https://github.com/googlecolab/colab-mcp`
  (sin tag fijado — sigue la rama por defecto del repo)
- Versión actual: **1.0.1**
  (`C:\Users\laura\AppData\Roaming\uv\tools\colab-mcp\Lib\site-packages\colab_mcp-1.0.1.dist-info`)
- `uv` (0.12.10) se instaló con `pip install uv` dentro del Python de
  Microsoft Store, así que su `.exe` **no** está en el PATH de la sesión ni en
  `~\.local\bin` (ahí solo vive el *shim* `colab-mcp.exe`). Su ruta real:
  `C:\Users\laura\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\uv.exe`

Para comprobar la versión o intentar actualizar:

```bash
UV="/c/Users/laura/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0/LocalCache/local-packages/Python311/Scripts/uv.exe"
"$UV" tool list                    # confirma la versión instalada
"$UV" tool upgrade colab-mcp       # trae el HEAD actual de la rama por defecto
```

No verificado: si `uv tool upgrade` trae de verdad commits más nuevos que el
release 1.0.2, o si el remoto solo ofrece hasta ahí. No se ejecutó el
comando, solo se confirmó dónde vive `uv.exe`.

---

## 4. Qué puede y qué no puede hacer Claude Code aquí

- **No puede lanzar ni completar un flujo OAuth de Google.** No puede pedir
  permisos, autorizar una cuenta ni renovar un token caducado. Si algo exige
  reautorizar Drive, Gmail o Colab desde cero, dilo así al usuario en vez de
  intentarlo: *"esto lo tienes que hacer tú, en el navegador o en claude.ai →
  Ajustes → Conectores"*.
- **Puede** leer los logs, comprobar y matar procesos, y hacer **un** intento
  de conexión ya diagnosticado — nunca una serie de intentos ciegos.
- **Puede** trabajar sin ningún conector: pedir al usuario que pegue el
  código o la salida sigue siendo la vía más rápida cuando algo ya falló una
  vez en la sesión.

---

## 5. Lo que aporta la investigación externa (8 sep 2026)

### Verificado localmente en esta máquina

Los cinco logs de hoy en `%TEMP%\colab-mcp-logs-*\` muestran siempre el mismo
patrón al arrancar:

```
server listening on [::1]:63415        <- IPv6, puerto A
server listening on 127.0.0.1:63416    <- IPv4, puerto B (distinto de A)
Starting WebSocket server on ws://localhost:63415   <- solo anuncia el puerto IPv6
```

Los cuatro logs que registraron `connection open` / `connection closed`
inmediato tienen este doble-bind con puertos distintos. Es un hecho
comprobado en disco, no una suposición.

### De la investigación externa (no confirmado por Google, pero coherente con lo anterior)

- El repositorio oficial [`googlecolab/colab-mcp`](https://github.com/googlecolab/colab-mcp)
  va por la versión **1.0.2** (release del 27 mar 2026). Su changelog dice
  solo *"fix: pyproject.toml format"* — nada de red, puertos ni Windows.
  Actualizar de 1.0.1 a 1.0.2 probablemente **no** arregla el
  `connection closed`.
- Un fork de terceros, [`SebastianGilPinzon/colab-mcp`](https://github.com/SebastianGilPinzon/colab-mcp),
  documenta en su README exactamente el patrón visto aquí: el servidor liga
  `host="localhost", port=0"`, lo que en Windows crea dos sockets (IPv4 e
  IPv6) en puertos distintos; el navegador resuelve `localhost` a una familia
  u otra y falla la conexión el porcentaje de veces que resuelve a la
  equivocada. Su arreglo es forzar `host="127.0.0.1"`. **Esto no es un fix
  oficial de Google ni está confirmado en un issue cerrado** — es la
  explicación más coherente disponible hoy, y coincide con los logs locales.
  Usar ese fork significa correr un servidor MCP no oficial con acceso a tu
  navegador; es una decisión del usuario, no algo que activar sin
  preguntarle.
- Discusiones oficiales [#84](https://github.com/googlecolab/colab-mcp/discussions/84)
  y [#43](https://github.com/googlecolab/colab-mcp/discussions/43) confirman
  el patrón de "Disconnected" por pestañas apuntando a un servidor muerto y
  por instancias duplicadas corriendo a la vez. Sin fix oficial en ninguna de
  las dos.
- [Issue #71](https://github.com/googlecolab/colab-mcp/issues/71): "Claude
  Code no conecta con colab-mcp". Abierto, sin respuesta de mantenedores, sin
  resolución.
- [`googlecolab/google-colab-cli`](https://github.com/googlecolab/google-colab-cli)
  permite `colab exec` / `colab run` sin pasar por el navegador — pero su
  propio README dice explícitamente que **solo soporta Linux y macOS, no
  Windows**. En esta máquina no es una alternativa directa. Podría funcionar
  dentro de WSL, pero **no se probó** (no verificado).
- El conector de Google Drive de claude.ai tiene un incidente de estado
  cerrado ("Degraded Google Drive Connector Experience",
  [status.claude.com](https://status.claude.com/incidents/9x9qzmfb2v0l)) y
  varios issues abiertos en `anthropics/claude-code`
  ([#41635](https://github.com/anthropics/claude-code/issues/41635),
  [#41660](https://github.com/anthropics/claude-code/issues/41660),
  [#70050](https://github.com/anthropics/claude-code/issues/70050)) sobre
  fallos del conector y sobre que ni siquiera se pasa a Claude Code aunque
  esté autorizado en claude.ai. No hay más procedimiento de reactivación que
  claude.ai → Ajustes → Conectores; si eso no lo arregla, es un bug del lado
  de Anthropic sin fecha pública, no algo que el usuario o Claude Code puedan
  forzar.

### Huecos declarados — sin verificar

- Si existe una opción en la UI de Colab o una extensión de navegador que
  evite el problema de conexión: no se encontró mención en la documentación
  oficial.
- Si `uv tool upgrade colab-mcp` trae commits más nuevos que el release 1.0.2:
  no se ejecutó el comando.
- Si WSL resuelve el problema de `google-colab-cli` en Windows: no se probó.
- La causa raíz exacta del `connection closed` **no está confirmada por
  Google** en ningún issue cerrado; lo de arriba es la explicación del fork,
  consistente con los logs de esta máquina pero no un "fixed by" oficial.
