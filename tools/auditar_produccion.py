"""Pruebas sintéticas autorizadas; nunca imprime contraseñas ni tokens.

preparar agrega un secreto independiente, sin leer las claves de usuarios reales.
retirar restaura los roles originales y elimina el secreto de pruebas.
No llama a proveedores de audio ni descarga datos de usuarios reales.
"""
import argparse
import json
import secrets
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))
import desplegar_app as despliegue

ESTADO = RAIZ / "tmp" / "seguridad-cuentas-temporales.json"
RESULTADO = RAIZ / "auditoria" / "seguridad_produccion_2026-10-01.json"
BASE = despliegue.URL
REGISTRO = []


def comprobar(nombre, condicion):
    REGISTRO.append({"prueba": nombre, "correcto": bool(condicion)})
    print(("OK " if condicion else "FALLA ") + nombre, flush=True)
    if not condicion:
        raise RuntimeError("Verificación fallida: " + nombre)


def guardar_resultados():
    RESULTADO.write_text(json.dumps({"momento_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pruebas": REGISTRO}, ensure_ascii=False, indent=2), encoding="utf-8")


def peticion(metodo, ruta, token=None, **kw):
    cab = {"X-Lector": "auditoria-produccion-" + "7" * 24}
    if token: cab["Authorization"] = "Bearer " + token
    cab.update(kw.pop("headers", {}))
    return requests.request(metodo, BASE + ruta, headers=cab, timeout=90, **kw)


def login(nombre, clave):
    r = peticion("POST", "/api/entrar", json={"usuario": nombre, "clave": clave})
    comprobar("inicio de sesión sintético", r.status_code == 200 and r.json().get("expira_en") == 28800)
    return r.json()["token"]


def preparar():
    from huggingface_hub import HfApi
    if ESTADO.exists(): raise RuntimeError("Ya existe una preparación; no duplicar.")
    api = HfApi(token=despliegue.token())
    variables = api.get_space_variables(despliegue.REPO)
    admins = variables.get("LITERALEVEL_ADMIN_USUARIOS")
    estado = {"admin_previo": admins.value if admins else None,
        "a": "audit" + secrets.token_hex(5), "b": "audit" + secrets.token_hex(5),
        "clave": secrets.token_urlsafe(24)}
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps(estado), encoding="utf-8")
    api.add_space_secret(despliegue.REPO, "LITERALEVEL_CUENTAS_AUDITORIA",
        ",".join(f"{estado[n]}:{estado['clave']}:40" for n in ("a", "b")))
    api.add_space_variable(despliegue.REPO, "LITERALEVEL_ADMIN_USUARIOS",
        ",".join(filter(None, (estado["admin_previo"], estado["a"]))))
    # Valores públicos: límites efectivos, no alertas del proveedor.
    api.add_space_variable(despliegue.REPO, "LITERALEVEL_PRESUPUESTO_DIA_CENTAVOS", "500")
    api.add_space_variable(despliegue.REPO, "LITERALEVEL_PRESUPUESTO_TOTAL_CENTAVOS", "2000")
    print("Cuentas temporales preparadas; contraseñas originales no consultadas.")


