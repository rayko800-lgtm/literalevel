#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
uso.py - Lector local de consumo de Claude Code (Anthropic) y Codex (OpenAI).

Lee las credenciales que YA tienes en disco (no pide nada, no las imprime nunca):
  - Claude Code : %USERPROFILE%\\.claude\\.credentials.json   -> claudeAiOauth.accessToken
  - Codex CLI   : %USERPROFILE%\\.codex\\auth.json             -> tokens.access_token

Consulta dos endpoints no documentados pero reales (los usan los propios CLI):
  - GET https://api.anthropic.com/api/oauth/usage
  - GET https://chatgpt.com/backend-api/codex/usage

Y escribe, junto a este script:
  - estado.json : datos normalizados (planos y anidados) para widgets
  - index.html  : pagina autocontenida con barras, para el movil o pantalla de inicio

MODOS
  python uso.py                 una lectura, escribe estado.json + index.html
  python uso.py --texto         ademas imprime las barras en la terminal
  python uso.py --loop 5        refresca cada 5 minutos (Ctrl+C para salir)
  python uso.py --serve 8787    sirve la carpeta en http://<ip-del-pc>:8787/ (LAN)
  python uso.py --loop 5 --serve 8787    lo habitual: refresca y sirve a la vez
  python uso.py --gist          publica estado.json + index.html en un Gist secreto
                                (requiere la variable de entorno GITHUB_TOKEN con
                                 permiso 'gist'; el token no se escribe en disco)

