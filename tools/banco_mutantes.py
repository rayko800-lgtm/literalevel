"""Banco de mutantes: rompe una cosa a proposito y exige que falle LA prueba.

    python tools/banco_mutantes.py            # control + todos
    python tools/banco_mutantes.py S1 S2      # solo los que empiecen asi

**Vive en el repositorio y no en el scratchpad, y eso es a proposito.** La
version anterior estaba en `scratchpad/mutar.py`, un subagente auditor escribio
SU arnes de mutacion con el mismo nombre en el mismo directorio -el scratchpad
es compartido- y se llevo el mio por delante. Un archivo que cuesta una hora de
escribir no puede vivir donde otro proceso puede pisarlo sin avisar.

REGLAS QUE SE APRENDIERON A GOLPES

1. Se copia el arbol DE VERDAD -no solo `app/`-, incluido
   `catalogo_recomendaciones.csv` y los `catalogo_emb_*.npy`. Si falta un
   archivo, fallan pruebas ajenas en TODAS las copias y los mutantes parecen
   cazados sin estarlo.
2. El control sin mutar tiene que pasar la suite entera ANTES de mutar nada.
3. No basta con "la suite falla": el fallo tiene que venir de la prueba que se
   espera. Se compara el nombre.
"""
import os
import pathlib
import shutil
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
# Las copias del arbol pesan ~2 GB (una por grupo de mutantes). En C: el disco se
# lleno (14 sep 2026): van a D: si existe; LITERALEVEL_BANCO manda sobre todo.
if os.environ.get("LITERALEVEL_BANCO"):
    BASE = pathlib.Path(os.environ["LITERALEVEL_BANCO"])
elif os.name == "nt" and pathlib.Path("D:/").exists():
    BASE = pathlib.Path("D:/literalevel_tmp/banco")
else:
    BASE = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "literalevel_banco"
NL = chr(10)

# `pruebas_corpus.py` y `tools` hacen falta para los mutantes C3: sin ellos, la
# primera pasada del 12 de septiembre de 2026 dio los ocho "cazado por OTRA: []"
# porque la suite no existia en la copia, no porque cazara nada.
COPIAR = ["app", "tools", "pruebas_extremas.py", "pruebas_integracion.py", "tests_smoke.py",
          "pruebas_ficha.py", "pruebas_perfil.py", "pruebas_lexicon.py", "pruebas_corpus.py",
          "main.py", "validar_local.py", "catalogo_recomendaciones.csv",
          # pruebas_api y el catalogo con el que corre: sin ellos, un mutante de
          # api.py salia «cazado por OTRA: []» porque la suite no estaba en la
          # copia (14 sep 2026, C3-bloque-sin-marca-*).
          "pruebas_api.py", "catalogo_medido.csv", "capitulos_medidos.parquet",
          "catalogo_externo.csv", "corpus_abierto.parquet", "avisos_contenido.csv",
          "correcciones_catalogo.csv"]

