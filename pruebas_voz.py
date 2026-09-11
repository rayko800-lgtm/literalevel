"""Pruebas de app/voz.py: el ciclo completo con llamadas reales a la API.

No hay microfono, asi que el audio de prueba se genera con tts-1 y se
transcribe de verdad con whisper-1: es la unica forma honesta de comprobar
que transcribir_audio() funciona contra el servicio real, no un mock.

Usa una base de datos SQLite aparte (no la de produccion) para no ensuciar
~/.literalevel/voz.db con datos de prueba.
"""
import os, sys, tempfile
import uuid

sys.path.insert(0, "app")
import config
import voz

config.cargar()
TIENE_CLAVE = bool(config.obtener("OPENAI_API_KEY"))
print(f"OPENAI_API_KEY presente: {TIENE_CLAVE}")

FALLOS = []


def check(nombre, cond, detalle=""):
    estado = "OK" if cond else "FALLO"
    print(f"  [{estado}] {nombre}" + (f" -- {detalle}" if detalle else ""))
    if not cond:
        FALLOS.append(nombre)


# --- 1) normalizar_palabras: minusculas, sin puntuacion, con contracciones
print("\n=== normalizar_palabras ===")
n = voz.normalizar_palabras("Well, I don't think so - really!")
print(" ", n)
check("quita puntuacion sobrante", n == ["well", "i", "don't", "think", "so", "really"], str(n))


# --- 2) evaluar_pronunciacion con errores deliberados (sin red) ----------
print("\n=== evaluar_pronunciacion (errores deliberados, sin red) ===")
objetivo = "The quick brown fox jumps over the lazy dog"
dicho_mal = "The quick brown fix jumped over the lazy dog"
ev = voz.evaluar_pronunciacion(objetivo, dicho_mal)
print(f"  objetivo : {ev.palabras_objetivo}")
print(f"  dicho    : {ev.palabras_dichas}")
print(f"  falladas : {ev.palabras_falladas}")
print(f"  puntuacion: {ev.puntuacion}")
# "fox"->"fix" y "jumps"->"jumped" son sustituciones; el resto es identico.
check("detecta exactamente 'fox' y 'jumps' como falladas",
      set(ev.palabras_falladas) == {"fox", "jumps"}, str(ev.palabras_falladas))
check("no marca palabras correctas como falladas",
      not ({"the", "quick", "brown", "over", "lazy", "dog"} & set(ev.palabras_falladas)))
check("puntuacion intermedia (ni 0 ni 100)", 0 < ev.puntuacion < 100, str(ev.puntuacion))

# Frase identica -> 100 y sin fallos.
ev_perfecta = voz.evaluar_pronunciacion(objetivo, objetivo)
check("frase identica -> 100.0", ev_perfecta.puntuacion == 100.0, str(ev_perfecta.puntuacion))
check("frase identica -> sin palabras falladas", ev_perfecta.palabras_falladas == [])

# Coma de mas no debe penalizar (normalizacion).
ev_coma = voz.evaluar_pronunciacion("Hello, world.", "hello world")
check("puntuacion no penaliza comas/puntos", ev_coma.puntuacion == 100.0, str(ev_coma.puntuacion))

# Se salta una palabra entera -> delete.
ev_salto = voz.evaluar_pronunciacion("I really like this book", "I like this book")
check("palabra saltada se detecta como fallada",
      ev_salto.palabras_falladas == ["really"], str(ev_salto.palabras_falladas))


# --- 3) degradacion sin clave: monkeypatch config.obtener a None --------
print("\n=== degradacion sin OPENAI_API_KEY ===")
_original_obtener = config.obtener
config.obtener = lambda nombre: None
try:
    check("transcribir_audio -> None sin clave", voz.transcribir_audio("no_existe.wav") is None)
    check("explicar_correccion -> None sin clave", voz.explicar_correccion(["fox"]) is None)
    # Una frase que nadie ha generado nunca: sin clave no hay de donde sacarla.
    _nueva = f"a phrase never spoken before {uuid.uuid4().hex}"
    check("generar_audio_correcto -> None sin clave",
          voz.generar_audio_correcto(_nueva) is None)
    # evaluar_pronunciacion no depende de la clave en absoluto.
    ev_sin_clave = voz.evaluar_pronunciacion(objetivo, dicho_mal)
    check("evaluar_pronunciacion sigue funcionando sin clave",
          set(ev_sin_clave.palabras_falladas) == {"fox", "jumps"})
finally:
    config.obtener = _original_obtener


# --- 4) puntos_debiles: varias repeticiones en una DB de prueba ----------
print("\n=== registrar_fallos / puntos_debiles (DB de prueba) ===")
# Carpeta PROPIA de esta ejecucion, y no un nombre fijo en el temporal del
# sistema. Con el nombre fijo, dos ejecuciones a la vez -que es justo lo que
# hace el banco de mutantes- se pisan el SQLite y sale un `PermissionError`
# que no tiene nada que ver con lo que se esta midiendo: un mutante parecia
# cazado por esta suite cuando lo unico que pasaba era que dos procesos
# abrieron el mismo archivo. Lo encontro la auditoria 16.
_TMP_VOZ = tempfile.mkdtemp(prefix="literalevel_voz_")
db_prueba = os.path.join(_TMP_VOZ, "voz_prueba.db")

