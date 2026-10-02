"""Consulta OSV para el cierre de dependencias Python instalado del proyecto."""
import json
import re
import time
from importlib import metadata
from pathlib import Path

import requests
from packaging.requirements import Requirement

raiz = Path(__file__).resolve().parents[1]
pendientes = []
for linea in (raiz / "requirements.txt").read_text(encoding="utf-8").splitlines():
    linea = linea.split("#")[0].strip()
    if linea:
        pendientes.append(Requirement(linea).name)
vistas = {}
while pendientes:
    nombre = pendientes.pop()
    normal = re.sub("[-_.]+", "-", nombre).lower()
    if normal in vistas: continue
    d = metadata.distribution(nombre)
    vistas[normal] = d.version
    for entrada in d.requires or []:
        q = Requirement(entrada)
        if q.marker is None or q.marker.evaluate(): pendientes.append(q.name)
items = sorted(vistas.items())
hallazgos = []
for i in range(0, len(items), 100):
    lote = items[i:i + 100]
    r = requests.post("https://api.osv.dev/v1/querybatch", json={"queries": [
        {"package": {"name": n, "ecosystem": "PyPI"}, "version": v} for n, v in lote]}, timeout=60)
    r.raise_for_status()
    for (n, v), resultado in zip(lote, r.json()["results"]):
        if resultado.get("vulns"):
            hallazgos.append({"paquete": n, "version": v, "advisories": [x["id"] for x in resultado["vulns"]]})
salida = {"momento_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "entorno": "Python local, dependencias y marcadores instalados; no es un SBOM del contenedor Linux",
    "paquetes": vistas, "hallazgos": hallazgos}
(raiz / "auditoria" / "seguridad_dependencias_2026-10-01.json").write_text(json.dumps(salida, indent=2), encoding="utf-8")
print(json.dumps({"paquetes_revisados": len(vistas), "hallazgos": hallazgos}))
