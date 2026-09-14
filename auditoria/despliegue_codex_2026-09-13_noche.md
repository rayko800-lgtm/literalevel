# Despliegue Selectivo De Codex

## Autorizacion Y Permisos

Miguel autorizo explicitamente desplegar, cambiar la app y ejecutar pruebas
despues del primer relevo nocturno. Sigue prohibido comprar o contratar.
Se leyo la skill `.claude/skills/desplegar-en-spaces/SKILL.md` y se mantuvo
un solo desplegador: Codex principal.

Las sesiones consultadas de Claude, incluida Central, registraban modo `auto`.
Su configuracion global no tenia un bloque `permissions`. No se copio ni
amplio ningun permiso, ni se cambiaron limites de consumo. El acceso existente
a Hugging Face se verifico como cuenta MikeMaki1763, permiso write. La credencial
se uso solo para autenticacion; no se mostro. No se leyeron `.env` ni CLAVES.txt.

## Codigo Publicado

- Space backend: https://huggingface.co/spaces/MikeMaki1763/literalevel
- Revision anterior: `e3a79cb90240610b260259401c00be03bed786d2`.
- Revision nueva: `e56cf08b2de2c98542963cf2ae3286313d23f684`.
- Archivos exactos: `app/api.py` y `app/voz.py`.
- Fuentes locales: `a87caa8` (temporal antes del cobro) y `71e4b52`
  (deduplicacion TTS entre hilos y migracion SQLite serializada).
- Se comparo el diff remoto antes de publicar: solo esos arreglos.
- No se tocaron README, entrypoint, requirements, hardware, plan ni secretos
  del Space. No se publico catalogo sucio ni se fusiono la rama boca3d.
- Un commit remoto, sin compras ni llamadas de prueba a OpenAI.

El script `tools/desplegar_app.py` omitia api.py y no impedia subir cambios
sin commit. Los commits `7e68a54` y `0aec4ee` agregan seleccion exacta `--solo`,
guardas Git, `parent_commit` para no pisar una revision remota concurrente,
congelacion del contenido y escaneo de esos mismos bytes antes del SDK.
No se ejecutaron rutas de subida de audios ni cambios de LFS en este despliegue.

## Pruebas Locales

El Python de Anaconda tenia un SDK de Hugging Face incompatible con el script
actual. Se creo un venv independiente en
`C:/Users/laura/.literalevel-dev/despliegue`, Python 3.11.15; no se modifico el
entorno de Claude. Gradio 6.26.0, FastAPI 0.141.1, huggingface_hub 1.31.0.
El primer intento de instalar dependencias vencio por timeout; el segundo
termino correctamente. No se instalaron modelos ni paquetes del stack NLP.

Comandos, usando el python del venv:

```powershell
python -X utf8 -m unittest pruebas_despliegue pruebas_voz_concurrencia pruebas_portadas
python -X utf8 pruebas_api.py
python -X utf8 tools/desplegar_app.py --seco --solo app/api.py app/voz.py
python -X utf8 tools/desplegar_app.py --solo app/api.py app/voz.py
python -X utf8 tools/desplegar_app.py --estado
python -X utf8 tools/desplegar_app.py --seco --solo app/api.py app/voz.py
```

- Despliegue 10/10 y concurrencia de voz 7/7, unittest.
- Portadas 11/11, runner propio al importar el modulo.
- API completa: **32/35**. Paso la prueba real FastAPI del temporal antes
  del cobro, ademas de limites, aislamiento, rutas de audio y errores.
- Fallaron `palabra_sin_clave_no_sale_a_la_red`, `cuaderno_aislado` y
  `palabra_escrita_no_se_atribuye_al_libro`. Las consultas devolvian 503 por
  ModuleNotFoundError; el cuaderno no tenia la entrada esperada despues.
  Se reprodujo directamente `consultar(..., usar_openai=False)`: falta spacy.
  Tampoco estan sentence_transformers, en_core_web_sm ni torch en este venv.
  No se maquillo el resultado con mocks ni se atribuye al producto una
  regresion demostrada por estos tres fallos de entorno.

## Verificacion Publicada

Despues de RUNNING_BUILDING y RUNNING_APP_STARTING, el Space llego a RUNNING
con el hardware existente cpu-basic. No se considera un HTTP 200 prueba de
funcionamiento por si solo.

1. `/api/salud`: HTTP 200, application/json, estado ok, API 0.2.0. Tras el
   reinicio, los tres recursos estaban inicialmente sin cargar.
2. `/api/palabra`, sesion nueva sin login, palabra house, oracion
   `The house is near the river.`, etapa diccionario: HTTP 200, ficha de
   Kaikki, sin texto IA, generado_por_ia false, explicacion pendiente false
   y motivo de acceso sin perfil. Esta comprobacion es de disponibilidad,
   no de calidad semantica: vease el pendiente de abajo.
3. `/api/voz`, otra peticion de esa sesion, multipart con audio sintetico
   de 2000 bytes: HTTP 403 por no entrar con perfil, antes de procesar voz.
   No se envio grabacion personal ni se probo correccion pagada.
4. Segunda comparacion del script: **iguales (2): app/api.py, app/voz.py**.
5. Navegador: la pagina oficial del front carga Angular; Empezar a leer abre
   Alicia, CHAPTER I, 2184 palabras, navegacion y texto visibles. Se cerro la
   indicacion inicial; no se entro con cuentas ni se activo microfono.
   Dominio correcto: https://mikemaki1763-literalevel-front.static.hf.space/
   El dominio sin `.static` dio 404 y no es el enlace de esta app.

## Pendientes Y Limites

La consulta house eligio `The people who live in a house; a household.`
para una frase sobre ubicacion de un edificio, similitud 0.4748 entre 26
candidatos, dudoso false. Caso reproducible para la siguiente auditoria
de `_elegir_sentido`; no se cambio lexicon en este despliegue. La prueba
remota no demuestra ausencia de todos los fallos de acepcion ni de XSS.

No se probo proveedor OpenAI real, microfono fisico, recuperacion tras un
fallo real del disco remoto ni deduplicacion TTS entre procesos. Se mantienen
los pendientes API documentados en el relevo. La rama Blender y la tanda
FLUX siguen en el estado y con los limites de ese informe.

Si fuera necesario revertir este despliegue, recuperar solo estos dos archivos
de la revision anterior indicada arriba, comparar la revision remota actual
y publicar el reemplazo con control de padre. No resetear el Space completo
ni los cambios ajenos del repositorio local.

Claude tiene el enlace al relevo en CLAUDE.md. No se afirma haber reanudado
automaticamente una sesion suya ni enviado un mensaje directo confirmado.