NUNCA imprime ni guarda tokens. Si un token esta caducado lo dice y te pide que
abras el CLI correspondiente una vez (Claude Code y Codex renuevan solos su token
al usarse, y este script vuelve a leer el fichero actualizado).
"""

import argparse
import json
import os
import secrets
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
HOME = Path(os.path.expanduser("~"))
CRED_CLAUDE = HOME / ".claude" / ".credentials.json"
CRED_CODEX = HOME / ".codex" / "auth.json"

URL_CLAUDE = "https://api.anthropic.com/api/oauth/usage"
URL_CODEX = "https://chatgpt.com/backend-api/codex/usage"

TIMEOUT = 20


# ---------------------------------------------------------------- utilidades

def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _iso_local(dt):
    return dt.astimezone().isoformat(timespec="seconds")


def _desde_epoch(seg):
    if not seg:
        return None, None, None
    dt = datetime.fromtimestamp(int(seg), tz=timezone.utc).astimezone()
    faltan = max(0, int((dt - datetime.now().astimezone()).total_seconds() // 60))
    return dt.isoformat(timespec="seconds"), dt.strftime("%a %H:%M"), faltan


def _desde_iso(txt):
    if not txt:
        return None, None, None
    t = txt.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(t).astimezone()
    except ValueError:
        return None, None, None
    faltan = max(0, int((dt - datetime.now().astimezone()).total_seconds() // 60))
    return dt.isoformat(timespec="seconds"), dt.strftime("%a %H:%M"), faltan


def _ventana(pct, iso_o_epoch, es_epoch=False):
    if pct is None:
        return None
    iso, corto, faltan = (_desde_epoch(iso_o_epoch) if es_epoch else _desde_iso(iso_o_epoch))
    return {
        "pct": round(float(pct)),
        "resetea_iso": iso,
        "resetea": corto,
        "faltan_min": faltan,
    }


# ---------------------------------------------------------------- proveedores

def leer_claude():
    """Devuelve dict normalizado. Nunca incluye el token."""
    out = {"ok": False, "error": None, "plan": None, "ventana_5h": None,
           "semana": None, "semana_opus": None, "extra_pct": None}
    try:
        cred = json.loads(CRED_CLAUDE.read_text(encoding="utf-8"))["claudeAiOauth"]
    except Exception as e:
        out["error"] = "no pude leer %s (%s)" % (CRED_CLAUDE, type(e).__name__)
        return out

    out["plan"] = cred.get("subscriptionType")
    caduca = cred.get("expiresAt")
    if caduca and caduca / 1000 < time.time():
        out["error"] = "token de Claude caducado; abre Claude Code una vez para renovarlo"
        return out

    try:
        d = _get(URL_CLAUDE, {
            "Authorization": "Bearer " + cred["accessToken"],
            "Content-Type": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
            "User-Agent": "uso.py/1.0 (local)",
        })
    except urllib.error.HTTPError as e:
        out["error"] = "HTTP %s del endpoint de uso de Anthropic" % e.code
        return out
    except Exception as e:
        out["error"] = "%s al consultar Anthropic" % type(e).__name__
        return out

    fh = d.get("five_hour") or {}
    sd = d.get("seven_day") or {}
    op = d.get("seven_day_opus") or {}
    xu = d.get("extra_usage") or {}

    out["ok"] = True
    out["ventana_5h"] = _ventana(fh.get("utilization"), fh.get("resets_at"))
    out["semana"] = _ventana(sd.get("utilization"), sd.get("resets_at"))
    out["semana_opus"] = _ventana(op.get("utilization"), op.get("resets_at"))
    if xu.get("is_enabled"):
        out["extra_pct"] = round(float(xu.get("utilization") or 0))
    return out


def leer_codex():
    out = {"ok": False, "error": None, "plan": None, "ventana_5h": None,
           "semana": None, "creditos": None, "modelos": {}}
    try:
        auth = json.loads(CRED_CODEX.read_text(encoding="utf-8"))
        tokens = auth["tokens"]
    except Exception as e:
        out["error"] = "no pude leer %s (%s)" % (CRED_CODEX, type(e).__name__)
        return out

    try:
        d = _get(URL_CODEX, {
            "Authorization": "Bearer " + tokens["access_token"],
            "chatgpt-account-id": tokens.get("account_id", ""),
            "Content-Type": "application/json",
            "originator": "codex_cli_rs",
            "User-Agent": "uso.py/1.0 (local)",
        })
    except urllib.error.HTTPError as e:
        extra = "; abre Codex una vez para renovar el token" if e.code in (401, 403) else ""
        out["error"] = "HTTP %s del endpoint de uso de Codex%s" % (e.code, extra)
        return out
    except Exception as e:
        out["error"] = "%s al consultar Codex" % type(e).__name__
        return out

    rl = d.get("rate_limit") or {}
    pw = rl.get("primary_window") or {}
    sw = rl.get("secondary_window") or {}
    cr = d.get("credits") or {}

    out["ok"] = True
    out["plan"] = d.get("plan_type")
    out["ventana_5h"] = _ventana(pw.get("used_percent"), pw.get("reset_at"), es_epoch=True)
    out["semana"] = _ventana(sw.get("used_percent"), sw.get("reset_at"), es_epoch=True)
    out["creditos"] = cr.get("balance")
    for nombre, info in (d.get("model_usage") or {}).items():
        out["modelos"][nombre] = bool((info or {}).get("available"))
    return out


# ---------------------------------------------------------------- salida

def _pct(bloque):
    return bloque["pct"] if bloque else None


def construir(cl, cx):
    ahora = datetime.now().astimezone()
    e = {
        "actualizado_iso": _iso_local(ahora),
        "actualizado": ahora.strftime("%d/%m %H:%M"),
        "epoch": int(ahora.timestamp()),
        # --- claves planas, para widgets que solo saben leer un campo ---
        "cc_5h_pct": _pct(cl["ventana_5h"]),
        "cc_7d_pct": _pct(cl["semana"]),
        "cc_5h_reset": (cl["ventana_5h"] or {}).get("resetea"),
        "cc_7d_reset": (cl["semana"] or {}).get("resetea"),
        "cx_5h_pct": _pct(cx["ventana_5h"]),
        "cx_7d_pct": _pct(cx["semana"]),
        "cx_5h_reset": (cx["ventana_5h"] or {}).get("resetea"),
        "cx_7d_reset": (cx["semana"] or {}).get("resetea"),
        # --- una linea que cabe en un widget de texto ---
        "resumen": "",
        # --- detalle ---
        "claude": cl,
        "codex": cx,
    }
    def trozo(nombre, d):
        if not d["ok"]:
            return "%s: --" % nombre
        a = _pct(d["ventana_5h"])
        b = _pct(d["semana"])
        return "%s 5h %s%% / sem %s%%" % (nombre, "?" if a is None else a, "?" if b is None else b)
    e["resumen"] = "%s | %s" % (trozo("Claude", cl), trozo("Codex", cx))
    return e


def barras_texto(e):
    def linea(etiqueta, pct, reset):
        if pct is None:
            return "  %-16s  sin dato" % etiqueta
        llenos = int(round(pct / 5.0))
        barra = "#" * llenos + "." * (20 - llenos)
        return "  %-16s [%s] %3d%%  reset %s" % (etiqueta, barra, pct, reset or "-")
    out = ["", "  Consumo  -  %s" % e["actualizado"], ""]
    out.append("  CLAUDE CODE (%s)" % (e["claude"].get("plan") or "?"))
    if e["claude"]["ok"]:
        out.append(linea("ventana 5h", e["cc_5h_pct"], e["cc_5h_reset"]))
        out.append(linea("semana", e["cc_7d_pct"], e["cc_7d_reset"]))
        if e["claude"]["semana_opus"]:
            out.append(linea("semana Opus", e["claude"]["semana_opus"]["pct"],
                             e["claude"]["semana_opus"]["resetea"]))
    else:
        out.append("    " + str(e["claude"]["error"]))
    out.append("")
    out.append("  CODEX (%s)" % (e["codex"].get("plan") or "?"))
    if e["codex"]["ok"]:
        out.append(linea("ventana 5h", e["cx_5h_pct"], e["cx_5h_reset"]))
        out.append(linea("semana", e["cx_7d_pct"], e["cx_7d_reset"]))
        libres = [m for m, ok in e["codex"]["modelos"].items() if ok]
        if libres:
            out.append("    modelos disponibles: %s" % ", ".join(sorted(libres)))
    else:
        out.append("    " + str(e["codex"]["error"]))
    out.append("")
    return "\n".join(out)


PLANTILLA = """<!doctype html>
<html lang="es"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0e1015">
<title>Uso IA</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>%F0%9F%93%8A</text></svg>">
<style>
*{box-sizing:border-box}
body{margin:0;background:#0e1015;color:#e8eaf0;
 font:16px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 padding:18px 16px 28px;-webkit-text-size-adjust:100%}
