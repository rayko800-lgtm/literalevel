"""Pruebas reales de app/lexicon.py: nada de mocks, se ejecuta contra la BD
Kaikki de verdad y, si hay OPENAI_API_KEY, contra OpenAI de verdad.

Demuestra:
  1. IPA UK y US disponibles para varias palabras.
  2. Desambiguacion por contexto: "brook" como sustantivo vs verbo segun la
     oracion, y el phrasal verb "set off" resuelto via particula (prt).
  3. "notwithstanding": el filtro POS deja la lista vacia (spaCy la etiqueta
     ADP, fuera del mapa) y el modulo cae a usar todos los sentidos, tal
     como pide la especificacion.
  4. Cache real: la segunda consulta IDENTICA es mucho mas rapida que la
     primera y `desde_cache=True`.

Si algo no funciona se dice explicitamente, no se maquilla.
"""
from __future__ import annotations

import sys
import tempfile
import time
import uuid
from pathlib import Path

sys.path.insert(0, "app")
import lexicon  # noqa: E402
import config  # noqa: E402


def linea():
    print("-" * 78)


def mostrar(r: lexicon.ResultadoLexico) -> None:
    print(f"  superficie        : {r.palabra_superficie!r}  en  {r.oracion!r}")
    print(f"  lema / buscado     : {r.lema} / {r.lema_buscado}")
    print(f"  pos spaCy / categ. : {r.pos_spacy} / {r.categoria}")
    print(f"  sentido elegido    : {r.sentido}")
    print(f"  etiquetas          : {r.etiquetas_sentido}")
    print(f"  similitud coseno   : {r.similitud}   (candidatos: {r.n_sentidos_candidatos})")
    print(f"  IPA uk / us        : {r.ipa_uk} / {r.ipa_us}")
    print(f"  audio uk / us      : {r.audio_uk} / {r.audio_us}   (generado={r.audio_generado})")
    print(f"  banda lector       : {r.banda_lector}")
    print(f"  frecuencia zipf    : {r.frecuencia_zipf}")
    print(f"  definicion_context : {r.definicion_contextual}")
    print(f"  explicacion_gram.  : {r.explicacion_gramatical}")
    print(f"  explicacion_adapt. : {r.explicacion_adaptada}")
    print(f"  ejemplo_simplific. : {r.ejemplo_simplificado}")
    print(f"  desde_cache        : {r.desde_cache}")
    print(f"  avisos             : {r.avisos}")
    print(f"  completo()         : {r.completo}")