def probar():
    e = json.loads(ESTADO.read_text(encoding="utf-8"))
    salud = peticion("GET", "/api/salud")
    comprobar("API publicada con protección", salud.status_code == 200 and salud.json().get("api") == "0.3.0-seguridad")
    for ruta in ("/config", "/gradio_api/info", "/docs", "/openapi.json"):
        comprobar("Gradio y esquema público cerrados " + ruta, peticion("GET", ruta).status_code == 404)
    comprobar("CORS origen ajeno rechazado", peticion("GET", "/api/salud", headers={"Origin": "https://ajeno.example"}).status_code == 403)
    opciones = peticion("OPTIONS", "/api/entrar", headers={"Origin": "https://pleyade-app.vercel.app", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,x-lector"})
    comprobar("CORS del front permite autenticación", opciones.status_code in (200, 204)
        and "authorization" in opciones.headers.get("access-control-allow-headers", "").lower()
        and opciones.headers.get("access-control-allow-origin") == "https://pleyade-app.vercel.app")
    comprobar("X-Lector no autentica", peticion("GET", "/api/entrada").json().get("dentro") is False)
    comprobar("token manipulado rechazado", peticion("GET", "/api/perfil", token="x" * 43).status_code == 401)
    a, b = login(e["a"], e["clave"]), login(e["b"], e["clave"])
    comprobar("cuota finita", peticion("GET", "/api/entrada", a).json().get("restantes") == 40)
    comprobar("rol de administrador separado", peticion("GET", "/api/entrada", a).json().get("admin") is True and peticion("GET", "/api/entrada", b).json().get("admin") is False)
    r = peticion("POST", "/api/perfil/cuestionario", a, json={"nombre": "Prueba sintética de seguridad", "respuestas": {"fragmento_medio": 1.2}})
    comprobar("perfil propio guardado", r.status_code == 200)
    comprobar("perfiles entre cuentas separados", peticion("GET", "/api/perfil", b).json().get("perfil") is None)
    comprobar("cambiar X-Lector no cambia la cuenta", peticion("GET", "/api/perfil", a, headers={"X-Lector": "otra-identidad-" + "3" * 24}).json().get("perfil", {}).get("nombre") == "Prueba sintética de seguridad")
    subir = peticion("POST", "/api/libros", a, files={"archivo": ("auditoria.txt", b"A private synthetic story. The cat sat under the tree. " * 10, "text/plain")})
    comprobar("subida de archivo sintético", subir.status_code == 200)
    ident = subir.json()["id"]
    e["libro"] = ident
    comprobar("otro usuario no abre el archivo", peticion("GET", "/api/libros/" + ident, b).status_code == 404)
    comprobar("visitante no abre el archivo", peticion("GET", "/api/libros/" + ident).status_code == 404)
    for ruta in ("/api/gpt-live/sesion", "/api/lectura/vivo"):
        comprobar("audio en vivo cerrado " + ruta, peticion("POST", ruta, a, json={"sdp": "prueba"}).status_code == 503)
    comprobar("sinopsis directa sin cuenta bloqueada", peticion("POST", "/api/libros/SWV369/sinopsis").status_code == 403)
    # La solicitud deliberadamente no tiene perfil; jamás llega a TTS.
    comprobar("audiolibro directo sin cuenta bloqueado", peticion("POST", "/api/libros/SWV369/capitulos/0/escuchar", json={"fragmento": 0}).status_code in (403, 422))
    comprobar("trabajador Eos privado", peticion("GET", "/api/eos/cola").status_code == 403)
    comprobar("no administrador no emite recuperación", peticion("POST", "/api/admin/recuperacion", b, json={"usuario": e["a"], "actual": e["clave"]}).status_code == 403)
    comprobar("administrador debe reautenticarse", peticion("POST", "/api/admin/recuperacion", a, json={"usuario": e["b"], "actual": "incorrecta"}).status_code == 401)
    def emitir():
        r = peticion("POST", "/api/admin/recuperacion", a, json={"usuario": e["b"], "actual": e["clave"]})
        comprobar("recuperación emitida solo por administrador", r.status_code == 200 and r.json().get("expira_en") == 900)
        return r.json()["codigo"]
    codigo1, codigo2 = emitir(), emitir()
    nueva_b = secrets.token_urlsafe(24)
    comprobar("reemisión revoca recuperación anterior", peticion("POST", "/api/recuperar", json={"codigo": codigo1, "nueva": nueva_b}).status_code == 401)
    comprobar("recuperación de contraseña", peticion("POST", "/api/recuperar", json={"codigo": codigo2, "nueva": nueva_b}).status_code == 200)
    comprobar("código de recuperación de un solo uso", peticion("POST", "/api/recuperar", json={"codigo": codigo2, "nueva": nueva_b}).status_code == 401)
    comprobar("recuperación revoca sesión previa", peticion("GET", "/api/perfil", b).status_code == 401)
    b = login(e["b"], nueva_b)
    nueva_a = secrets.token_urlsafe(24)
    comprobar("cambio de contraseña", peticion("POST", "/api/cuenta/clave", a, json={"actual": e["clave"], "nueva": nueva_a}).status_code == 200)
    comprobar("cambio revoca sesión previa", peticion("GET", "/api/perfil", a).status_code == 401)
    comprobar("contraseña anterior inválida", peticion("POST", "/api/entrar", json={"usuario": e["a"], "clave": e["clave"]}).status_code == 401)
    a = login(e["a"], nueva_a)
    comprobar("borrado del archivo sintético", peticion("DELETE", "/api/libros/" + ident, a).status_code == 200)
    # Dejar una sesión para verificar persistencia tras el reinicio de retirada.
    e.update({"token_b": b, "token_a": a, "nueva_a": nueva_a})
    ESTADO.write_text(json.dumps(e), encoding="utf-8")
    comprobar("cierre de sesión", peticion("POST", "/api/salir", a).status_code == 200)
    comprobar("reutilizar sesión cerrada falla", peticion("GET", "/api/perfil", a).status_code == 401)
    guardar_resultados()


def retirar():
    from huggingface_hub import HfApi
    e = json.loads(ESTADO.read_text(encoding="utf-8"))
    api = HfApi(token=despliegue.token())
    api.delete_space_secret(despliegue.REPO, "LITERALEVEL_CUENTAS_AUDITORIA")
    if e["admin_previo"] is None: api.delete_space_variable(despliegue.REPO, "LITERALEVEL_ADMIN_USUARIOS")
    else: api.add_space_variable(despliegue.REPO, "LITERALEVEL_ADMIN_USUARIOS", e["admin_previo"])
    print("Secreto de cuentas temporales retirado y roles originales restaurados.")


def retirada():
    e = json.loads(ESTADO.read_text(encoding="utf-8"))
    if "token_b" in e:
        comprobar("sesión de cuenta retirada ya no válida", peticion("GET", "/api/perfil", e["token_b"]).status_code == 401)
    ESTADO.unlink()
    if RESULTADO.exists():
        previo = json.loads(RESULTADO.read_text(encoding="utf-8"))["pruebas"]
        REGISTRO[:0] = previo
    guardar_resultados()


def reiniciar():
    from huggingface_hub import HfApi
    HfApi(token=despliegue.token()).restart_space(despliegue.REPO)
    print("Reinicio solicitado para verificar persistencia, sin reconstruir la imagen.")


def persistencia():
    e = json.loads(ESTADO.read_text(encoding="utf-8"))
    if RESULTADO.exists(): REGISTRO.extend(json.loads(RESULTADO.read_text(encoding="utf-8"))["pruebas"])
    r = peticion("GET", "/api/entrada", e["token_b"])
    comprobar("sesión y cuota conservadas tras reinicio", r.status_code == 200 and r.json().get("dentro") is True and r.json().get("restantes") == 40)
    a = login(e["a"], e["nueva_a"])
    comprobar("contraseña cambiada y perfil conservados tras reinicio", peticion("GET", "/api/perfil", a).json().get("perfil", {}).get("nombre") == "Prueba sintética de seguridad")
    peticion("POST", "/api/salir", a)
    guardar_resultados()


def smoke():
    if RESULTADO.exists(): REGISTRO.extend(json.loads(RESULTADO.read_text(encoding="utf-8"))["pruebas"])
    r = peticion("GET", "/api/salud")
    comprobar("salud del despliegue final", r.status_code == 200 and r.json().get("estado") == "ok" and r.json().get("api") == "0.3.0-seguridad")
    comprobar("cabeceras de seguridad API", r.headers.get("x-content-type-options") == "nosniff" and r.headers.get("x-frame-options") == "DENY" and "default-src 'none'" in r.headers.get("content-security-policy", ""))
    comprobar("cuentas gratuitas no dan barra libre", peticion("GET", "/api/entrada").json().get("dentro") is False)
    for ruta in ("/config", "/gradio_api/info", "/gradio_api/queue/join"):
        comprobar("cierre Gradio del despliegue final " + ruta, peticion("GET", ruta).status_code == 404)
    for ruta in ("/api/gpt-live/sesion", "/api/lectura/vivo"):
        comprobar("cierre audio vivo del despliegue final " + ruta, peticion("POST", ruta, json={}).status_code == 503)
    comprobar("generación de audiolibro final sin cuenta rechazada", peticion("POST", "/api/libros/SWV369/capitulos/0/escuchar").status_code == 403)
    guardar_resultados()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("accion", choices=("preparar", "probar", "reiniciar", "persistencia", "retirar", "retirada", "smoke"))
    args = p.parse_args()
    try:
        {"preparar": preparar, "probar": probar, "reiniciar": reiniciar,
         "persistencia": persistencia, "retirar": retirar, "retirada": retirada, "smoke": smoke}[args.accion]()
    except Exception as error:
        # No imprimir respuestas ni datos de peticiones que contienen credenciales.
        guardar_resultados()
        print("La comprobación necesita revisión: " + type(error).__name__)
        raise SystemExit(1)