# (id, archivo, viejo, nuevo, prueba que debe cazarlo)
MUTANTES = [
    ("S1-medir", "app/ui.py",
     "    except Exception as e:" + NL + "        yield _aviso(e)" + NL + "        return",
     "    except (ValueError, OSError) as e:" + NL + "        yield _aviso(e)" + NL + "        return",
     "el modelo puede reventar de cualquier forma"),
    ("S1-analisis", "app/ui.py",
     "            except Exception as e:" + NL +
     "                # Un capitulo que revienta no puede llevarse el libro entero:",
     "            except (ValueError, OSError) as e:" + NL +
     "                # Un capitulo que revienta no puede llevarse el libro entero:",
     "el modelo puede reventar de cualquier forma"),
    ("S2-cache", "app/catalogo.py",
     "DIR_CACHE = config.dir_datos()",
     'DIR_CACHE = Path(os.path.expanduser("~")) / ".literalevel"',
     "una sola raiz de datos, configurable"),
    # --- Los trece que sobrevivieron a la auditoria 14 --------------------
    ("M26-marcapaginas", "app/ui.py",
     "    return Path(_archivo_lector(" + chr(34) + "sesion.json" + chr(34) + ", peticion))",
     "    return RUTA_SESION",
     "el marcapaginas y el cuaderno son de cada lector"),
    ("M27-cuaderno", "app/ui.py",
     "            ruta=_archivo_lector(" + chr(34) + "cuaderno.db" + chr(34) + ", peticion))",
     "            ruta=_archivo_lector(" + chr(34) + "cuaderno.db" + chr(34) + "))",
     "el marcapaginas y el cuaderno son de cada lector"),
    ("M21-cuestionario", "app/ui.py",
     "    claves = _claves_cuestionario()",
     "    claves = _claves_cuestionario()[::-1]",
     "cada respuesta del cuestionario va a su pregunta"),
    ("M33-por-nivel", "app/catalogo.py",
     "        d = self.df[np.abs(obj - nivel_lector) <= holgura]",
     "        d = self.df",
     "sorprendeme filtra de verdad por nivel"),
    ("M02-opciones", "app/ui.py",
     "                for b in libros if str(b.id).upper().startswith(\"PG\")]",
     "                for b in [] if str(b.id).upper().startswith(\"PG\")]",
     "un libro de Gutenberg se puede abrir desde la tabla"),
    ("M32-sinopsis", "app/ui.py",
     "    datos = _sinopsis_guardada(libro)",
     "    datos = None",
     "la sinopsis guardada no se vuelve a pagar"),
    ("M03-cubos", "app/ui.py",
     "    clave = f" + chr(34) + "{cubo}:{_ip(peticion)}" + chr(34) + NL +
     "    ahora = time.time()" + NL +
     "    with _CANDADO_GASTO:" + NL +
     "        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]" + NL +
     "        if len(marcas) >= tope:",
     "    clave = f" + chr(34) + "lexico:{_ip(peticion)}" + chr(34) + NL +
     "    ahora = time.time()" + NL +
     "    with _CANDADO_GASTO:" + NL +
     "        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]" + NL +
     "        if len(marcas) >= tope:",
     "cubos distintos no se mezclan"),
    ("M01-paletas", "app/ui.py",
     "def _css_paleta(clave: str) -> str:",
     "def _css_paleta(clave: str) -> str:" + NL + "    return " + chr(34) * 2,
     "todas las paletas dan css"),
    ("M28-pronunciacion", "app/ui.py",
     "    fallo = set(ev.palabras_falladas)",
     "    fallo = set()",
     "marca bien y mal"),
    # --- Auditoria 15 ------------------------------------------------------
    ("F15-nan", "app/ui.py",
     "    return (isinstance(x, (int, float)) and not isinstance(x, bool)" + NL +
     "            and math.isfinite(x))",
     "    return isinstance(x, (int, float)) and not isinstance(x, bool)",
     "los archivos que escribe la app no la tumban"),
    ("F15-sinopsis-lista", "app/ui.py",
     "            fuera[k] = " + chr(34) + " " + chr(34) +
     ".join(str(x) for x in v) if isinstance(v, list) else str(v)",
     "            fuera[k] = v if isinstance(v, list) else str(v)",
     "los archivos que escribe la app no la tumban"),
    ("F15-perfil-carpeta", "app/perfil.py",
     "    except (json.JSONDecodeError, TypeError, ValueError, OSError):",
     "    except (json.JSONDecodeError, TypeError, ValueError):",
     "los archivos que escribe la app no la tumban"),
    # Se muta la FUNCION y no sus tres usos: el texto de la llamada aparece
    # tres veces y el arnes exige una sola coincidencia, a proposito.
    ("F15-curva-palabras", "app/ui.py",
     "    try:" + NL +
     "        return ficha.caracteristicas(libro).palabras or libro.palabras",
     "    try:" + NL +
     "        return libro.palabras",
     "la pantalla del libro no se contradice ni en la curva"),
    ("F15-abreviaturas", "app/ui.py",
     "    for f in _oraciones(_sin_encabezado(limpio)):",
     "    for f in scoring.SENT_RE.findall(limpio):",
     "las frases no se parten en las abreviaturas"),
    ("F15-umbral-duda", "app/ui.py",
     "AFINIDAD_DUDOSA = 0.40",
     "AFINIDAD_DUDOSA = 0.35",
     "la ficha no promete una pronunciacion que no existe"),
    ("F15-aviso-audio", "app/ui.py",
     "    if not r.audio_generado:",
     "    if False:",
     "la ficha no promete una pronunciacion que no existe"),
    ("S3-tts", "app/ui.py",
     'elif puede and getattr(r, "llamadas_de_pago", 0) == 0:',
     'elif puede and getattr(r, "desde_cache", False):',
     "el cupo cuadra con las llamadas de pago"),
    ("M09-sin-clave", "app/ui.py",
     "        if config.falta():",
     "        if False:",
     "el cupo no baja sin clave de OpenAI"),
    ("M10-sinopsis", "app/ui.py",
     'if va_a_costar and not _dentro_del_limite(' + NL +
     '                peticion, "sinopsis", LIMITE_SINOPSIS_HORA):',
     'if not _dentro_del_limite(' + NL +
     '                peticion, "sinopsis", LIMITE_SINOPSIS_HORA):',
     "el cubo por hora solo cuenta lo que cuesta dinero"),
    ("M39-lexico", "app/ui.py",
     'if va_a_costar and not _dentro_del_limite(peticion, "lexico",',
     'if not _dentro_del_limite(peticion, "lexico",',
     "el cubo por hora solo cuenta lo que cuesta dinero"),
    ("M26-tope-cero", "app/cuentas.py",
     'if cuenta.tope == 0:' + NL + '        return True, ""',
     'if cuenta.tope != 0:' + NL + '        return True, ""',
     "un perfil sin tope puede gastar"),
    ("M06-ventana", "app/ui.py",
     "_VENTANA = 3600.0",
     "_VENTANA = 1.0",
     "el tope por hora dura una hora"),
    ("M29-min-words", "app/scoring.py",
     "MIN_WORDS = 150",
     "MIN_WORDS = 1",
     "un texto de veinte palabras no se puntua"),
    ("M35-boilerplate", "app/ficha.py",
     "limpio = sin_licencia(capitulo.texto)",
     "limpio = capitulo.texto",
     "la licencia se quita antes de decidir si es licencia"),
    ("M49-portadilla", "app/ui.py",
     "    inicial = next((i for i, c in enumerate(libro.capitulos) if _cuerpo(c)),"
     + NL + "                   next((i for i, c in enumerate(libro.capitulos)"
     + NL + "                         if c.palabras >= 500), 0))",
     "    inicial = 0",
     "abrir un libro no cae en la portadilla"),
    ("M46-oracion", "app/ui.py",
     'oracion = (oracion_manual or "").strip()[:LIMITE_ORACION]',
     'oracion = (oracion_manual or "").strip()',
     "lo que viaja a OpenAI va recortado"),
    ("M20-cola", "app/ui.py",
     'b_medir.click(_medir, [est_libro, cap, escala], medicion_md,' + NL +
     '                              concurrency_id="modelo", concurrency_limit=1)',
     'b_medir.click(_medir, [est_libro, cap, escala], medicion_md)',
     "la cola admite a mas de uno"),
    ("S2-titulo", "app/reader.py",
     "        if sirve(cand):",
     "        if cand and cand.casefold() != titulo_libro.casefold():",
     "la cabecera corrida de Gutenberg no es el titulo del capitulo"),
    ("S2-portadilla", "app/ficha.py",
     "if _INICIO_PG.search(capitulo.texto) and not scoring.continuous_prose(limpio)[0]:",
     "if False:",
     "la cabecera corrida de Gutenberg no es el titulo del capitulo"),
    ("S8-ruta", "app/ui.py",
     'if not isinstance(d.get("ruta"), str):',
     "if False:",
     "un archivo de sesion con la forma torcida no tumba el arranque"),
    ("S8-analisis", "app/ui.py",
     'or not _es_numero(f.get("dificultad"))):',
     'or "dificultad" not in f):',
     "un analisis guardado a medias no tumba la ficha"),
    ("S7-holgura", "app/perfil.py",
     "        return (round(max(self.nivel - HOLGURA, 0.0), 3)," + NL +
     "                round(min(self.nivel + HOLGURA, 2.0), 3))",
     "        return (round(max(self.nivel - 0.10, 0.0), 3), self.objetivo)",
     "las dos pestanas prometen el mismo rango"),
    ("n2-infinito", "app/perfil.py",
     "if not math.isfinite(p.nivel) or not 0.0 <= p.nivel <= 2.0:",
     "if False:",
     "un perfil con nivel infinito no se carga"),
    ("n3-poda", "app/ui.py",
     "        _LECTOR_POR_SESION.pop(str(sesion), None)" + NL +
     "        _LECTOR_POR_SESION[str(sesion)] = limpio",
     "        _LECTOR_POR_SESION[str(sesion)] = limpio",
     "la poda de sesiones no tira al que sigue leyendo"),
    ("n3-poda-consulta", "app/ui.py",
     "            _LECTOR_POR_SESION.pop(str(sesion), None)" + NL +
     "            _LECTOR_POR_SESION[str(sesion)] = propio",
     "            pass",
     "la poda de sesiones no tira al que sigue leyendo"),
    ("n5-descargas", "app/ui.py",
     "    if not _esta_cacheado(id_libro) and not _dentro_del_limite(",
     "    if False and not _dentro_del_limite(",
     "las descargas nuevas tienen tope por hora"),

    # --- Los veintidos que sobrevivieron a la auditoria 15 ----------------
    # Cuatro familias: los datos de un lector que se le dan a todos (01-06),
    # las devoluciones del cupo en el resumen (08, 09), las constantes del
    # modelo aseveradas contra si mismas (14-17) y las promesas del documento
    # que no probaba nadie (18-23, 31, 32, 39, 40).
    ("F15-01-sesion", "app/ui.py",
     '    return str(_lector_de_sesion(h) or h or "local")',
     '    return "local"',
     "la sesion de pago es de cada visitante"),
    ("F15-02-estanteria", "app/ui.py",
     '    todos = biblioteca.listar(_archivo_lector("biblioteca.json", peticion))',
     '    todos = biblioteca.listar(_archivo_lector("biblioteca.json"))',
     "la estanteria, la voz y el perfil son de cada lector"),
    ("F15-03-debiles", "app/ui.py",
     '        filas = voz.puntos_debiles(n=15, ruta=_archivo_lector("voz.db", peticion))',
     '        filas = voz.puntos_debiles(n=15, ruta=_archivo_lector("voz.db"))',
     "la estanteria, la voz y el perfil son de cada lector"),
    ("F15-04-fallos", "app/ui.py",
     '                                 ruta=_archivo_lector("voz.db", peticion))',
     '                                 ruta=_archivo_lector("voz.db"))',
     "la estanteria, la voz y el perfil son de cada lector"),
    ("F15-05-biblioteca", "app/ui.py",
     "                      capitulo=inicial, palabras=libro.palabras," + NL +
     '                      ruta=_archivo_lector("biblioteca.json", peticion))',
     "                      capitulo=inicial, palabras=libro.palabras," + NL +
     '                      ruta=_archivo_lector("biblioteca.json"))',
     "la estanteria, la voz y el perfil son de cada lector"),
    ("F15-06-perfil", "app/ui.py",
     "        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or " +
     chr(34) + chr(34) + ")" + NL +
     '        p.guardar(_archivo_lector("perfil.json", peticion))',
     "        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or " +
     chr(34) + chr(34) + ")" + NL +
     '        p.guardar(_archivo_lector("perfil.json"))',
     "la estanteria, la voz y el perfil son de cada lector"),
    ("F15-08-constructor", "app/ui.py",
     "            cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))" + NL +
     '            yield _aviso(f"No pude preparar el resumen ({type(e).__name__}). "',
     '            yield _aviso(f"No pude preparar el resumen ({type(e).__name__}). "',
     "el resumen devuelve el uso cuando no sale a la red"),
    ("F15-09-sin-red", "app/ui.py",
     '            if causa in ("sin_red", "sin_pasajes"):' + NL +
     "                cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))",
     "            if False:" + NL +
     "                cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))",
     "el resumen devuelve el uso cuando no sale a la red"),
    ("F15-14-clip", "app/scoring.py",
     "            fuera.extend(float(v) for v in np.clip(np.atleast_1d(salida), 0, 5))",
     "            fuera.extend(float(v) for v in np.atleast_1d(salida))",
     "el recorte va dentro del sumatorio"),
    ("F15-15-bloques", "app/scoring.py",
     "MAX_BLOCKS_PER_DOC = 8",
     "MAX_BLOCKS_PER_DOC = 800",
     "las ventanas son las del entrenamiento"),
    ("F15-16-ventana", "app/scoring.py",
     "BLOCK_WORDS = 250",
     "BLOCK_WORDS = 200",
     "las ventanas son las del entrenamiento"),
    ("F15-17-holgura", "app/perfil.py",
     "HOLGURA = 0.25",
     "HOLGURA = 0.5",
     "las dos pestanas prometen el mismo rango"),
    ("F15-18-portada", "app/reader.py",
     '            caps.append(Capitulo("Antes del primer capítulo", preambulo))',
     '            caps.append(Capitulo("Preámbulo", preambulo))',
     "la portada de un txt se llama siempre igual"),
    ("F15-19-licencia", "app/ui.py",
     "        r = puntuador().puntuar(ficha.sin_licencia(c.texto))",
     "        r = puntuador().puntuar(c.texto)",
     "medir un capitulo no puntua la licencia"),
    ("F15-20-escape", "app/ui.py",
     '                  f\'<div class="ll-f">{_html.escape(_recortar(a.oracion, 220))}</div>\']',
     '                  f\'<div class="ll-f">{_recortar(a.oracion, 220)}</div>\']',
     "la tarjeta del cuaderno escapa el html"),
    ("F15-21-tabla", "app/ui.py",
     "| 1.00 – 1.40 | **B2** | novela adulta corriente |",
     "| 1.00 – 1.50 | **B2** | novela adulta corriente |",
     "la tabla que ve el lector es la del codigo"),
    ("F15-22-subida", "app/ui.py",
     'TAMANO_MAXIMO_SUBIDA = "20mb"',
     'TAMANO_MAXIMO_SUBIDA = "20gb"',
     "el tope de subida es el que se declara"),
    ("F15-23-peso-nivel", "app/catalogo.py",
     "               peso_nivel: float = 0.3, n: int = 10,",
     "               peso_nivel: float = 0.0, n: int = 10,",
     "la casilla de acercar al nivel hace algo"),
    ("F15-31-pasaje", "app/ficha.py",
     "    return [" + chr(34) + " " + chr(34) +
     ".join(sin_licencia(cuerpo[i].texto).split()[:_TOPE_EXTRACTO])",
     "    return [" + chr(34) + " " + chr(34) +
     ".join(sin_licencia(cuerpo[i].texto).split())",
     "ningun pasaje de la sinopsis viaja entero",
     "pruebas_ficha.py"),
    ("F15-32-frase-voz", "app/ui.py",
     '    frase = (frase or "").strip()[:LIMITE_FRASE_VOZ]',
     '    frase = (frase or "").strip()',
     "la frase de voz no viaja entera"),
    ("F15-39-primera", "app/ui.py",
     "    return candidatas[n % len(candidatas)]",
     "    return candidatas[0]",
     "traer una frase no devuelve siempre la misma"),
    ("F15-40-vistazo", "app/ui.py",
     "        if rapido and len(cuerpo) > RAPIDO_CAPITULOS:",
     "        if False and len(cuerpo) > RAPIDO_CAPITULOS:",
     "el vistazo rapido muestrea de verdad"),

    # --- Y lo que se arreglo el 11 de septiembre: que no se pueda deshacer -
    ("F15-m5a-cupo", "app/lexicon.py",
     "        llamadas_de_pago = (int(audio_pagado)" + NL +
     "                            + int(pedir_explicacion and extra is not None))",
     "        llamadas_de_pago = (int(bool(pedir_audio))" + NL +
     "                            + int(bool(pedir_explicacion)))",
     "una llamada que fallo cobro",
     "pruebas_lexicon.py --sin-openai"),
    ("F15-m5a-tts", "app/lexicon.py",
     "    if ruta.exists():" + NL +
     "        return str(ruta), False",
     "    if ruta.exists():" + NL +
     "        return str(ruta), True",
     "una llamada que fallo cobro",
     "pruebas_lexicon.py --sin-openai"),
    ("F15-m5b-freno", "app/ui.py",
     '    if _cubo_agotado(peticion, "entrar", LIMITE_INTENTOS_ENTRAR):',
     "    if False:",
     "la puerta de entrada tiene freno"),
    ("F15-m5b-ficha", "app/ui.py",
     '            _dentro_del_limite(peticion, "entrar", LIMITE_INTENTOS_ENTRAR)',
     "            pass",
     "la puerta de entrada tiene freno"),
    ("F15-m6c-recarga", "app/ui.py",
     "            cadena = cadena.then(_estado_de_entrada, None, estado_codigo)",
     "            pass",
     "recargar no borra el has entrado como"),
    ("F15-m6d-botones", "app/ui.py",
     "                b_debiles.click(_debiles, None, debiles_md)",
     "                b_debiles.click(_debiles, None, veredicto)",
     "los dos botones de voz no se pisan"),
    ("F15-m6a-tokens", "app/ficha.py",
     '_PALABRA_RE = re.compile(r"[^' + chr(92) + 'W' + chr(92) + 'd_](?:[^'
     + chr(92) + 'W' + chr(92) + 'd_]|[' + "'’-])*" + chr(34) + ", re.UNICODE)",
     '_PALABRA_RE = re.compile(r"[A-Za-z][A-Za-z' + "'’-]{2,}" + chr(34) + ")",
     "lo que mas se repite no son muletillas"),
    # --- Lo que encontro la auditoria 16 ----------------------------------
    ("F16-indice-valor", "app/ui.py",
     "                cap.change(_indice_de, [est_libro, cap], indice)",
     "                cap.change(lambda v: gr.update(value=v), cap, indice)",
     "abrir un libro no pinta un error rojo"),
    # --- Auditoria 17: la regresion sobre los arreglos de la 16 -----------
    ("F17-indice-cero", "app/ui.py",
     "    return gr.update(choices=_opciones_capitulos(libro)," + NL +
     "                     value=int(actual) if valido else None)",
     "    return gr.update(choices=_opciones_capitulos(libro)," + NL +
     "                     value=int(actual) if valido else 0)",
     "abrir un libro no pinta un error rojo"),
    ("F17-dos-mandos", "app/ui.py",
     "    opciones = _opciones_capitulos(libro)",
     "    opciones = [(c.titulo, i) for i, c in enumerate(libro.capitulos)]",
     "abrir un libro no pinta un error rojo"),
    ("F17-final-vacio", "app/ui.py",
     "    yield libro, upd, html, resumen, gr.Tabs(selected=" + chr(34) + "leer" + chr(34) + "), " + chr(34) * 2,
     "    yield libro, gr.update(choices=[], value=None), html, resumen, gr.Tabs(selected=" + chr(34) + "leer" + chr(34) + "), " + chr(34) * 2,
     "abrir un libro no pinta un error rojo"),
    ("F17-rango-invertido", "app/ui.py",
     'tiempo = (f"entre {ficha.reloj(c.minutos(False))} y "' + NL +
     '                      f"{ficha.reloj(c.minutos(True))} de lectura, según lo "',
     'tiempo = (f"entre {ficha.reloj(c.minutos(True))} y "' + NL +
     '                      f"{ficha.reloj(c.minutos(False))} de lectura, según lo "',
     "la ficha no promete un ritmo que no sabe"),
    ("F17-plural", "app/ui.py",
     "               f" + chr(34) + "{n_caps} {'capítulo' if n_caps == 1 else 'capítulos'} · " + chr(34),
     "               f" + chr(34) + "{n_caps} capítulos · " + chr(34),
     "la pantalla del libro no se contradice"),
    ("F17-libro-lee-cap", "app/ui.py",
     "                est_libro.change(_indice_de, est_libro, indice)",
     "                est_libro.change(_indice_de, [est_libro, cap], indice)",
     "abrir un libro no pinta un error rojo"),
    ("F17-retomar-vacia", "app/ui.py",
     "    yield (None, sin_tocar, _html_lectura(" + chr(34) + chr(34) + "), gr.update(), gr.Tabs()," + NL +
     "           " + chr(34) + "Abriendo…" + chr(34) + ")",
     "    yield (None, vacio, _html_lectura(" + chr(34) + chr(34) + "), gr.update(), gr.Tabs()," + NL +
     "           " + chr(34) + "Abriendo…" + chr(34) + ")",
     "abrir un libro no pinta un error rojo"),
    ("F17-lector-tirado", "app/ui.py",
     "    quieto = (gr.skip(), sin_tocar, gr.skip(), gr.skip(), gr.Tabs())",
     "    quieto = (None, sin_tocar, _html_lectura(" + chr(34) + chr(34) + "), gr.update(), gr.Tabs())",
     "abrir un libro no pinta un error rojo"),
    ("F16-descarga-vacia", "app/ui.py",
     "    quieto = (gr.skip(), sin_tocar, gr.skip(), gr.skip(), gr.Tabs())",
     "    quieto = (gr.skip(), gr.update(choices=[], value=None), gr.skip(), gr.skip(), gr.Tabs())",
     "abrir un libro no pinta un error rojo"),
    ("F16-indice-select", "app/ui.py",
     "                indice.select(_indice_de, [est_libro, indice], cap)",
     "                indice.select(lambda v: v, indice, cap)",
     "abrir un libro no pinta un error rojo"),
    ("F16-indice-rango", "app/ui.py",
     "    try:" + NL +
     "        valido = 0 <= int(actual) < len(libro.capitulos)" + NL +
     "    except (TypeError, ValueError):" + NL +
     "        valido = False",
     "    try:" + NL +
     "        valido = actual is not None" + NL +
     "    except (TypeError, ValueError):" + NL +
     "        valido = False",
     "abrir un libro no pinta un error rojo"),
    ("F16-voz-sin-clave", "app/ui.py",
     "    if config.falta():" + NL +
     "        return (" + chr(34) + chr(34) + ", _aviso(" + chr(34) +
     "Para corregir la pronunciación hace falta la clave " + chr(34),
     "    if False:" + NL +
     "        return (" + chr(34) + chr(34) + ", _aviso(" + chr(34) +
     "Para corregir la pronunciación hace falta la clave " + chr(34),
     "la practica de voz no cobra sin clave"),
    # --- Capitulos a tu nivel (12 de septiembre de 2026) -------------------
    ("C1-borde", "app/ficha.py",
     "        if dif <= nivel + margen:",
     "        if dif < nivel + margen:",
     "capitulos a tu nivel: el borde del margen entra", "pruebas_ficha.py"),
    ("C1-facilidad", "app/ficha.py",
     '    buenas.sort(key=lambda f: (abs(float(f["dificultad"]) - nivel), int(f["indice"])))',
     '    buenas.sort(key=lambda f: (float(f["dificultad"]), int(f["indice"])))',
     "capitulos a tu nivel: el orden es por cercania, no por facilidad", "pruebas_ficha.py"),
    ("C1-cortos", "app/ficha.py",
     '        if (f.get("palabras") or 0) < minimo_palabras:',
     "        if False:",
     "capitulos a tu nivel: un capitulo corto no se recomienda", "pruebas_ficha.py"),
    ("C1-reto-a-mano", "app/ui.py",
     "        if ficha.dificultad_global(filas) <= p.nivel + perfil_mod.RETO:",
     "        if ficha.dificultad_global(filas) <= p.nivel + 0.5:",
     "las sugerencias de capitulos salen cuando tocan"),
    ("C1-indice-ajeno", "app/ui.py",
     '               if 0 <= int(f["indice"]) < len(libro.capitulos)]',
     '               if True]',
     "las sugerencias de capitulos salen cuando tocan"),
    ("C1-lee-desplegable", "app/ui.py",
     "                est_libro.change(_capitulos_sugeridos, [est_libro, est_perfil],",
     "                est_libro.change(_capitulos_sugeridos, [est_libro, cap],",
     "las sugerencias de capitulos salen cuando tocan"),
    ("C1-salto-suelto", "app/ui.py",
     "                sugeridos.select(_indice_de, [est_libro, sugeridos], cap)",
     "                sugeridos.select(lambda v: v, sugeridos, cap)",
     "las sugerencias de capitulos salen cuando tocan"),
    ("C1-ficha-reto", "app/ui.py",
     "            exigente = nivel_libro > p.nivel + perfil_mod.RETO",
     "            exigente = nivel_libro > p.nivel + 0.6",
     "la ficha no promete un ritmo que no sabe"),
    # --- Fase 2: el catalogo medido y sus capitulos (12 de septiembre) -------
    ("C2-titulo-sin-mirar", "app/ficha.py",
     '        if _titulo_normalizado(c.titulo) != _titulo_normalizado(f.get("titulo", "")):',
     "        if False:",
     "alinear: un titulo distinto en su posicion no alinea", "pruebas_ficha.py"),
    ("C2-cuenta-sin-mirar", "app/ficha.py",
     "    if not cuerpo or len(cuerpo) != len(filas):",
     "    if not cuerpo:",
     "alinear: con distinto numero de capitulos no alinea", "pruebas_ficha.py"),
    ("C2-indice-del-catalogo", "app/ui.py",
     '    return [dict(f, indice=mapa[int(f["capitulo"])]) for f in filas]',
     "    return [dict(f) for f in filas]",
     "el catalogo medido recomienda capitulos sin saltar mal"),
    ("C2-epub-primero", "app/ui.py",
     '        (f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt", ".txt"),' + NL +
     '        (f"https://www.gutenberg.org/ebooks/{num}.txt.utf-8", ".txt"),' + NL +
     '        (f"https://www.gutenberg.org/ebooks/{num}.epub.noimages", ".epub"),',
     '        (f"https://www.gutenberg.org/ebooks/{num}.epub.noimages", ".epub"),' + NL +
     '        (f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt", ".txt"),' + NL +
     '        (f"https://www.gutenberg.org/ebooks/{num}.txt.utf-8", ".txt"),',
     "el catalogo medido recomienda capitulos sin saltar mal"),
    ("C2-sin-excluir", "app/catalogo.py",
     "        d = self.df[(np.abs(obj - nivel_lector) <= holgura) & ~self._excluidos",
     "        d = self.df[(np.abs(obj - nivel_lector) <= holgura)",
     "el catalogo medido recomienda capitulos sin saltar mal"),
    ("C2-sin-literarios", "app/catalogo.py",
     "                    & self._literarios]",
     "                    ]",
     "el catalogo medido recomienda capitulos sin saltar mal"),
    ("C2-sin-id-catalogo", "app/ui.py",
     '    libro.id_catalogo = f"PG{m_pg.group(1)}" if m_pg else None',
     "    libro.id_catalogo = None",
     "el catalogo medido recomienda capitulos sin saltar mal"),
    # --- C3: los corpus libres en el catalogo y en el lector (12 sep 2026) ---
    ("C3-externo-no-entra", "app/catalogo.py",
     "                if len(ext):",
     "                if False:",
     "los externos van al final y no duplican ids", "pruebas_corpus.py"),
    ("C3-externo-duplica", "app/catalogo.py",
     '                ext = ext[~ext["id"].astype(str).isin(set(self.df["id"].astype(str)))]',
     "                pass",
     "los externos van al final y no duplican ids", "pruebas_corpus.py"),
    ("C3-desplegable-solo-pg", "app/ui.py",
     "                for b in libros if _abrible(b.id)]",
     '                for b in libros if str(b.id).upper().startswith("PG")]',
     "el buscador ofrece y deja abrir los cuentos libres", "pruebas_corpus.py"),
    ("C3-cache-por-digitos", "app/ui.py",
     '    if pid and not pid.upper().startswith("PG"):' + NL + "        return _abrible(pid)",
     "    if False:" + NL + "        return _abrible(pid)",
     "la cache no confunde un id externo con uno de Gutenberg", "pruebas_corpus.py"),
    ("C3-libre-no-se-escribe", "app/ui.py",
     '        if abierto and abierto.get("texto"):',
     "        if False:",
     "un libro libre se abre sin descargar nada", "pruebas_corpus.py"),
    ("C3-sin-id-externo", "app/ui.py",
     "        libro.id_catalogo = m_ext.group(1).upper() if m_ext else None",
     "        libro.id_catalogo = None",
     "la cabecera de un libro libre lleva su titulo", "pruebas_corpus.py"),
    ("C3-borra-externo", "app/catalogo.py",
     '            if viejo != cache and (prefijo != "catalogo_emb_" or not viejo.name.startswith("catalogo_emb_ext_")):',
     "            if viejo != cache:",
     "embeddings alineados, y el externo no borra los de Gutenberg", "pruebas_corpus.py"),
    # Los tres arreglos de la auditoria de Codex de esa misma noche.
    ("C3-cache-ext-por-archivo", "app/catalogo.py",
     '            ext = self._embeddings_de("catalogo_emb_ext_", h.hexdigest()[:16], textos[n:])',
     '            ext = self._embeddings_de("catalogo_emb_ext_", _huella(externo), textos[n:])',
     "la cache del externo depende de sus filas efectivas", "pruebas_corpus.py"),
    ("C3-licencia-por-prefijo", "tools/catalogar_corpus.py",
     "    if norma not in LIBRES:",
     '    if not norma.startswith(("cc by", "dominio publico")):',
     "dominio publico con excepcion no entra", "pruebas_corpus.py"),
    ("C3-copia-vieja", "app/ui.py",
     '            if vigente != abierto["texto"]:',
     "            if vigente is None:",
     "una copia vieja de un libro libre se renueva", "pruebas_corpus.py"),
    ("C3-cuela-derechos", "tools/catalogar_corpus.py",
     "    if len(malas):",
     "    if False:",
     "el catalogador aborta si llega un texto con derechos", "pruebas_corpus.py"),
    # Prueba final del 13 sep 2026: el indice enlazado de Andrew Lang salia a un B1.
    ("C3-indices-enlazados", "app/catalogo.py",
     '    r"|linked index|index for works of|\\ban index to all\\b|hyperlinks to all chapters"' + NL,
     "",
     "los indices enlazados de Gutenberg no se recomiendan por nivel", "pruebas_corpus.py"),
    ("C3-aviso-encabeza", "app/catalogo.py",
     "                d = pd.concat([cabeza, d.drop(cabeza.index)])",
     "                pass",
     "un titulo con aviso de contenido no encabeza pero sigue saliendo", "pruebas_corpus.py"),
    # Decision de Miguel del 14 sep 2026: un tercio de las tarjetas para los libres.
    ("C3-libres-sin-hueco", "app/catalogo.py",
     "        huecos = set(range(1, n, CADA_CUANTOS_LIBRE))",
     "        huecos = set()",
     "los textos libres se intercalan en los primeros puestos por nivel", "pruebas_corpus.py"),
    ("C3-libre-con-aviso-arriba", "app/catalogo.py",
     "                if i not in usados and not (puesto < PRIMEROS_SIN_AVISO and aviso[i]):",
     "                if i not in usados:",
     "los textos libres se intercalan en los primeros puestos por nivel", "pruebas_corpus.py"),
    # Reinicio 14: libres por cercania al nivel, y la atribucion fuera al medir.
    ("C3-libres-sin-cercania", "app/catalogo.py",
     "            libres.sort(key=lambda i: (distancia[i], en_bloque[i], i))",
     "            pass",
     "los libres van por cercania al nivel y los medidos solos antes que los de bloque", "pruebas_corpus.py"),
    ("C3-libres-bloque-igual", "app/catalogo.py",
     "            libres.sort(key=lambda i: (distancia[i], en_bloque[i], i))",
     "            libres.sort(key=lambda i: (distancia[i], i))",
     "los libres van por cercania al nivel y los medidos solos antes que los de bloque", "pruebas_corpus.py"),
    ("C3-bloque-sin-marca-tarjeta", "app/api.py",
     '            "medido_en_bloque": getattr(b, "medida", "") == "bloque"}',
     '            "medido_en_bloque": False}',
     "medido en bloque en ficha y tarjeta", "pruebas_api.py"),
    ("C3-bloque-sin-marca-ficha", "app/api.py",
     '        return ui.catalogo().medida_de(ident) == "bloque"',
     "        return False",
     "medido en bloque en ficha y tarjeta", "pruebas_api.py"),
    ("C3-atribucion-medida", "app/ficha.py",
     '    return _ATRIBUCION_LIBRE.sub("", limpio).strip() if limpio else limpio',
     "    return limpio",
     "la atribucion de un texto libre no se mide con el cuento", "pruebas_corpus.py"),
    # Punto 4: el texto servido, limpio; el medido, tal cual.
    ("C3-servido-sin-limpiar", "tools/catalogar_corpus.py",
     '    textos["texto"] = textos["texto"].map(limpiar_para_servir) + "\\n\\n" + textos["atribucion"]',
     '    textos["texto"] = textos["texto"] + "\\n\\n" + textos["atribucion"]',
     "el texto servido sale limpio sin tocar el que se mide", "pruebas_corpus.py"),
    ("C3-estribillo-fuera", "tools/catalogar_corpus.py",
     "    if mitad != w[len(w) // 2:] or len(_FIN_DE_FRASE.findall(\" \".join(mitad))) < 2:",
     "    if mitad != w[len(w) // 2:]:",
     "el texto servido sale limpio sin tocar el que se mide", "pruebas_corpus.py"),
    # Reinicio 16: el buscador (diagnostico de e6) y los textos que no son lectura.
    ("C3-busqueda-nivel-manda", "app/catalogo.py",
     "            orden = np.lexsort((-clave, ~(relevante | nombre), ~nombre))",
     "            orden = np.argsort(-total)",
     "al buscar, el titulo gana y el nivel solo ordena lo relevante", "pruebas_corpus.py"),
    ("C3-titulo-no-gana", "app/catalogo.py",
     "            orden = np.lexsort((-clave, ~(relevante | nombre), ~nombre))",
     "            orden = np.lexsort((-clave, ~(relevante | nombre)))",
     "al buscar, el titulo gana y el nivel solo ordena lo relevante", "pruebas_corpus.py"),
    ("C3-no-lectura-ignorada", "app/catalogo.py",
     '                self._excl = self._excl | d["id"].astype(str).str.strip().str.upper().isin(fuera).to_numpy()',
     "                pass",
     "los textos que no son lectura en ingles no salen al buscar ni al recomendar", "pruebas_corpus.py"),
    ("C3-relleno-distintas", "tools/marcar_no_lectura.py",
     "    if distintas < MIN_DISTINTAS:",
     "    if False:",
     "los textos que no son lectura en ingles no salen al buscar ni al recomendar", "pruebas_corpus.py"),
    ("C3-relleno-ingles", "tools/marcar_no_lectura.py",
     "    if inglesas < MIN_INGLES:",
     "    if False:",
     "los textos que no son lectura en ingles no salen al buscar ni al recomendar", "pruebas_corpus.py"),
    ("C3-correccion-ignorada", "app/catalogo.py",
     '            self.df.loc[ids == pid, "dificultad"] = round(dif, 3)',
     "            pass",
     "la tabla de correcciones se aplica al cargar sin tocar el CSV", "pruebas_corpus.py"),
    ("C3-medidas-sin-cache", "tools/medir_corpus.py",
     "        if k in hechas:" + NL + "            return hechas[k]",
     "        if False:" + NL + "            return hechas[k]",
     "la medicion del corpus es reanudable y reparte como el catalogador", "pruebas_corpus.py"),
    ("C3-nombre-palabra-suelta", "app/catalogo.py",
     "        fuera[i] = mejor * (1.0 - 0.15 * (1.0 - cubiertas / len(pistas)))",
     "        fuera[i] = mejor",
     "un titulo entero gana a los que solo comparten una palabra", "pruebas_corpus.py"),
    ("C3-correccion-sin-curva", "app/catalogo.py",
     "        if arreglo and len(filas) == 1:",
     "        if False:",
     "la tabla de correcciones se aplica al cargar sin tocar el CSV", "pruebas_corpus.py"),
    ("F16-ficha-ritmo", "app/ui.py",
     "        if nivel_libro is None:",
     "        if False:",
     "la ficha no promete un ritmo que no sabe"),
    ("F16-rescate", "app/catalogo.py",
     "_PARECIDO_NOMBRE = 0.75",
     "_PARECIDO_NOMBRE = 0.99",
     "el buscador encuentra un nombre mal escrito"),
    ("F16-umbral", "app/catalogo.py",
     "               minimo_similitud: float = 0.10) -> tuple[list[Libro], str]:",
     "               minimo_similitud: float = 0.0) -> tuple[list[Libro], str]:",
     "el buscador encuentra un nombre mal escrito"),
    ("F16-miles", "app/ficha.py",
     '    return format(int(n), ",").replace(",", ".")',
     '    return format(int(n), ",")',
     "los miles llevan punto, no coma",
     "pruebas_ficha.py"),
    ("F16-muestra", "app/ficha.py",
     "def _muestra(libro, tope_palabras: int = 60000) -> str:",
     "def _muestra(libro, tope_palabras: int = 6000) -> str:",
     "el tope de la muestra es el que se documenta",
     "pruebas_ficha.py"),
    ("F16-usuarios", "app/cuentas.py",
     "    return _analizar(os.environ.get(" + chr(34) + "LITERALEVEL_CUENTAS" +
     chr(34) + ", " + chr(34) + chr(34) + ").strip()," + NL +
     "                     con_nombre=False)[1]",
     "    return _analizar(os.environ.get(" + chr(34) + "LITERALEVEL_CUENTAS" +
     chr(34) + ", " + chr(34) + chr(34) + ").strip()," + NL +
     "                     con_nombre=True)[1]",
     "la pestana publica no dice que usuarios hay"),

    ("F15-s5-nota", "app/ui.py",
     "    return (f" + chr(34) + "Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:"
     + chr(92) + "n" + chr(92) + "n" + chr(34) + NL +
     "            + _tabla_libros(libros, vacio=si_no_hay, nota=_nota_nivel()),",
     "    return (f" + chr(34) + "Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:"
     + chr(92) + "n" + chr(92) + "n" + chr(34) + NL +
     "            + _tabla_libros(libros, vacio=si_no_hay),",
     "la letra del catalogo se declara heredada"),
]


