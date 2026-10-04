"""Calibra la lengua de Eos contra la geometría de la boca, en el visor aislado (puerto 8790).

Para cada sonido canónico (poses.ejemplo.json de boca3d → canales, como lengua.py) pone la pose en
el visor (window.__lab, 4 oct 2026), mide los vértices de la lengua en mm respecto al padre de
Tongue1 (x lateral, y arriba, z adelante; cabeza quieta) frente al techo de la boca que el propio
visor mide (paladar, encía, incisivos), y guarda un corte sagital (corte_<etiqueta>_<sonido>.png).

    python -X utf8 tools/eos_pronunciar/calibrar_lengua.py --etiqueta v4            # las constantes del visor
    python -X utf8 tools/eos_pronunciar/calibrar_lengua.py --etiqueta prueba --K h1=-0.4,alv4=-0.8 --sonidos i,l,t

Qué mirar: «pala»/«cima» es dónde toca o se acerca la lengua (alveolares: pala en z 7-10 mm,
y 18-22, tocando el alvéolo; k g ŋ: cima en z −20 tocando el velo; i j u: cima a 1-2 mm del
paladar; θ ð: asoma 3 mm por delante de los incisivos de abajo); «sobre_techo» tiene que ser 0 o
casi (el visor permite 1 mm de contacto).
"""
import argparse
import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

AQUI = Path.cwd() / "lengua_calibracion"
AQUI.mkdir(exist_ok=True)
URL = "http://127.0.0.1:8790/index.html?grabar=clips/ga_006c&camara=0,-0.035,0.62"
POSES = Path("C:/Users/laura/literalevel/front/src/app/compartido/boca3d/poses.ejemplo.json")
MAND = 0.75   # K.mand del laboratorio: jawOpen = mandibula * 0.75


def canales(pose):
    punta = pose.get('punta', 'reposo')
    return {'altura': pose['cuerpo'][0], 'adelante': pose['cuerpo'][1],
            'velo': 1.0 if pose.get('dorso_velo') else 0.0, 'alto': float(pose.get('dorso_alto', 0.0)),
            'raiz': float(pose.get('raiz', 0.0)),
            'alveolar': 1.0 if punta == 'alveolar' else (0.6 if punta == 'dental' else 0.0),
            'interdental': 1.0 if punta == 'interdental' else (0.4 if punta == 'dental' else 0.0),
            'postalveolar': 1.0 if punta == 'postalveolar' else 0.0,
            'retrofleja': 1.0 if punta == 'retrofleja' else 0.0}


def techo():
    """Perfil del techo (z → y, mm): lo da el visor en la primera medida (window.__lab.techoBoca)."""
    return []


def techo_en(perfil, z):
    if not perfil:
        return None
    if z <= perfil[0][0]:
        return perfil[0][1]
    for (z0, y0), (z1, y1) in zip(perfil, perfil[1:]):
        if z0 <= z <= z1:
            return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
    return perfil[-1][1]


JS_MEDIR = r"""
(a) => {
  const L = window.__lab, THREE = window.__THREE, eos = window.__eos;
  if (a.K) Object.assign(L.KL, a.K);
  Object.keys(L.bocaM.morphTargetDictionary).forEach(n => L.poner(n, 0));
  L.poner('jawOpen', a.jaw);
  L.lengua(a.c, a.jaw);
  eos.updateMatrixWorld(true); L.bocaM.skeleton.update();
  const o = L.padreL.getWorldPosition(new THREE.Vector3());
  const pts = L.bocaIdx.lengua.map(i => { const p = L.verticeBoca(i).clone().sub(o).multiplyScalar(1000); return [p.x, p.y, p.z]; });
  const inc = L.bocaIdx.incisivos.map(i => { const p = L.verticeBoca(i).clone().sub(o).multiplyScalar(1000); return [p.x, p.y, p.z]; });
  window.__qRep = L.lenguaReposo.map(r => r.q);
  const giros = L.LENGUA.map((h, i) => { const e = new THREE.Euler().setFromQuaternion(window.__qRep[i].clone().invert().multiply(h.quaternion)); return [e.x, e.y, e.z].map(v => Math.round(v * 100) / 100); });
  return { pts, inc, giros, KL: L.KL, techo: L.techoBoca };
}
"""

