"""Mide el arranque en frio del Space, que hasta hoy era una estimacion.

La limitacion 12 del documento decia "decenas de segundos" sin haberlo medido.
Esto lo mide de verdad: reinicia el Space y cronometra dos cosas distintas,
que no son la misma y conviene separarlas.

  1. Hasta que el runtime dice RUNNING. Es lo que tarda el contenedor en
     levantarse y en ejecutar `app.py` hasta que Gradio escucha. Aqui es donde
     se cargan torch, los 328 MB del modelo y el diccionario.
  2. Hasta que la pagina responde 200 a una peticion de verdad. Siempre es un
     poco mas: el proxy tarda en enterarse.

NO mide la suspension por inactividad. Un Space gratuito se duerme tras 48 h
sin visitas (gcTimeout = 172800 s segun la API) y despertar de ahi incluye
ademas volver a traer la imagen. Lo que se mide aqui es la cota inferior: el
arranque de un contenedor que ya tiene todo en su sitio.

Uso:  python -X utf8 medir_arranque.py
El token de escritura sale de HF_TOKEN o de C:/Users/laura/.hf_token.
"""
import json
import os
import time
import urllib.error
import urllib.request

ESPACIO = "MikeMaki1763/literalevel"
API = "https://huggingface.co/api/spaces/" + ESPACIO
PAGINA = "https://" + ESPACIO.replace("/", "-").lower() + ".hf.space/"


def token():
    t = os.environ.get("HF_TOKEN")
    if t:
        return t.strip()
    ruta = os.path.join(os.path.expanduser("~"), ".hf_token")
    if os.path.exists(ruta):
        return open(ruta, encoding="utf-8").read().strip()
    raise SystemExit("No hay token: ponlo en HF_TOKEN o en ~/.hf_token")


def estado():
    with urllib.request.urlopen(API, timeout=30) as r:
        d = json.load(r)
    return (d.get("runtime") or {}).get("stage")


def reiniciar(tk):
    pet = urllib.request.Request(API + "/restart", method="POST",
                                 headers={"Authorization": "Bearer " + tk})
    with urllib.request.urlopen(pet, timeout=60) as r:
        return r.status


def responde():
    """True en cuanto la pagina devuelve algo, sea 200 o un error del propio
    Gradio. Lo que se cronometra es que haya alguien al otro lado."""
    try:
        pet = urllib.request.Request(PAGINA, headers={"User-Agent": "literalevel/1.0"})
        with urllib.request.urlopen(pet, timeout=20) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return False
    except Exception:
        return False


def main():
    tk = token()
    print("estado antes del reinicio:", estado())
    print("reiniciando", ESPACIO, "...")
    reiniciar(tk)
    t0 = time.time()

    visto_construyendo = False
    t_running = None
    while time.time() - t0 < 900:
        s = estado()
        if s in ("BUILDING", "RUNNING_BUILDING", "STARTING", "APP_STARTING"):
            visto_construyendo = True
        if s == "RUNNING" and visto_construyendo:
            t_running = time.time() - t0
            print("  RUNNING a los %.0f s" % t_running)
            break
        print("  %5.0f s  %s" % (time.time() - t0, s))
        time.sleep(5)

    if t_running is None:
        print("no llego a RUNNING en 15 min; se para aqui")
        return

    while time.time() - t0 < 900:
        if responde():
            t_pagina = time.time() - t0
            print("  la pagina responde 200 a los %.0f s" % t_pagina)
            print()
            print("ARRANQUE EN FRIO MEDIDO")
            print("  contenedor hasta RUNNING : %.0f s" % t_running)
            print("  hasta que responde 200   : %.0f s" % t_pagina)
            return
        time.sleep(5)
    print("RUNNING a los %.0f s, pero la pagina no respondio en 15 min" % t_running)


if __name__ == "__main__":
    main()
