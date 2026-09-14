"""Saca la cabeza de la malla base de MakeHuman a un OBJ pequeño que sí va en
el repositorio (tools/boca3d_blender/makehuman_cabeza.obj).

Origen: makehuman/data/3dobjs/base.obj de la etiqueta v1.3.0 del repositorio
oficial github.com/makehumancommunity/makehuman (descargado a
build/makehuman/base.obj con `gh api ... -H "Accept: application/vnd.github.raw"`).
Licencia: la cabecera del propio base.obj dice «This asset was explicitly
released as CC0 in september 2020», y LICENSE.md (C) del repositorio: «The base
mesh and proxies [...] have been released under CC0 1.0 Universal». La FAQ de
MakeHuman: «The asset license is CC0. In practice this imposes no restriction
on your use of the core assets, be they used through MakeHuman or copied
through some other means.»

Se queda solo con las caras del grupo `body` cuyos vértices están por encima
del cuello (y >= 5.6 en decímetros de MakeHuman) y con los ocho vértices de
cada articulación de ojo (centro de cada globo ocular). Coordenadas de
MakeHuman sin tocar (y arriba, +z la cara, decímetros); cara.py las convierte.

    python -X utf8 tools/boca3d_blender/recortar_makehuman.py
"""
from __future__ import annotations

import os

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(AQUI, "..", "..", "build", "makehuman", "base.obj")
SALIDA = os.path.join(AQUI, "makehuman_cabeza.obj")
Y_CUELLO = 5.6

vertices: list[tuple[float, float, float]] = []
caras: list[list[int]] = []
ojos: dict[str, list[int]] = {"joint-l-eye": [], "joint-r-eye": []}
grupo = ""
with open(ORIGEN, encoding="utf-8") as f:
    for linea in f:
        if linea.startswith("v "):
            x, y, z = map(float, linea.split()[1:4])
            vertices.append((x, y, z))
        elif linea.startswith("g "):
            grupo = linea.split(None, 1)[1].strip()
        elif linea.startswith("f "):
            idx = [int(p.split("/")[0]) - 1 for p in linea.split()[1:]]
            if grupo == "body" and all(vertices[i][1] >= Y_CUELLO for i in idx):
                caras.append(idx)
            elif grupo in ojos:
                ojos[grupo].extend(idx)

usados = sorted({i for c in caras for i in c})
nuevo = {viejo: k for k, viejo in enumerate(usados)}
centros = {}
for nombre, idx in ojos.items():
    puntos = [vertices[i] for i in sorted(set(idx))]
    centros[nombre] = tuple(sum(p[k] for p in puntos) / len(puntos) for k in range(3))

with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
    f.write("# Cabeza de la malla base de MakeHuman 1.3.0 (makehuman/data/3dobjs/base.obj,\n"
            "# grupo body, y >= 5.6), recortada por tools/boca3d_blender/recortar_makehuman.py.\n"
            "# Licencia CC0 1.0 Universal (cabecera del original: «This asset was explicitly\n"
            "# released as CC0 in september 2020»; LICENSE.md del repositorio, apartado C).\n"
            "# Coordenadas de MakeHuman: decimetros, y arriba, +z la cara.\n")
    for nombre, c in centros.items():
        f.write("# %s %.4f %.4f %.4f\n" % (nombre, *c))
    for i in usados:
        f.write("v %.4f %.4f %.4f\n" % vertices[i])
    f.write("g cabeza\n")
    for c in caras:
        f.write("f " + " ".join(str(nuevo[i] + 1) for i in c) + "\n")
print("MAKEHUMAN_CABEZA_OK", {"vertices": len(usados), "caras": len(caras), "ojos": centros,
                             "bytes": os.path.getsize(SALIDA)})