JS_CORTE = r"""
(a) => {
  const L = window.__lab, THREE = window.__THREE, eos = window.__eos;
  const o = L.padreL.getWorldPosition(new THREE.Vector3());
  L.renderer.localClippingEnabled = true;
  const plano = new THREE.Plane(new THREE.Vector3(-1, 0, 0), o.x + 0.0003);
  eos.traverse(m => { if (m.isMesh) [].concat(m.material).forEach(mt => { mt.clippingPlanes = [plano]; mt.side = THREE.DoubleSide; mt.needsUpdate = true; }); });
  L.scene.traverse(m => { if (m.isMesh) [].concat(m.material).forEach(mt => { mt.clippingPlanes = [plano]; mt.side = THREE.DoubleSide; mt.needsUpdate = true; }); });
  const cam = L.camara; const d = a.dist || 0.16;
  cam.position.set(o.x + d, o.y + 0.012, o.z - 0.002);
  L.controles.target.set(o.x, o.y + 0.012, o.z - 0.002); L.controles.update();
  L.renderer.render(L.scene, cam);
  return { fov: cam.fov };
}
"""


def resumen(pts, inc, perfil):
    def mx(cands, key):
        cands = list(cands)
        return max(cands, key=key) if cands else [None, None, None]
    tip = mx((p for p in pts if abs(p[0]) < 4), key=lambda p: p[2])
    cima = mx(pts, key=lambda p: p[1])
    dorso = mx((p for p in pts if p[2] < -8), key=lambda p: p[1])
    pala = mx((p for p in pts if -2 < p[2] < 12), key=lambda p: p[1])
    con_techo = [(techo_en(perfil, p[2]), p) for p in pts if abs(p[0]) < 6]
    con_techo = [(t, p) for t, p in con_techo if t is not None]
    holg = min(((t - p[1], p) for t, p in con_techo), default=(None, [None, None, None]))
    dentro = sum(1 for t, p in con_techo if p[1] > t)
    lateral = max([abs(p[0]) for p in pts if p[2] > 10] or [0])
    frente_inc = max(p[2] for p in inc) if inc else None
    r1 = lambda q: [None if v is None else round(v, 1) for v in q]
    return {"punta": r1(tip), "cima": r1(cima), "dorso": r1(dorso), "pala": r1(pala), "holgura_min": None if holg[0] is None else round(holg[0], 1), "holgura_en": r1(holg[1]),
            "vertices_sobre_techo": dentro, "asoma_mm": None if frente_inc is None or tip[2] is None else round(tip[2] - frente_inc, 1),
            "x_max_punta": round(lateral, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--etiqueta", default="pre")
    ap.add_argument("--K", default="")
    ap.add_argument("--sonidos", default="reposo,i,ɪ,ɛ,æ,ʌ,ɑ,ɔ,ʊ,u,j,w,l,t,s,θ,ʃ,tʃ,ɹ,ɝ,k,ŋ")
    ap.add_argument("--sin-corte", action="store_true")
    ap.add_argument("--dist", type=float, default=0.16)
    a = ap.parse_args()
    K = {k: float(v) for k, v in (x.split("=") for x in a.K.split(",") if x)}
    P = json.load(open(POSES, encoding="utf-8"))
    perfil = techo()
    salida = {}
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])
        pag = nav.new_page(viewport={"width": 640, "height": 640})
        pag.on("pageerror", lambda e: print("pageerror:", e))
        pag.goto(URL)
        pag.wait_for_function("window.listo === true", timeout=300000)
        for s in a.sonidos.split(","):
            pose = P["reposo"] if s == "reposo" else P["sonidos"][s]
            c = canales(pose)
            jaw = round(float(pose.get("mandibula", 0.2)) * MAND, 3)
            r = pag.evaluate(JS_MEDIR, {"c": c, "jaw": jaw, "K": K or None})
            if s == a.sonidos.split(",")[0]:
                print("techo del visor (mm, z de -42 a +27 cada 3):", [None if y is None else round(y * 1000, 1) for y in r["techo"]])
                perfil = [(-42 + (k + 0.5) * 3, y * 1000) for k, y in enumerate(r["techo"]) if y is not None]
            res = resumen(r["pts"], r["inc"], perfil)
            res["jaw"] = jaw; res["giros_x"] = [g[0] for g in r["giros"]]
            salida[s] = res
            print(f"{s:7s} jaw {jaw:.2f} punta {res['punta']} cima {res['cima']} dorso {res['dorso']} pala {res['pala']} "
                  f"holgura {res['holgura_min']} en {res['holgura_en']} sobre_techo {res['vertices_sobre_techo']} "
                  f"asoma {res['asoma_mm']} |x|punta {res['x_max_punta']} giros_x {res['giros_x']}")
            if not a.sin_corte:
                pag.evaluate(JS_CORTE, {"dist": a.dist})
                pag.screenshot(path=str(AQUI / f"corte_{a.etiqueta}_{s}.png"))
        if K:
            print("KL:", r["KL"])
        nav.close()
    json.dump(salida, open(AQUI / f"calibracion_{a.etiqueta}.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
