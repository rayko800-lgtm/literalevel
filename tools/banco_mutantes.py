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
BASE = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "literalevel_banco"
NL = chr(10)

COPIAR = ["app", "pruebas_extremas.py", "pruebas_integracion.py", "tests_smoke.py",
          "pruebas_ficha.py", "pruebas_perfil.py", "pruebas_lexicon.py",
          "main.py", "validar_local.py", "catalogo_recomendaciones.csv"]

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
    ("F15-s5-nota", "app/ui.py",
     "    return (f" + chr(34) + "Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:"
     + chr(92) + "n" + chr(92) + "n" + chr(34) + NL +
     "            + _tabla_libros(libros, vacio=si_no_hay, nota=NOTA_NIVEL_HEREDADO),",
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
    r = subprocess.run([sys.executable, "-X", "utf8"] + suite.split(),
                       cwd=destino, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=1800)
    # Cada suite dice sus fallos a su manera, y el banco tiene que entender
    # las dos. `pruebas_extremas` y `pruebas_lexicon` los listan con "- ";
    # `pruebas_ficha` y `pruebas_perfil` escriben "  FALLA <nombre>". Sin la
    # segunda, un mutante cazado por `ficha` salia como "cazado por OTRA: []",
    # que es peor que un fallo: parece que lo caza cualquier cosa menos la
    # prueba que se escribio para el.
    fallos = [l.split(":", 1)[0].strip(" -")
              for l in r.stdout.splitlines() if l.strip().startswith("- ")]
    fallos += [l.strip()[len("FALLA"):].split("  ->")[0].strip()
               for l in r.stdout.splitlines() if l.strip().startswith("FALLA")]
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