def preparar(destino: pathlib.Path) -> None:
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    for nombre in COPIAR:
        origen = RAIZ / nombre
        if origen.is_dir():
            shutil.copytree(origen, destino / nombre,
                            ignore=shutil.ignore_patterns("__pycache__"))
        elif origen.exists():
            shutil.copy2(origen, destino / nombre)
    for npy in RAIZ.glob("catalogo_emb_*.npy"):
        shutil.copy2(npy, destino / npy.name)


def correr(destino: pathlib.Path, suite="pruebas_extremas.py"):
    """`suite` puede traer argumentos: "pruebas_lexicon.py --sin-openai"."""
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["LITERALEVEL_MODELO"] = str(RAIZ / "modelo_v4")
    env["LITERALEVEL_DICCIONARIO"] = str(RAIZ / "kaikki_diccionario.db")
    # `pruebas_extremas.py` a veces imprime su veredicto y luego no termina de
    # salir. Con `capture_output` eso colgaba el banco hasta el timeout, y el
    # TimeoutExpired lo tumbaba entero: C2-sin-excluir se llevo por delante los
    # dos mutantes que le seguian. Ahora el timeout se come lo ya impreso y
    # sigue; si el veredicto no llego a salir, cuenta como fallo sin nombre.
    try:
        r = subprocess.run([sys.executable, "-X", "utf8"] + suite.split(),
                           cwd=destino, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, timeout=900)
    except subprocess.TimeoutExpired as e:
        salida = e.stdout or ""
        if isinstance(salida, bytes):
            salida = salida.decode("utf-8", "replace")
        verde = ("pruebas extremas pasan" in salida or "pruebas de la ficha pasan" in salida
                 or "pruebas de corpus pasan" in salida)
        r = subprocess.CompletedProcess(e.cmd, 0 if verde else 1, salida, "")
    # Cada suite dice sus fallos a su manera, y el banco tiene que entender
    # las dos. `pruebas_extremas` y `pruebas_lexicon` los listan con "- ";
    # `pruebas_ficha` y `pruebas_perfil` escriben "  FALLA <nombre>". Sin la
    # segunda, un mutante cazado por `ficha` salia como "cazado por OTRA: []",
    # que es peor que un fallo: parece que lo caza cualquier cosa menos la
    # prueba que se escribio para el.
    # Y solo se miran las lineas de DESPUES del titular de fallos. Sin eso,
    # una vinieta de Markdown de cualquier docstring que la suite imprima
    # -empiezan por "- " igual que los fallos- entraba en la lista y el banco
    # decia "cazado por OTRA" citando un texto que no era ningun fallo.
    lineas = r.stdout.splitlines()
    desde = next((i for i, l in enumerate(lineas)
                  if "FALLOS de" in l or "fallo(s)" in l), None)
    cola = lineas[desde:] if desde is not None else []
    fallos = [l.split(":", 1)[0].strip(" -")
              for l in cola if l.strip().startswith("- ")]
    fallos += [l.strip()[len("FALLA"):].split("  ->")[0].strip()
               for l in lineas if l.strip().startswith("FALLA")]
    return r.returncode, fallos, r.stdout