h1{font-size:13px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
 color:#7a8194;margin:0 0 14px}
.tarjeta{background:#171a22;border:1px solid #242833;border-radius:14px;
 padding:14px 15px 16px;margin:0 0 12px}
.cab{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:12px}
.nom{font-size:17px;font-weight:650}
.plan{font-size:12px;color:#7a8194}
.fila{margin:11px 0 0}
.et{display:flex;justify-content:space-between;font-size:13px;color:#9aa1b4;margin-bottom:5px}
.et b{color:#e8eaf0;font-weight:650;font-variant-numeric:tabular-nums}
.pista{height:9px;border-radius:99px;background:#262a36;overflow:hidden}
.rel{height:100%;border-radius:99px;transition:width .3s}
.v{background:#3fb950}.a{background:#d29922}.r{background:#f85149}
.pie{margin-top:14px;font-size:12px;color:#5d6475;text-align:center}
.err{color:#f85149;font-size:13px}
</style></head><body>
<h1>Consumo de modelos</h1>
__TARJETAS__
<div class="pie">Actualizado __CUANDO__ &middot; se refresca solo cada 2 min</div>
<script>setTimeout(function(){location.reload()},120000);</script>
</body></html>
"""


def _barra_html(etiqueta, pct, reset):
    if pct is None:
        return '<div class="fila"><div class="et"><span>%s</span><b>--</b></div>' \
               '<div class="pista"></div></div>' % etiqueta
    clase = "v" if pct < 60 else ("a" if pct < 85 else "r")
    sufijo = (" &middot; reset %s" % reset) if reset else ""
    return ('<div class="fila"><div class="et"><span>%s%s</span><b>%d%%</b></div>'
            '<div class="pista"><div class="rel %s" style="width:%d%%"></div></div></div>'
            % (etiqueta, sufijo, pct, clase, min(100, pct)))


def _tarjeta(nombre, d, p5, p7, r5, r7):
    if not d["ok"]:
        cuerpo = '<div class="err">%s</div>' % (d["error"] or "sin datos")
    else:
        cuerpo = _barra_html("Ventana de 5 h", p5, r5) + _barra_html("Semana", p7, r7)
        extra = d.get("semana_opus")
        if extra:
            cuerpo += _barra_html("Semana Opus", extra["pct"], extra["resetea"])
    return ('<div class="tarjeta"><div class="cab"><span class="nom">%s</span>'
            '<span class="plan">%s</span></div>%s</div>'
            % (nombre, d.get("plan") or "", cuerpo))


def construir_html(e):
    t = _tarjeta("Claude Code", e["claude"], e["cc_5h_pct"], e["cc_7d_pct"],
                 e["cc_5h_reset"], e["cc_7d_reset"])
    t += _tarjeta("Codex", e["codex"], e["cx_5h_pct"], e["cx_7d_pct"],
                  e["cx_5h_reset"], e["cx_7d_reset"])
    return PLANTILLA.replace("__TARJETAS__", t).replace("__CUANDO__", e["actualizado"])


def escribir(e):
    (AQUI / "estado.json").write_text(
        json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    (AQUI / "index.html").write_text(construir_html(e), encoding="utf-8")


# ---------------------------------------------------------------- gist

def publicar_gist(e):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("  [gist] falta la variable de entorno GITHUB_TOKEN (permiso 'gist'); no publico")
        return
    gid_f = AQUI / ".gist_id"
    ficheros = {
        "estado.json": {"content": json.dumps(e, ensure_ascii=False, indent=1)},
        "index.html": {"content": construir_html(e)},
    }
    cab = {"Authorization": "Bearer " + token,
           "Accept": "application/vnd.github+json",
           "User-Agent": "uso.py"}
    try:
        if gid_f.exists():
            gid = gid_f.read_text(encoding="utf-8").strip()
            req = urllib.request.Request(
                "https://api.github.com/gists/" + gid, method="PATCH",
                data=json.dumps({"files": ficheros}).encode(), headers=cab)
        else:
            req = urllib.request.Request(
                "https://api.github.com/gists", method="POST",
                data=json.dumps({"public": False, "description": "uso de modelos IA",
                                 "files": ficheros}).encode(), headers=cab)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read().decode())
        gid_f.write_text(d["id"], encoding="utf-8")
        crudo = d["files"]["estado.json"]["raw_url"].rsplit("/raw/", 1)[0] + "/raw/estado.json"
        print("  [gist] JSON para el widget: " + crudo)
    except urllib.error.HTTPError as ex:
        print("  [gist] HTTP %s al publicar" % ex.code)
    except Exception as ex:
        print("  [gist] %s al publicar" % type(ex).__name__)


# ---------------------------------------------------------------- servidor

def arrancar_servidor(puerto):
    import http.server
    import threading

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(AQUI), **k)

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("0.0.0.0", puerto), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "TU-IP"
    print("  servidor en  http://%s:%d/           (pagina)" % (ip, puerto))
    print("               http://%s:%d/estado.json (JSON para el widget)" % (ip, puerto))
    return srv


# ------------------------------------------------------- tunel publico

def arrancar_tunel(puerto):
    """Expone la pagina en una URL HTTPS publica, para verla fuera de casa.

    Usa el tunel de Gradio, que ya esta instalado para LiteraLevel y **no
    pide ninguna cuenta ni token**. Es el camino corto cuando no hay un
    GITHUB_TOKEN a mano para el Gist: se levanta y en diez segundos hay un
    enlace que abre desde cualquier red.

    Lo que se publica son solo porcentajes y horas de reinicio. Las
    credenciales no salen de este equipo: se usan aqui para consultar y ya.
    Aun asi, el enlace es publico para quien lo tenga; no lo repartas.
    """
    try:
        from gradio_client import client  # noqa: F401
    except Exception:
        pass
    try:
        from gradio import networking
    except Exception as e:
        print(f"  [tunel] gradio no esta disponible ({type(e).__name__}); "
              f"usa --serve y la IP local, o --gist")
        return None
    # La firma de setup_tunnel ha cambiado entre versiones de Gradio: hoy pide
    # cinco argumentos y antes tres. Se prueban de mas a menos en vez de fijar
    # una version, que es lo que romperia en la proxima actualizacion.
    ficha = secrets.token_urlsafe(32)
    url = None
    for args in (("127.0.0.1", puerto, ficha, None, None),
                 ("127.0.0.1", puerto, ficha, None),
                 ("127.0.0.1", puerto, ficha)):
        try:
            url = networking.setup_tunnel(*args)
            break
        except TypeError:
            continue
        except Exception as e:
            print(f"  [tunel] no se pudo abrir ({type(e).__name__}: {e})")
            return None
    if not url:
        print("  [tunel] la version de gradio no encaja con ninguna firma conocida")
        return None
    print(f"  ENLACE PUBLICO   {url}/")
    print(f"  JSON del widget  {url}/estado.json")
    print("  (dura mientras este proceso siga vivo)")
    return url


# ---------------------------------------------------------------- main

def una_vez(args):
    e = construir(leer_claude(), leer_codex())
    escribir(e)
    if args.gist:
        publicar_gist(e)
    if args.texto or args.loop:
        print(barras_texto(e))
    else:
        print("  " + e["resumen"])
        print("  escrito: %s" % (AQUI / "estado.json"))
    return e


def main():
    p = argparse.ArgumentParser(description="Consumo de Claude Code y Codex")
    p.add_argument("--texto", action="store_true", help="imprime barras en la terminal")
    p.add_argument("--loop", type=float, metavar="MIN", help="refresca cada MIN minutos")
    p.add_argument("--serve", type=int, metavar="PUERTO", help="sirve la carpeta por HTTP")
    p.add_argument("--gist", action="store_true", help="publica en un Gist secreto")
    p.add_argument("--publico", action="store_true",
                   help="ademas de servir, abre un tunel HTTPS publico (sin cuentas)")
    args = p.parse_args()

    if args.publico and not args.serve:
        args.serve = 8787          # --publico implica servir
    if args.serve:
        arrancar_servidor(args.serve)
        if args.publico:
            arrancar_tunel(args.serve)

    una_vez(args)

    if args.loop:
        try:
            while True:
                time.sleep(max(30.0, args.loop * 60))
                una_vez(args)
        except KeyboardInterrupt:
            print("\n  fin")
    elif args.serve:
        print("  Ctrl+C para parar")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\n  fin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
