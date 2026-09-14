"""Roce de la lengua glb con encias, hueso y dientes en las 53 poses del JSON.

Metodo independiente de entrega-4e (lee el glb sin Blender, necesita numpy):
sirve para contrastar la comprobacion que hace tools/boca3d_blender/lengua.py
al exportar. Validado contra escena.ts de boca3d 75f334a (pivote, giro de la
mandibula, lengua dentro de la mandibula y morfosDe no cambian desde 41eebc0).

Como escena.ts: la lengua es hija de `dentroMandibula` (gira con la
mandibula en PIVOTE_MAND), el morfo `mandibula` va al 30 % y el resto de
influencias salen de morfosDe. Los tubos y dientes de abajo giran con la
mandibula; los de arriba no. Profundidad >0 = entra; se da tambien la holgura
minima (<0) para ver lo cerca que pasa.

    python -X utf8 medir_roces.py poses.json lengua_a.glb [lengua_b.glb ...]
"""
import json, math, struct, sys
import numpy as np

ANCHO = 2.7
PIV = np.array([2.6, 0.9])
MAND_MAX = 0.42
U = np.linspace(-1, 1, 801)


def cargar_glb(ruta):
    d = open(ruta, "rb").read()
    _, _, total = struct.unpack_from("<III", d, 0)
    off, g, binario = 12, None, None
    while off < total:
        largo, tipo = struct.unpack_from("<II", d, off)
        c = d[off + 8: off + 8 + largo]
        if tipo == 0x4E4F534A: g = json.loads(c)
        elif tipo == 0x004E4942: binario = c
        off += 8 + largo
    def acc(i):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]
        ini = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(binario, dtype=np.float32, count=a["count"] * 3, offset=ini).reshape(-1, 3).astype(np.float64)
    m = g["meshes"][0]; p = m["primitives"][0]
    nodo = next(n for n in g["nodes"] if n.get("mesh") == 0)
    assert not any(k in nodo for k in ("translation", "rotation", "scale", "matrix")), nodo
    return acc(p["attributes"]["POSITION"]), {n: acc(t["POSITION"]) for n, t in zip(m["extras"]["targetNames"], p["targets"])}


EXPO_ARCO = 2.6                 # la arcada de cara.py


def arco(u, ret=2.3):
    return np.stack([-2.6 + ret * np.abs(u) ** EXPO_ARCO, (ANCHO / 2) * u], axis=-1)


def tangente_arco(u, ret=2.3):
    return ret * EXPO_ARCO * abs(u) ** (EXPO_ARCO - 1) * (1 if u >= 0 else -1)


def rotar(xy, ang):
    c, s = math.cos(ang), math.sin(ang)
    r = xy - PIV
    return np.stack([c * r[:, 0] - s * r[:, 1], s * r[:, 0] + c * r[:, 1]], axis=1) + PIV


def piezas(ang):
    tubos, dientes = [], []
    a = arco(U)
    tubos.append((np.stack([a[:, 0], np.full(len(U), 0.98), a[:, 1]], 1), 0.2, "encia sup"))
    for y, r, ret, nombre in ((-0.2, 0.2, 2.3, "encia inf"), (-0.62, 0.28, 2.6, "hueso inf")):
        a = arco(U, ret)
        xy = rotar(np.stack([a[:, 0], np.full(len(U), y)], 1), ang)
        tubos.append((np.stack([xy[:, 0], xy[:, 1], a[:, 1]], 1), r, nombre))
    for u in [-0.92, -0.76, -0.6, -0.44, -0.28, -0.1, 0.1, 0.28, 0.44, 0.6, 0.76, 0.92]:
        pt = arco(np.array([u]))[0]
        w, dd = (0.34, 0.24) if abs(u) < 0.3 else (0.34, 0.3) if abs(u) < 0.5 else (0.38, 0.36) if abs(u) < 0.85 else (0.46, 0.42)
        rot_y = -math.atan2(tangente_arco(u), ANCHO / 2)
        dientes.append((np.array([pt[0], 0.7, pt[1]]), rot_y, dd, 0.5, w, f"diente sup u={u:+.2f}", 0.0))
        dientes.append((np.array([pt[0], 0.1, pt[1]]), rot_y, dd, 0.5, w, f"diente inf u={u:+.2f}", ang))
    return tubos, dientes


