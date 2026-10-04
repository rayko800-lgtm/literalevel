"""Mide la lengua de Eos en el visor aislado (8790): qué hace cada eje local de cada hueso de la
lengua y cómo se mueve la punta a lo largo de un clip, en ejes de la cabeza quieta (x lateral,
y arriba, z adelante), en mm respecto al reposo. Con el visor del 4 oct 2026 (window.__lab) mide
también cuánto se hunde la lengua en el techo de la boca y el salto de la punta entre fotogramas.

    python -X utf8 tools/eos_pronunciar/medir_lengua.py ga_006c ga_0070 ...   # → lengua_medidas/<clip>.json

Lo que debe salir con el visor arreglado: lateral 0 mm (antes, hasta 12 mm en /l/: los giros iban
sobre el eje y, que es el lateral), techo ≤ 2-4 mm y solo en fotogramas sueltos, saltos ≤ 4 mm.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8790"
CLIPS = Path("D:/literalevel_eos_pronunciar/visor/clips")
AQUI = Path.cwd() / "lengua_medidas"
AQUI.mkdir(exist_ok=True)
clips = sys.argv[1:] or ["ga_006c"]

JS_REF = r"""
() => {
  const eos = window.__eos, THREE = window.__THREE;
  const T = ['FACIAL_C_Tongue1','FACIAL_C_Tongue2','FACIAL_C_Tongue3','FACIAL_C_Tongue4'].map(n => eos.getObjectByName(n));
  const padre = T[0].parent;
  eos.updateMatrixWorld(true);
  const qRest = padre.getWorldQuaternion(new THREE.Quaternion());
  const pos = h => { eos.updateMatrixWorld(true);
    const p = h.getWorldPosition(new THREE.Vector3()), o = padre.getWorldPosition(new THREE.Vector3());
    const q = padre.getWorldQuaternion(new THREE.Quaternion()).invert();
    return p.sub(o).applyQuaternion(q).applyQuaternion(qRest); };
  const base = T.map(pos);
  window.__ref = { T, padre, qRest, base, pos };
  const rest = T.map(h => h.quaternion.clone());
  const mm = v => [v.x, v.y, v.z].map(x => Math.round(x * 10000) / 10);
  const out = { padre: padre.name, cadena: [], reposo_mm: base.map(mm), ejes: {} };
  let p = padre; while (p) { out.cadena.push(p.name); p = p.parent; }
  for (let i = 0; i < 4; i++) for (const eje of ['x', 'y', 'z']) {
    const e = new THREE.Euler(0, 0, 0); e[eje] = 0.3;
    T[i].quaternion.copy(rest[i]).multiply(new THREE.Quaternion().setFromEuler(e));
    out.ejes[`T${i + 1}.${eje}+0.3`] = { punta: mm(pos(T[3]).sub(base[3])), t3: mm(pos(T[2]).sub(base[2])), t2: mm(pos(T[1]).sub(base[1])) };
    T[i].quaternion.copy(rest[i]);
  }
  eos.updateMatrixWorld(true);
  return out;
}
"""

JS_FRAME = r"""
(t) => {
  window.pintar(t);
  const { T, base, pos } = window.__ref;
  const mm = v => [v.x, v.y, v.z].map(x => Math.round(x * 10000) / 10);
  // hundimiento en el techo (visor nuevo): máximo entre los vértices de la línea media de la lengua
  let pen = null, lat = null;
  const L = window.__lab;
  if (L && L.techoBoca) {
    const THREE = window.__THREE, eos = window.__eos;
    eos.updateMatrixWorld(true); L.bocaM.skeleton.update(); L.prepararBoca();
    const Z0 = -0.042, PASO = 0.003, N = L.techoBoca.length;
    const techo = z => { const f = (z - Z0) / PASO - 0.5, b = Math.max(0, Math.min(N - 2, Math.floor(f))), a = Math.max(0, Math.min(1, f - b)); return L.techoBoca[b] * (1 - a) + L.techoBoca[b + 1] * a; };
    pen = -1e9; lat = 0;
    for (const i of L.bocaIdx.lengua) { const p = L.enBoca(L.verticeBoca(i)); if (p.z > 0.008 && Math.abs(p.x) > lat) lat = Math.abs(p.x); if (Math.abs(p.x) > 0.006) continue; const d = p.y - techo(p.z); if (d > pen) pen = d; }
    pen = Math.round(pen * 10000) / 10; lat = Math.round(lat * 10000) / 10;
  }
  return { punta: mm(pos(T[3]).sub(base[3])), t3: mm(pos(T[2]).sub(base[2])), t2: mm(pos(T[1]).sub(base[1])), pen, lat };
}
"""


def main():
    resumen = {}
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True,
                                args=["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"])
        pag = nav.new_page(viewport={"width": 320, "height": 320})
        pag.on("pageerror", lambda e: print("pageerror:", e))
        ejes = None
        for clip in clips:
            pag.goto(f"{URL}/index.html?grabar=clips/{clip}&camara=0,-0.035,0.62")
            pag.wait_for_function("window.listo === true", timeout=300000)
            ref = pag.evaluate(JS_REF)
            if ejes is None:
                ejes = ref
                print("padre:", ref["padre"], "| cadena:", " > ".join(ref["cadena"][:5]))
                print("reposo (mm, x lateral / y arriba / z adelante):", ref["reposo_mm"])
                for k, v in ref["ejes"].items():
                    print(f"  {k:10s} punta {v['punta']}  T3 {v['t3']}  T2 {v['t2']}")
            datos = json.load(open(CLIPS / clip / "curvas.json", encoding="utf-8"))
            fps, n = datos["fps"], len(datos["cabeza"])
            filas = [pag.evaluate(JS_FRAME, i / fps) for i in range(n)]
            punta = [f["punta"] for f in filas]
            t3 = [f["t3"] for f in filas]
            dx = [abs(q[0]) for q in punta]
            dx3 = [abs(q[0]) for q in t3]
            res = {"fps": fps, "n": n,
                   "punta_x_max": max(dx), "punta_x_media": round(sum(dx) / n, 2),
                   "t3_x_max": max(dx3), "t3_x_media": round(sum(dx3) / n, 2),
                   "punta_y": [min(q[1] for q in punta), max(q[1] for q in punta)],
                   "punta_z": [min(q[2] for q in punta), max(q[2] for q in punta)]}
            # qué canal explica el movimiento lateral: correlación de |x| de la punta con cada canal
            import math
            corr = {}
            for k, arr in (datos.get("lengua") or {}).items():
                a = arr[:n]
                if max(a) - min(a) < 1e-6:
                    continue
                xs = [q[0] for q in punta]
                ma, mx = sum(a) / n, sum(xs) / n
                num = sum((u - ma) * (v - mx) for u, v in zip(a, xs))
                den = math.sqrt(sum((u - ma) ** 2 for u in a) * sum((v - mx) ** 2 for v in xs)) or 1
                corr[k] = round(num / den, 2)
            res["corr_x_canales"] = corr
            saltos = [math.hypot(punta[i][1] - punta[i - 1][1], punta[i][2] - punta[i - 1][2]) for i in range(1, n)]
            res["salto_punta_max_mm"] = round(max(saltos), 1)
            res["fotogramas_salto_mas_de_4mm"] = sum(1 for s_ in saltos if s_ > 4)
            pens = [f["pen"] for f in filas if f["pen"] is not None]
            if pens:
                res["techo_hundimiento_max_mm"] = max(pens)
                res["fotogramas_mas_de_1mm"] = sum(1 for p_ in pens if p_ > 1.0)
                res["ancho_punta_max_mm"] = max(f["lat"] for f in filas)
            json.dump({"resumen": res, "punta": punta, "t3": t3, "t2": [f["t2"] for f in filas], "pen": [f["pen"] for f in filas],
                       "lengua": datos.get("lengua"), "jawOpen": datos["curvas"].get("jawOpen")},
                      open(AQUI / f"{clip}.json", "w"), indent=0)
            resumen[clip] = res
            print(clip, json.dumps(res, ensure_ascii=False))
        nav.close()
    json.dump({"ejes": ejes, "clips": resumen}, open(AQUI / "resumen.json", "w"), indent=1)


if __name__ == "__main__":
    main()
