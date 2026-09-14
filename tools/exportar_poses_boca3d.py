"""Exporta las poses articulatorias a JSON para el visor 3D de la boca.

Lee `app/animacion_articulatoria.PARAMETROS` (los 46 sonidos del corte 2D) y
escribe un JSON con cada objetivo YA RESUELTO contra el reposo (sin campos
libres), la pose de reposo y las duraciones por tipo de movimiento que usa
`trocear`/`_linea_palabra` para una palabra. Es el contrato que la API podria
servir despues en una ruta propia; el front lo lleva embebido mientras tanto.

Solo lee el modulo: no lo edita. Biblioteca estandar.

    python -X utf8 tools/exportar_poses_boca3d.py [salida.json]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "app"))

import animacion_articulatoria as anim  # noqa: E402

SALIDA = RAIZ / "front" / "src" / "app" / "compartido" / "boca3d" / "poses.ejemplo.json"


def _pose(art: anim.Articulacion, vecino: anim.Articulacion = anim.REPOSO) -> dict:
    a = anim._resolver(art, vecino)
    d = {
        "movimiento": a.movimiento,
        # Campos que PARAMETROS deja libres (None): en una palabra los pone la
        # vocal vecina, no el reposo. `cuerpo` libre arrastra raiz y dorso_alto.
        "libres": [c for c in ("mandibula", "labios", "punta", "cuerpo") if getattr(art, c) is None],
        "mandibula": round(float(a.mandibula), 3),
        "labios": a.labios,
        "punta": a.punta,
        "punta_toca": bool(a.punta_toca),
        "cuerpo": [round(float(a.cuerpo[0]), 3), round(float(a.cuerpo[1]), 3)],
        "dorso_velo": bool(a.dorso_velo),
        "dorso_alto": round(float(a.dorso_alto), 3),
        "raiz": round(float(a.raiz), 3),
        "velo_abierto": bool(a.velo_abierto),
        "sonora": bool(a.sonora),
        "lugar": a.lugar,
        "larga": bool(a.larga),
        "leyenda": a.leyenda,
    }
    if art.hacia is not None:
        # Diptongo: el segundo objetivo se resuelve contra el reposo; africada,
        # contra la fase de cierre (igual que `_objetivos` en el 2D).
        vecino_b = anim.REPOSO if art.movimiento == "diptongo" else a
        d["hacia"] = _pose(art.hacia, vecino_b)
    return d


def exportar() -> dict:
    return {
        "version": 1,
        "origen": "app/animacion_articulatoria.PARAMETROS",
        "escala": {"mandibula": "0 dientes juntos .. 1 muy abierta",
                   "cuerpo": "[altura, adelantamiento] 0..1",
                   "labios": list(anim.LABIOS), "punta": list(anim.PUNTAS),
                   "movimiento": list(anim.MOVIMIENTOS)},
        "duracion_s": dict(anim._DURACION),
        "factor_lento": anim._LENTO,
        "reposo": _pose(anim.REPOSO),
        "sonidos": {s: _pose(a) for s, a in anim.PARAMETROS.items()},
        "rp": {s: _pose(a) for s, a in anim.PARAMETROS_RP.items()},
    }


def main() -> None:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else SALIDA
    datos = exportar()
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(datos['sonidos'])} sonidos + {len(datos['rp'])} de RP -> {salida}")


if __name__ == "__main__":
    main()