def morfos_de(p):
    alt, ade = p["cuerpo"]
    return {"mandibula": 0.3 * min(1, max(0, p["mandibula"])),
            "punta_arriba": (1 if p["punta_toca"] else 0.75) if p["punta"] in ("alveolar", "postalveolar") else (0.45 if p["punta"] == "dental" else 0),
            "punta_atras": 1 if p["punta"] == "retrofleja" else 0,
            "punta_interdental": 1 if p["punta"] == "interdental" else 0,
            "cuerpo_alto": max(0, (alt - 0.45) / 0.55), "cuerpo_bajo": max(0, (0.45 - alt) / 0.45),
            "cuerpo_delante": max(0, (ade - 0.5) / 0.5), "cuerpo_atras": max(0, (0.5 - ade) / 0.5),
            "dorso_velo": 1 if p["dorso_velo"] else min(1, p["dorso_alto"]),
            "raiz_atras": min(1, max(0, p["raiz"]))}


def medir(pos, deltas, pose):
    infl = morfos_de(pose)
    ang = min(1, max(0, pose["mandibula"])) * MAND_MAX
    v = pos.copy()
    for k, w in infl.items():
        if w: v += w * deltas[k]
    xy = rotar(v[:, :2], ang)
    v = np.stack([xy[:, 0], xy[:, 1], v[:, 2]], 1)
    tubos, dientes = piezas(ang)
    peor = (-np.inf, None, None)
    for curva, r, nombre in tubos:
        for trozo in np.array_split(np.arange(len(v)), 8):
            dist = np.min(np.linalg.norm(v[trozo][:, None, :] - curva[None, ::2, :], axis=2), axis=1)
            pen = r - dist
            i = int(np.argmax(pen))
            if pen[i] > peor[0]:
                peor = (float(pen[i]), nombre, tuple(np.round(v[trozo][i], 2)))
    for centro, rot_y, dd, alto, w, nombre, ang_m in dientes:
        c = centro.copy()
        if ang_m:
            c[:2] = rotar(c[None, :2], ang_m)[0]
        rel = v - c
        if ang_m:
            cs, sn = math.cos(-ang_m), math.sin(-ang_m)
            rel = np.stack([cs * rel[:, 0] - sn * rel[:, 1], sn * rel[:, 0] + cs * rel[:, 1], rel[:, 2]], 1)
        cy, sy = math.cos(-rot_y), math.sin(-rot_y)
        lx = cy * rel[:, 0] + sy * rel[:, 2]
        lz = -sy * rel[:, 0] + cy * rel[:, 2]
        ly = rel[:, 1]
        # distancia con signo a la caja: >0 dentro (margen a la cara mas cercana), <0 fuera
        q = np.stack([np.abs(lx) - dd / 2, np.abs(ly) - alto / 2, np.abs(lz) - w / 2], 1)
        fuera = np.linalg.norm(np.maximum(q, 0), axis=1)
        dentro = -np.minimum(q.max(axis=1), 0)
        pen = np.where(fuera > 0, -fuera, dentro)
        i = int(np.argmax(pen))
        if pen[i] > peor[0]:
            peor = (float(pen[i]), nombre, tuple(np.round(v[i], 2)))
    return peor


poses_json = json.load(open(sys.argv[1], encoding="utf-8"))
poses = dict(poses_json["sonidos"])
poses.update({f"rp:{k}": v for k, v in poses_json["rp"].items()})
poses["reposo"] = poses_json["reposo"]
mallas = [(r.rsplit("/", 1)[-1].rsplit("\\", 1)[-1], *cargar_glb(r)) for r in sys.argv[2:]]
print(f"{len(poses)} poses | " + " | ".join(f"{n}: {len(p)} vertices" for n, p, _ in mallas))
resultados = {n: {} for n, _, _ in mallas}
for nombre, pose in poses.items():
    fila = []
    for n, pos, deltas in mallas:
        r = medir(pos, deltas, pose)
        resultados[n][nombre] = r
        fila.append(f"{r[0]:+.3f} {r[1]} {r[2]}")
    print(f"{nombre:8s} " + " || ".join(f"{c:52s}" for c in fila))
for n in resultados:
    orden = sorted(resultados[n].items(), key=lambda kv: -kv[1][0])
    print(f"\n{n}: peor {orden[0][0]} {orden[0][1][0]:+.3f} {orden[0][1][1]}; poses > +0,005: "
          + ", ".join(f"{k} {v[0]:+.3f}" for k, v in orden if v[0] > 0.005) or "ninguna")
