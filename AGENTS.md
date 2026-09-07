# LiteraLevel — reglas para agentes

Aquí trabajan **dos agentes a la vez** sobre el mismo repo: Claude Code y Codex.
El afectado de una colisión es Miguel. Lee esto antes de tocar nada.

## Reparto vigente (6 sep 2026)

| Zona | Dueño | Regla |
|---|---|---|
| `app/ui.py` | **Claude Code** | Codex no la edita. Puede leerla para auditar contratos. |
| `app/reader.py`, `app/lexicon.py`, `app/voz.py` | **Codex** | Está auditándolos. Claude no los edita sin avisar. |
| `app/scoring.py`, `app/perfil.py`, `app/catalogo.py`, `app/config.py` | compartido | Quien entre, avisa en el commit. |
| `modelo_v4/`, `kaikki_diccionario.db` | nadie | Datos. No se regeneran ni se versionan. |

**Si vas a cambiar la firma pública de un módulo, dilo en el mensaje de commit
en la primera línea.** `ui.py` depende de todas ellas y se rompe en silencio.

## Lo que no se toca

- **El modelo v4 es final y no se reentrena.** La fase es la interfaz.
- **Oxford Dictionaries está descartado** (sus claves dan HTTP 403). El
  diccionario es Kaikki/Wiktionary en SQLite local, sin límites de API. OpenAI
  solo aporta la explicación contextual y gramatical: tiene prohibido
  redefinir la palabra.
- **`app/perfil.py` no puede llamarse `profile.py`**: taparía el módulo
  `profile` de la stdlib y rompe `import cProfile` dentro de torch.
- `CLAVES.txt` y `.env` llevan claves reales y están en `.gitignore`.

## Contrato entre módulos

Escalas: la **pública es 0..2** (la que ve el usuario y la que consumen
`catalogo.buscar`, `lexicon.consultar` y `perfil.Perfil.nivel`); la interna del
modelo es 0..5. `public_score(y) = clip(y,0,5)*0.4`.

- `scoring.Puntuador(ruta).puntuar(texto) -> Resultado` — lanza `ValueError`
  legible si no es prosa continua.
- `reader.cargar(ruta) -> Libro(titulo, autor, capitulos[])`
- `perfil.desde_cuestionario(dict) / desde_muestra(texto, puntuador) -> Perfil`
- `catalogo.Catalogo().buscar(consulta, nivel_lector, n) -> (libros, aviso)` —
  nunca devuelve vacío en silencio. **El catálogo son 1197 libros, no 12752**:
  `wc -l` engaña porque el campo `hook` lleva saltos de línea entrecomillados.
  Cuéntalo con pandas. Que el 60% sea A1 es deliberado (cuentos graduados de
  StoryWeaver junto a los clásicos de Gutenberg), no un fallo de etiquetado.
- `lexicon.ConsultorLexico().consultar(palabra, oracion, nivel) -> ResultadoLexico`
  — nunca lanza por falta de red o clave; lo que falte va en `.avisos`.
- `voz.practicar(ruta_audio, frase) -> SesionVoz`

Regla común: **degradación elegante**. Sin `OPENAI_API_KEY` la app funciona
(diccionario, IPA, audio de Wiktionary, buscador y puntuación no usan red); lo
que se apaga es la explicación contextual y la voz.

## Arranque

```bash
python -X utf8 app/ui.py      # la app
python -X utf8 tests_smoke.py       # lógica sin modelo
python -X utf8 validar_local.py     # la prueba para el profesor
python -X utf8 pruebas_voz.py
python -X utf8 pruebas_lexicon.py
```

`ui.py` carga los tres recursos pesados (modelo 328 MB, embeddings del
catálogo, diccionario 243 MB + spaCy + MiniLM) **al primer uso, no al
arrancar**. No lo cambies a carga anticipada: la demo se vuelve inusable.

## Antes de "arreglar" una llamada a una librería

Este stack va por delante de lo que cualquier modelo recuerda de memoria:
gradio **6.26**, transformers **5.16**, pandas **3.0**, openai **3.8**,
torch 2.14. Verifica la firma real antes de tocarla:

```bash
python -c "import gradio as gr, inspect; print(inspect.signature(gr.Blocks.launch))"
```

Caso comprobado: en Gradio 6 `theme` va en `launch()` y **ya no existe** en el
constructor de `Blocks`; `Textbox` tampoco acepta `show_copy_button`. El código
actual es correcto. Quien lo "corrija" de memoria hacia Gradio 4, lo rompe.

## Despliegue (punto 6, lo único que falta)

Consumo medido en local: **~1,05 GB de RSS** con el modelo y los embeddings
del catálogo cargados; con spaCy y el diccionario encima, pico realista de
**1,2-1,5 GB**. En disco, 562 MB (modelo 328 + diccionario 233 + CSV 0,9).
Eso descarta cualquier plan de 512 MB (Render free, Koyeb free).

**Hugging Face cambió el tier gratuito a mediados de 2026.** La doc del Hub
dice literalmente: *"Static Spaces are free for everyone. Gradio and Docker
Spaces run on compute and require a paid plan to create: PRO for personal
accounts... Free personal accounts in good standing can still host up to 2
Gradio Spaces running on ZeroGPU."* La guía de Gradio y los artículos de
"pricing 2026" siguen diciendo que es gratis: **están desactualizados**.
CPU Basic es 2 vCPU / 16 GB RAM / 50 GB de disco efímero, y duerme por
inactividad.

Cuatro cosas que hay que resolver antes de subir, sea cual sea la plataforma:

1. **`app/` no es un paquete.** Los módulos se importan planos y solo funciona
   porque `ui.py` se mete su directorio en `sys.path`. Un Space espera `app.py`
   en la raíz: hace falta un envoltorio.
2. **La ruta del diccionario está clavada.** `ui.py` sí permite mover el modelo
   (`LITERALEVEL_MODELO`), pero `lexicon.py` fija
   `RUTA_DICCIONARIO = RAIZ / "kaikki_diccionario.db"`. Con los datos montados
   como volumen de solo lectura hay que poder cambiarla por entorno.
   **Es archivo de Codex: que lo parametrice quien lo lleva.**
3. **Los 562 MB están en `.gitignore`** y deben seguir estándolo. Suben como
   repo de modelo y repo de dataset aparte, montados de solo lectura.
4. **Las cachés de `~/.literalevel/`** (lexicon y voz) son disco efímero en un
   Space: se borran en cada reinicio. Es aceptable porque son caché, pero la
   primera consulta tras cada despertar irá lenta.
