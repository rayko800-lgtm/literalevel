# LiteraLevel — contrato operativo para agentes

Este archivo contiene SOLO el contrato vigente que un agente necesita antes
de tocar código.

El historial completo anterior al 16 sep 2026 está preservado en:

`docs/ai/legacy/_architecture/AGENTS.full.2026-09-16.md`

No cargues ese historial completo salvo que una tarea requiera investigar una
decisión antigua concreta.

## Estado actual

- La entrega es el **front Angular** (`front/`) sobre `app/api.py`.
- Gradio (`app/ui.py`) queda como motor y respaldo.
- Una función de cara al usuario no está terminada hasta tener:
  - contrato/ruta en `app/api.py`; y
  - pantalla correspondiente en `front/`.
- El modelo v4 es **final**. No se reentrena.
- Hasta después del 20 sep, `app/catalogo.py` y `app/cuentas.py` están
  congelados salvo un SERIO que afecte demo o usuarios.
- Antes de la demo/vídeo no iniciar código nuevo salvo petición explícita
  de Miguel o un SERIO confirmado.
- Estado operativo inmediato: `docs/ai/HANDOFF.md`.

## Reparto de archivos

- `app/ui.py`, interfaz Gradio y coordinación UI: Claude Code.
- `app/reader.py`, `app/lexicon.py`, `app/voz.py`: históricamente auditados
  por Codex. Antes de editarlos, revisar `git log` y el HANDOFF vigente.
- `app/scoring.py`, `app/perfil.py`, `app/catalogo.py`, `app/config.py`:
  compartidos; revisar diff antes de editar o hacer commit.
- `modelo_v4/` y `kaikki_diccionario.db`: datos. No regenerarlos ni
  versionarlos.

Si cambia una firma pública de un módulo, indicarlo claramente en el commit.

## Contratos que no se rompen

### Escalas
- Escala pública: **0..2**.
- Escala interna del modelo: **0..5**.
- La escala interna no sale de `scoring.py`.

### Modelo y lectura
- `scoring.Puntuador(...).puntuar(texto)` es la frontera de puntuación.
- No cambiar a carga anticipada de los recursos pesados: deben cargarse al
  primer uso.
- El modelo v4 no se sustituye ni se reentrena.

### Diccionario y léxico
- Oxford Dictionaries está descartado.
- Diccionario principal: Kaikki/Wiktionary en SQLite local.
- OpenAI puede explicar contexto, gramática y traducir.
- OpenAI NO redefine una palabra que el diccionario ya trae.
- Si no hay una acepción utilizable en el diccionario, OpenAI puede definirla,
  pero la interfaz debe marcarla como **generada por IA**.
- `usar_openai=False` es la puerta para impedir llamadas de pago.
- `llamadas_de_pago` debe reflejar llamadas pagadas reales.

### Degradación elegante
Sin `OPENAI_API_KEY` deben seguir funcionando, cuando corresponda:

- diccionario local;
- IPA/audio disponible localmente;
- buscador;
- puntuación;
- ficha;
- navegación y funciones no dependientes de red.

No convertir una función gratuita/local en una dependencia obligatoria de red.

### Datos por lector
Los datos personales de cada lector son independientes.

No usar rutas fijas compartidas para:
- perfil;
- sesión;
- cuaderno;
- historial de voz.

`lexicon.db` sí puede ser compartida porque es caché, no historial personal.

### API / Angular
- Identidad HTTP del lector: cabecera `X-Lector`.
- El Space usa:
  `demo.launch(..., ssr_mode=False, app_kwargs=api.para_gradio())`.
- `con_gradio()` es solo para local.
- `app/api.py` consume helpers de `ui.py`; si cambia una firma usada por la API,
  actualizar/verificar ambas fronteras.

## Git — árbol compartido

Nunca ejecutar globalmente en el working tree compartido:

- `git stash`
- `git checkout .`
- `git add -A`
- `git add .`
- `git commit -a`
- `git reset --hard`

Antes de un commit:

1. `git status`
2. `git diff -- <archivo>`
3. confirmar que no haya hunks de otra sesión
4. añadir únicamente cambios propios

Si dos trabajos necesitan editar simultáneamente el mismo código, usar un
worktree aislado o ejecutarlos en secuencia.

Nunca desplegar desde un worktree.

## Secretos

- `.env`, `CLAVES.txt` y archivos equivalentes contienen secretos.
- Nunca imprimirlos, ni siquiera enmascarados.
- Nunca subir el proyecto con `huggingface_hub.upload_folder` sin exclusiones
  explícitas de secretos.
- Preferir los scripts/procedimientos de despliegue ya establecidos.

## Pruebas

Ejecutar primero la suite más estrecha relacionada con el cambio.

Principales:
- `tests_smoke.py`
- `pruebas_extremas.py`
- `pruebas_integracion.py`
- `pruebas_desambiguacion.py`
- `pruebas_perfil.py`
- `pruebas_ficha.py`
- `pruebas_corpus.py`
- `pruebas_animacion.py`
- `pruebas_voz_ritmo.py`
- `pruebas_voz_concurrencia.py`
- `pruebas_audio_atomico.py`
- `pruebas_api.py`
- `pruebas_portadas.py`
- `pruebas_despliegue.py`
- `pruebas_despliegue_front.py`

`pruebas_voz.py` y `pruebas_lexicon.py` pueden usar OpenAI real dependiendo
de opciones/clave. No provocar gasto externo sin autorización.

Las pruebas del front se ejecutan desde `front/` con `npm.cmd test`.

## Versiones

Este proyecto puede ir por delante del conocimiento del modelo.

Antes de "corregir" una API de una librería, inspeccionar la firma instalada.

Stack documentado:
- Gradio 6.26
- transformers 5.16
- pandas 3.0
- OpenAI 3.8
- torch 2.14

No retroceder código hacia APIs antiguas por memoria del modelo.

## Despliegue

- Verificar el despliegue por contenido/hash, no por suposición.
- Para la API, un HTTP 200 no basta: comprobar el JSON esperado de `/api/salud`.
- Una vuelta atrás del Space no implica que HEAD haya vuelto atrás.
- Archivos acoplados se despliegan juntos o no se despliegan.
- Antes de publicar, cada cambio relevante debe haber sido revisado o
  verificado de manera apropiada.

## Concurrencia

La política actual es **secuencial por defecto**.

- Un workstream activo normalmente.
- Paralelismo únicamente para trabajos realmente independientes.
- No usar múltiples sesiones como estrategia automática de velocidad.
- No mantener sesiones terminadas vivas.
- Si hace falta coordinación multiagente, consultar la skill
  `trabajar-en-equipo`.

## Contexto histórico

Si una tarea necesita saber por qué existe una regla o investigar una decisión
antigua, consultar selectivamente:

`docs/ai/legacy/_architecture/AGENTS.full.2026-09-16.md`

No cargarlo entero por defecto.

La verdad actual se determina con:
1. código actual;
2. `docs/ai/HANDOFF.md`;
3. `git log` / commit correspondiente;
4. memoria/skill relevante;
5. historial legado, solo cuando sea necesario.