voz.registrar_fallos(["fox", "jumps"], ruta=db_prueba)
voz.registrar_fallos(["fox"], ruta=db_prueba)
voz.registrar_fallos(["fox", "the"], ruta=db_prueba)
top = voz.puntos_debiles(10, ruta=db_prueba)
print(" ", top)
top_dict = dict(top)
check("'fox' acumula 3 fallos", top_dict.get("fox") == 3, str(top_dict))
check("'jumps' acumula 1 fallo", top_dict.get("jumps") == 1, str(top_dict))
check("'fox' es la palabra mas debil (orden desc)", top[0][0] == "fox", str(top))

top_limitado = voz.puntos_debiles(1, ruta=db_prueba)
check("limite N funciona", len(top_limitado) == 1, str(top_limitado))
os.remove(db_prueba)


# --- 5) ciclo completo de verdad: tts-1 -> whisper-1 -> comparacion ------
if TIENE_CLAVE:
    print("\n=== ciclo completo con API real (tts-1 + whisper-1) ===")
    frase_prueba = "I would like a cup of coffee, please."
    audio_tmp = os.path.join(_TMP_VOZ, "prueba_voz.mp3")
    ruta_audio = voz.generar_audio_correcto(frase_prueba, ruta_salida=audio_tmp)
    check("generar_audio_correcto devuelve una ruta", ruta_audio is not None, str(ruta_audio))
    check("el archivo de audio existe y no esta vacio",
          ruta_audio is not None and os.path.getsize(ruta_audio) > 1000,
          str(os.path.getsize(ruta_audio)) if ruta_audio else "")

    transcripcion = voz.transcribir_audio(audio_tmp) if ruta_audio else None
    print(f"  transcripcion whisper-1: {transcripcion!r}")
    check("transcribir_audio devuelve texto no vacio",
          bool(transcripcion and transcripcion.strip()), str(transcripcion))

    if transcripcion:
        ev_real = voz.evaluar_pronunciacion(frase_prueba, transcripcion)
        print(f"  puntuacion real: {ev_real.puntuacion}  falladas: {ev_real.palabras_falladas}")
        check("un audio bien generado puntua alto (>=85)", ev_real.puntuacion >= 85,
              str(ev_real.puntuacion))

    # Ciclo end-to-end vía practicar(), con una DB de prueba para no tocar la real.
    db_practicar = os.path.join(_TMP_VOZ, "voz_practicar.db")
    voz.RUTA_DB_POR_DEFECTO_ORIGINAL = voz.RUTA_DB_POR_DEFECTO
    voz.RUTA_DB_POR_DEFECTO = db_practicar
    try:
        sesion = voz.practicar(audio_tmp, frase_prueba)
        check("practicar() transcribe correctamente", sesion.transcripcion_ok)
        print(f"  sesion.evaluacion.puntuacion: {sesion.evaluacion.puntuacion}")
        print(f"  sesion.correccion: {sesion.correccion}")
        print(f"  sesion.audio_correcto: {sesion.audio_correcto}")
    finally:
        voz.RUTA_DB_POR_DEFECTO = voz.RUTA_DB_POR_DEFECTO_ORIGINAL
    if os.path.exists(db_practicar):
        os.remove(db_practicar)

    # --- 6) explicar_correccion con Structured Outputs, con fallos reales
    print("\n=== explicar_correccion (Structured Outputs) ===")
    correccion = voz.explicar_correccion(["thought", "world", "clothes"])
    check("explicar_correccion devuelve una Correccion", isinstance(correccion, voz.Correccion))
    if correccion:
        print(f"  resumen : {correccion.resumen}")
        check("hay un detalle por cada palabra fallada", len(correccion.detalles) == 3,
              str(len(correccion.detalles)))
        for d in correccion.detalles:
            print(f"  - {d.palabra}: sonido={d.sonido_que_falla!r}")
            check(f"detalle de '{d.palabra}' tiene sonido_que_falla no vacio",
                  bool(d.sonido_que_falla.strip()))
            check(f"detalle de '{d.palabra}' tiene como_colocar_la_boca no vacio",
                  bool(d.como_colocar_la_boca.strip()))

    if os.path.exists(audio_tmp):
        os.remove(audio_tmp)
else:
    print("\n(sin OPENAI_API_KEY: se omiten las pruebas que necesitan red)")


# --- resumen --------------------------------------------------------------
print("\n" + "=" * 60)
if FALLOS:
    print(f"FALLARON {len(FALLOS)} comprobaciones:")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("TODO OK")
