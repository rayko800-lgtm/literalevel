"""Pruebas de la parte pura del cuaderno de portadas (tools/colab_portadas.py).

Solo ejecuta las celdas marcadas `# %% [puro]`: nada de GPU, red ni Colab. El
cuaderno es la unica fuente de las reglas; aqui se comprueba que:
- el prompt nunca lleva titulo, autor ni nombres propios, y siempre pide sin
  texto y sin caras;
- la semilla es determinista y la decada sale de las fechas del autor;
- la paleta y los contrastes WCAG son los que dicen;
- las reglas de exclusion son las MISMAS que las de app/catalogo.py.

Uso:  python -X utf8 pruebas_portadas.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
import ast
import json
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, "app")
os.environ["LITERALEVEL_DATOS"] = tempfile.mkdtemp(prefix="literalevel_portadas_")

FALLOS: list[str] = []
HECHAS = 0


def prueba(nombre, fn):
    global HECHAS
    HECHAS += 1
    try:
        r = fn()
        print(f"  ok   {nombre}" + (f"  -> {r}" if r else ""))
    except Exception as e:
        FALLOS.append(nombre)
        print(f"  FALLA {nombre}  -> {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)


def _celdas_puras() -> dict:
    fuente = Path("tools/colab_portadas.py").read_text(encoding="utf-8")
    trozos = fuente.split("# %%")
    puros = [t[len(" [puro]"):] for t in trozos if t.startswith(" [puro]")]
    assert puros, "el cuaderno no tiene celdas [puro]"
    espacio: dict = {}
    exec(compile("\n".join(puros), "colab_portadas[puro]", "exec"), espacio)
    return espacio


P = _celdas_puras()
FILA = {"id": "PG11", "title": "Alice's Adventures in Wonderland",
        "author": "Carroll, Lewis, 1832-1898",
        "hook": "Alice follows the White Rabbit down a hole in Oxford and meets the Queen.",
        "temas": "Fantasy fiction; Alice (Fictitious character) -- Juvenile fiction; Wonderland (Imaginary place)"}

print("\nPortadas: parte pura")


def _prompt_sin_titulo_ni_autor():
    p = P["construir_prompt"](FILA)
    bajo = p.lower()
    for prohibida in ("alice", "wonderland", "carroll", "lewis", "rabbit hole", "oxford", "queen"):
        assert prohibida not in bajo, f"el prompt lleva «{prohibida}»: {p}"
    assert "no text" in bajo and "no faces" in bajo and "no people" in bajo, p
    assert "floating castle" in bajo, "no usa el motivo de Fantasy fiction"
    assert "1860s" in bajo, "no pone la decada del autor"
    return p[:120] + "…"


prueba("el prompt no lleva titulo, autor ni nombres, y pide sin texto ni caras", _prompt_sin_titulo_ni_autor)


def _decada_y_semilla():
    assert P["decada"]("Carroll, Lewis, 1832-1898") == "1860s"
    assert P["decada"]("Shakespeare, William, 1564-1616") == "1590s"
    assert P["decada"]("Anonymous") is None and P["decada"]("") is None
    s = P["semilla"]
    assert s("PG11") == s("pg11") and s("PG11") != s("PG12") and 0 <= s("PG11") < 2**32
    return f"PG11 -> {s('PG11')}"


prueba("la decada sale del autor y la semilla es determinista por id", _decada_y_semilla)


def _motivos():
    M = P["MOTIVOS"]
    assert len(M) == 30, f"el mapa tiene {len(M)} temas, no 30"
    assert P["motivos_de"]("Nada que ver; Tampoco") == [P["MOTIVO_POR_DEFECTO"]]
    assert P["motivos_de"]("Science fiction; Horror tales -- 20th century; England -- Fiction", maximo=2) == \
        [M["Science fiction"], M["Horror tales"]]
    for tema, motivo in M.items():
        assert not any(w in motivo.lower() for w in ("face", "portrait of", " text", "letter")) or "no face" in motivo, \
            f"el motivo de {tema} pide caras o texto: {motivo}"
    return "30 temas, orden respetado, motivo por defecto"


prueba("el mapa de 30 temas a motivos se aplica en orden", _motivos)


def _contraste_y_paleta():
    c = P["contraste"]
    assert c("#FFFFFF", "#000000") == 21.0 and c("#777777", "#777777") == 1.0
    from PIL import Image
    img = Image.new("RGB", (80, 120), (20, 40, 90))
    for x in range(30):
        for y in range(120):
            img.putpixel((x, y), (230, 180, 40))
    pal = P["paleta_de"](img)
    assert 1 <= len(pal) <= 5 and abs(sum(p["proporcion"] for p in pal) - 1) < 0.01, pal
    assert pal[0]["proporcion"] >= pal[-1]["proporcion"], "la paleta no va de mas a menos"
    col = P["colores_de_lectura"](pal)
    assert col["contraste_texto"] >= 4.5, col
    assert c("#F2F2F2", col["fondo_lector"]) >= 7.0, col
    assert col["contraste_acento"] >= 4.5, col
    return f"dominante {pal[0]['hex']}, texto {col['color_texto']}, fondo {col['fondo_lector']}, acento {col['acento']}"


prueba("paleta de 5 colores y contrastes WCAG del lector", _contraste_y_paleta)


def _json_contrato():
    pal = [{"hex": "#223344", "proporcion": 0.6}, {"hex": "#DDAA33", "proporcion": 0.4}]
    d = P["json_de_portada"](FILA, P["construir_prompt"](FILA), pal, 123.4, 12.3, 1.87)
    for clave in ("id", "modelo", "semilla", "prompt_sha", "paleta", "color_texto", "fondo_lector",
                  "acento", "archivos", "kb", "generada_por_ia", "aviso"):
        assert clave in d, f"falta {clave} en el JSON"
    assert d["id"] == "PG11" and d["generada_por_ia"] is True and d["aviso"] == "Portada generada por IA, no oficial"
    assert d["archivos"] == {"portada": "PG11.webp", "miniatura": "PG11_256.webp"}
    assert "Alice" not in str(d), "el JSON guarda el titulo o el prompt en claro"
    return "claves del contrato presentes, sin prompt en claro"


prueba("el JSON por portada cumple el contrato del front", _json_contrato)


def _mismas_reglas_que_la_app():
    import catalogo as cm
    assert P["NO_ES_LECTURA_TEMAS"] == cm._NO_ES_LECTURA_TEMAS.pattern, "temas de exclusion distintos de la app"
    assert P["NO_ES_LECTURA_TITULO"] == cm._NO_ES_LECTURA_TITULO.pattern, "titulos de exclusion distintos de la app"
    assert P["LITERARIO"] == cm._LITERARIO.pattern, "regla de literario distinta de la app"
    import pandas as pd
    df = pd.DataFrame({
        "id": ["PG1", "PG2", "PG3", "PG4"], "downloads": [10, 50, 40, 30],
        "title": ["Uno", "The Fairy Books A Project Gutenberg Linked Index", "Tres", "Cuatro"],
        "temas": ["Fiction", "Fairy tales", "Chemistry", "Love stories"], "author": [""] * 4, "hook": [""] * 4})
    sel = P["seleccionar"](df, "top_medido", n=10)
    assert sel["id"].tolist() == ["PG4", "PG1"], sel["id"].tolist()
    cur = P["seleccionar"](df, "curado", n=10, ids_curado=["PG1"])
    assert cur["id"].tolist() == ["PG1"], cur["id"].tolist()
    return "exclusion y literario identicos a app/catalogo.py"


prueba("la seleccion usa las mismas reglas que el catalogo de la app", _mismas_reglas_que_la_app)


def _presupuesto():
    validar = P["validar_presupuesto"]
    assert validar(10, 15, 600, True) == 2.5
    for saldo, tarifa, segundos, permiso in (
        (None, 15, 60, True), (0, 15, 60, True), (-1, 15, 60, True),
        (float("nan"), 15, 60, True), (float("inf"), 15, 60, True),
        (10, None, 60, True), (10, 0, 60, True), (10, 15, float("nan"), True),
        (10, 15, 60, False), (10, 15, 60, 1), (True, 15, 60, True), (1, 15, 600, True),
    ):
        try:
            validar(saldo, tarifa, segundos, permiso)
        except ValueError:
            pass
        else:
            raise AssertionError((saldo, tarifa, segundos, permiso))


prueba("el presupuesto exige permiso, saldo, tarifa y medida finitos con margen", _presupuesto)


def _reanudar_remoto():
    completos = P["ids_completos"]
    rutas = [f"portadas/shard_000/PG11{ext}" for ext in (".json", ".webp", "_256.webp")]
    assert completos(rutas) == {"PG11"}
    assert completos(rutas[:2]) == set()
    assert completos(rutas[:2] + ["portadas/shard_001/PG11_256.webp"]) == set()
    assert completos([r.replace("portadas/", "otro/") for r in rutas]) == set()
    assert completos(["portadas/progreso.json", "portadas/shard_000/../PG11.json"]) == set()
    filas = [{"id": "PG11"}, {"id": "pg12"}, {"id": "PG12"}]
    assert P["pendientes_de"](filas, {"PG11", "PG900", "PG901"}) == [(1, {"id": "pg12"})]
    for pid in ("../../PG11", "PG11/../", "", "PG-1"):
        try:
            P["id_seguro"](pid)
        except ValueError:
            pass
        else:
            raise AssertionError(pid)


prueba("reanudar exige ambos WebP junto al JSON y cuenta solo IDs seleccionados", _reanudar_remoto)


def _funciones_ejecucion():
    arbol = ast.parse(Path("tools/colab_portadas.py").read_text(encoding="utf-8"))
    funciones = [n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name in ("generar", "volcar")]
    espacio = dict(P)
    exec(compile(ast.Module(body=funciones, type_ignores=[]), "portadas[runtime]", "exec"), espacio)
    return espacio


def _cache_local():
    from PIL import Image
    import itertools
    E = _funciones_ejecucion()
    llamadas = []
    class Generador:
        def manual_seed(self, semilla):
            return self
    def tuberia(*args, **kwargs):
        llamadas.append(kwargs)
        return SimpleNamespace(images=[Image.new("RGB", (P["ANCHO"], P["ALTO"]), "#223344")])
    reloj = itertools.count()
    E.update(tuberia=tuberia, time=SimpleNamespace(time=lambda: next(reloj)), torch=SimpleNamespace(
        Generator=lambda dispositivo: Generador(), cuda=SimpleNamespace(synchronize=lambda: None)))
    with tempfile.TemporaryDirectory() as carpeta:
        E["LOCAL"] = Path(carpeta)
        rutas, datos = E["generar"](FILA)
        assert len(llamadas) == 1 and all(r.exists() for r in rutas)
        assert E["generar"](FILA)[1] == datos and len(llamadas) == 1
        assert not list(Path(carpeta).glob("*.tmp"))
        assert P["portada_local"]({**FILA, "temas": "Horror tales"}, carpeta) is None
        rutas[0].write_bytes(b"webp truncado")
        assert P["portada_local"](FILA, carpeta) is None
        E["generar"](FILA)
        assert len(llamadas) == 2
        rutas[2].write_text("[]", encoding="utf-8")
        assert P["portada_local"](FILA, carpeta) is None
        rutas[2].unlink()
        assert P["portada_local"](FILA, carpeta) is None


prueba("generar reutiliza la muestra sin GPU y rechaza cache parcial, corrupta o de otro prompt", _cache_local)


def _guardas_reales():
    fuente = Path("tools/colab_portadas.py").read_text(encoding="utf-8")
    celda3 = next(c for c in fuente.split("# %%") if "# --- 3." in c)
    # Ejecuta la configuracion REAL: debe parar antes de pedir secretos o importar torch.
    with tempfile.TemporaryDirectory() as carpeta:
        celda3 = celda3.replace('Path("/content/portadas")', f"Path({carpeta!r})")
        try:
            exec(compile(celda3, "portadas[config]", "exec"), dict(P))
        except ValueError as e:
            assert "autorizacion" in str(e)
        else:
            raise AssertionError("la configuracion permite ejecutar por defecto")
    E = _funciones_ejecucion()
    E["PUBLICAR_CONFIRMADO"] = False
    try:
        E["volcar"]([("shard_000", [Path("PG11.webp")])])
    except RuntimeError as e:
        assert "no autorizada" in str(e)
    else:
        raise AssertionError("se intento publicar sin permiso")


prueba("las celdas reales bloquean secretos/GPU por defecto y bloquean subir sin permiso", _guardas_reales)


def _notebook_sincronizado():
    from tools.a_notebook import celdas
    fuente = Path("tools/colab_portadas.py").read_text(encoding="utf-8")
    nb = json.loads(Path("tools/colab_portadas.ipynb").read_text(encoding="utf-8"))
    assert nb["cells"] == celdas(fuente), "regenerar tools/colab_portadas.ipynb"
    assert "accelerator" not in nb["metadata"], "no preseleccionar recursos GPU al abrir el cuaderno"


prueba("notebook sincronizado con la fuente y sin GPU preseleccionada", _notebook_sincronizado)

print()
if FALLOS:
    print(f"{len(FALLOS)} fallo(s) de {HECHAS} pruebas de portadas:")
    for n in FALLOS:
        print(f"- {n}")
    sys.exit(1)
print(f"Todas las pruebas de portadas pasan ({HECHAS}).")
