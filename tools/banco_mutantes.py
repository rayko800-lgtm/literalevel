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
          "pruebas_ficha.py", "pruebas_perfil.py", "main.py", "validar_local.py",
          "catalogo_recomendaciones.csv"]

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
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["LITERALEVEL_MODELO"] = str(RAIZ / "modelo_v4")
    env["LITERALEVEL_DICCIONARIO"] = str(RAIZ / "kaikki_diccionario.db")
    r = subprocess.run([sys.executable, "-X", "utf8", suite],
                       cwd=destino, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=1800)
    fallos = [l.split(":", 1)[0].strip(" -")
              for l in r.stdout.splitlines() if l.strip().startswith("- ")]
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
    for ident, rel, viejo, nuevo, esperada in hechos:
        d = BASE / ident
        preparar(d)
        p = d / rel.replace("/", os.sep)
        t = p.read_text(encoding="utf-8")
        if t.count(viejo) != 1:
            print(f"{ident:18} NO SE PUDO APLICAR: {t.count(viejo)} coincidencias",
                  flush=True)
            vivos.append(ident + " (no aplicado)")
            continue
        p.write_text(t.replace(viejo, nuevo), encoding="utf-8")
        rc, fallos, salida = correr(d)
        acierto = any(esperada in f for f in fallos)
        if acierto:
            estado = "CAZADO por su prueba"
        elif rc != 0:
            estado = "cazado por OTRA: " + str(fallos[:3])
        else:
            estado = "VIVO"
        print(f"{ident:18} {estado}", flush=True)
        (cazados if acierto else vivos).append(ident)
    print(flush=True)
    print(f"cazados por su prueba: {len(cazados)} de {len(hechos)}")
    if vivos:
        print("NO cazados:", vivos)


if __name__ == "__main__":
    main()