def main():
    pedidos = list(sys.argv[1:])
    BASE.mkdir(parents=True, exist_ok=True)

    control = BASE / "control"
    preparar(control)
    rc, _, salida = correr(control)
    resumen = [l for l in salida.splitlines() if "pruebas extremas" in l]
    print("CONTROL sin mutar:", "verde" if rc == 0 else "ROJO", resumen, flush=True)
    if rc != 0:
        print(salida[-3000:])
        sys.exit("el control no pasa: no tiene sentido mutar nada")
    print(flush=True)

    hechos = [m for m in MUTANTES if not pedidos or any(p in m[0] for p in pedidos)]
    cazados, vivos = [], []
    for mutante in hechos:
        # El sexto elemento es opcional: la suite que tiene que cazarlo, si no
        # es la de extremas. Los mutantes de `lexicon` y de `ficha` no los ve
        # `pruebas_extremas.py`, y sin esto el banco los daba por vivos.
        ident, rel, viejo, nuevo, esperada = mutante[:5]
        suite = mutante[5] if len(mutante) > 5 else "pruebas_extremas.py"
        d = BASE / ident
        preparar(d)
        p = d / rel.replace("/", os.sep)
        t = p.read_text(encoding="utf-8")
        if t.count(viejo) != 1:
            print(f"{ident:22} NO SE PUDO APLICAR: {t.count(viejo)} coincidencias",
                  flush=True)
            vivos.append(ident + " (no aplicado)")
            continue
        p.write_text(t.replace(viejo, nuevo), encoding="utf-8")
        rc, fallos, salida = correr(d, suite)
        acierto = any(esperada in f for f in fallos)
        if acierto:
            estado = "CAZADO por su prueba"
        elif rc != 0:
            estado = "cazado por OTRA: " + str(fallos[:3])
        else:
            estado = "VIVO"
        print(f"{ident:22} {estado}", flush=True)
        (cazados if acierto else vivos).append(ident)
    print(flush=True)
    print(f"cazados por su prueba: {len(cazados)} de {len(hechos)}")
    if vivos:
        print("NO cazados:", vivos)


if __name__ == "__main__":
    main()