def main() -> int:
    fallos: list[str] = []

    print("=== estado de claves ===")
    print(config.estado())
    tiene_clave = "OPENAI_API_KEY" not in config.falta()
    print(f"OPENAI_API_KEY presente: {tiene_clave}")
    linea()

    print("=== cargando ConsultorLexico (diccionario + cache) ===")
    t0 = time.time()
    consultor = lexicon.ConsultorLexico()
    print(f"cargado en {time.time() - t0:.2f}s")
    linea()

    # --- 1) IPA UK/US en palabras reales -----------------------------
    print("=== 1) IPA UK y US ===")
    for palabra, oracion in [
        ("free", "You are free to leave whenever you want."),
        ("welcome", "You are always welcome in this house."),
    ]:
        r = consultor.consultar(palabra, oracion, nivel=1.0)
        mostrar(r)
        if not r.ipa_uk or not r.ipa_us:
            fallos.append(f"IPA incompleta para '{palabra}': uk={r.ipa_uk} us={r.ipa_us}")
        linea()

    # --- 2) Desambiguacion por contexto ------------------------------
    print("=== 2) Desambiguacion: 'brook' sustantivo vs verbo ===")
    r_sust = consultor.consultar(
        "brook", "A small brook ran behind the old cottage.", nivel=1.0)
    mostrar(r_sust)
    linea()
    r_verbo = consultor.consultar(
        "brook", "He could not brook such an insult from a stranger.", nivel=1.0)
    mostrar(r_verbo)
    linea()

    if r_sust.categoria != "noun":
        fallos.append(f"'brook' sustantivo: categoria detectada fue {r_sust.categoria!r}, esperaba 'noun'")
    if r_verbo.categoria != "verb":
        fallos.append(f"'brook' verbo: categoria detectada fue {r_verbo.categoria!r}, esperaba 'verb'")
    if not r_sust.sentido or not r_verbo.sentido:
        fallos.append("brook: no se eligio sentido en alguno de los dos casos")
    elif r_sust.sentido == r_verbo.sentido:
        fallos.append("brook: se eligio el MISMO sentido en sustantivo y verbo (fallo de desambiguacion)")
    else:
        print("OK: 'brook' eligio sentidos distintos segun el contexto.\n")

    # --- 2b) Phrasal verb "set off" ----------------------------------
    print("=== 2b) Phrasal verb: 'set off' ===")
    r_set_off = consultor.consultar(
        "set off", "The fireworks will set off at midnight over the bay.", nivel=1.0)
    mostrar(r_set_off)
    linea()
    if r_set_off.lema_buscado != "set off":
        fallos.append(
            f"'set off': se esperaba lema_buscado='set off' (via particula prt), salio {r_set_off.lema_buscado!r}")
    else:
        print("OK: la particula 'off' se detecto y 'set off' se busco como frase.\n")
    if not r_set_off.sentido:
        fallos.append("'set off': no se obtuvo ningun sentido")

    # --- 3) Filtro POS vacio: 'notwithstanding' ----------------------
    print("=== 3) Filtro POS vacio -> usa todos los sentidos: 'notwithstanding' ===")
    r_notw = consultor.consultar(
        "notwithstanding", "Notwithstanding the rain, they continued the hike.", nivel=1.6)
    mostrar(r_notw)
    linea()
    if r_notw.categoria is not None:
        fallos.append(
            f"'notwithstanding': se esperaba categoria=None (POS spaCy fuera del mapa), salio {r_notw.categoria!r}")
    if r_notw.n_sentidos_candidatos < 2:
        fallos.append(
            f"'notwithstanding': se esperaban >=2 sentidos candidatos (todas las categorias sin filtrar), salieron {r_notw.n_sentidos_candidatos}")
    if not r_notw.sentido:
        fallos.append("'notwithstanding': no se eligio ningun sentido")
    if not r_notw.categoria and r_notw.n_sentidos_candidatos >= 2:
        print("OK: sin categoria util, se uso el conjunto completo de sentidos.\n")

    # --- 4) Cache real: misma consulta dos veces ----------------------
    # Se usa una cache SQLite temporal y aislada (no la de ~/.literalevel)
    # para garantizar que la 1a consulta es realmente en frio: si se
    # reutilizara la cache por defecto, una ejecucion previa de este mismo
    # script ya habria cacheado la respuesta y la comparacion de tiempos
    # perderia sentido.
    print("=== 4) Cache real (misma palabra, misma oracion, mismo nivel) ===")
    ruta_cache_demo = Path(tempfile.gettempdir()) / f"lexicon_cache_demo_{uuid.uuid4().hex}.db"
    consultor_demo = lexicon.ConsultorLexico(ruta_cache=ruta_cache_demo)
    palabra_cache = "welcome"
    oracion_cache = "You are always welcome in this house."
    try:
        t0 = time.time()
        primera = consultor_demo.consultar(palabra_cache, oracion_cache, nivel=1.0)
        t_primera = time.time() - t0

        t0 = time.time()
        segunda = consultor_demo.consultar(palabra_cache, oracion_cache, nivel=1.0)
        t_segunda = time.time() - t0

        print(f"  1a consulta: {t_primera:.3f}s   desde_cache={primera.desde_cache}")
        print(f"  2a consulta: {t_segunda:.3f}s   desde_cache={segunda.desde_cache}")
        linea()

        if tiene_clave and primera.definicion_contextual:
            # Solo exigimos el comportamiento de cache si de verdad hubo
            # llamada real a OpenAI que cachear (con clave y sentido resuelto).
            if primera.desde_cache:
                fallos.append("la 1a consulta (cache recien creada) ya vino de cache: la prueba no es valida")
            if not segunda.desde_cache:
                fallos.append("la segunda consulta identica NO vino de cache (desde_cache=False)")
            if t_segunda >= t_primera:
                fallos.append(
                    f"la segunda consulta ({t_segunda:.3f}s) no fue mas rapida que la primera ({t_primera:.3f}s)")
            if not primera.desde_cache and segunda.desde_cache and t_segunda < t_primera:
                print(f"OK: cache confirmada. {t_primera:.3f}s -> {t_segunda:.3f}s "
                      f"({t_primera / max(t_segunda, 1e-6):.1f}x mas rapido).\n")
        else:
            print("AVISO: sin OPENAI_API_KEY (o sin sentido resuelto) no hubo llamada real "
                  "que cachear; la prueba de velocidad de cache no aplica en este entorno.\n")
    finally:
        consultor_demo.cerrar()
        ruta_cache_demo.unlink(missing_ok=True)

    # --- 5) Degradacion sin API key (simulada) ------------------------
    print("=== 5) Degradacion elegante simulada (sin OPENAI_API_KEY) ===")
    consultor_sin_clave = lexicon.ConsultorLexico()
    consultor_sin_clave._sin_clave = True  # fuerza la rama "sin credencial"
    try:
        r_deg = consultor_sin_clave.consultar(
            "brook", "A small brook ran behind the old cottage.", nivel=1.0)
        mostrar(r_deg)
        if r_deg.definicion_contextual is not None:
            fallos.append("degradacion: definicion_contextual deberia ser None sin clave")
        if not any("OPENAI_API_KEY" in a for a in r_deg.avisos):
            fallos.append("degradacion: no se aviso claramente de la falta de OPENAI_API_KEY")
        if r_deg.sentido is None:
            fallos.append("degradacion: se perdio el diccionario tambien (deberia seguir funcionando)")
        print("OK: no hubo excepcion; se devolvio diccionario + IPA y avisos claros.\n")
    except Exception as e:
        fallos.append(f"degradacion: lanzo excepcion en vez de degradar ({type(e).__name__}: {e})")
    finally:
        consultor_sin_clave.cerrar()

    consultor.cerrar()

    linea()
    if fallos:
        print(f"RESULTADO: {len(fallos)} fallo(s):")
        for f in fallos:
            print(f"  - {f}")
        return 1

    print("RESULTADO: TODO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
