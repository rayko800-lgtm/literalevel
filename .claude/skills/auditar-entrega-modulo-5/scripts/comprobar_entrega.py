"""Comprobaciones mecánicas del paquete de entrega del Módulo 5 (Pléyade / LiteraLevel).

    python -X utf8 .claude/skills/auditar-entrega-modulo-5/scripts/comprobar_entrega.py
    python -X utf8 .../comprobar_entrega.py --sin-red        # sin tocar Vercel ni el Space
    python -X utf8 .../comprobar_entrega.py --json salida.json

Imprime una tabla Markdown por rubro con OK / AVISO / FALLO y la evidencia. Solo mide lo
que una máquina puede medir (archivos, páginas, duración, códecs, secciones, cifras
repetidas, salud de lo publicado). El juicio —si el documento se entiende, si la demo
convence— lo pone quien audita, con la SKILL.md de al lado.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
ENTREGA = RAIZ / "entrega"
VERCEL = "https://pleyade-app.vercel.app"
SPACE_API = "https://mikemaki1763-literalevel.hf.space"
SPACE_REPO = "MikeMaki1763/literalevel"
TOPE_VIDEO_S = 300

# Secciones que exige la rúbrica, en este orden (skill modulo-5-literalevel §3).
SECCIONES = ["Introducción", "Planteamiento del problema", "Estrategia", "Descripción de los datos",
             "Análisis exploratorio", "Procesamiento de datos", "Modelación", "Resolución del problema",
             "Conclusiones"]

# Cifras que viven en varios archivos y tienen que coincidir. Cada entrada: nombre,
# patrón de la cifra buena y patrones de variantes que delatan una copia vieja.
CIFRAS = [
    ("libros del catálogo medido", r"53\.179", [r"61\.642 libros medidos", r"68\.546 libros medidos"]),
    ("capítulos medidos", r"585\.111", []),
    ("Spearman validación interna", r"0,908", []),   # «0,91» redondeado en el vídeo es legítimo
    ("modelo articulatorio TCN vs reglas", r"0,566", [r"0,57\b"]),
    ("palabras habladas del guion", r"\b(5[01][0-9]) palabras", []),
    ("enlace principal", r"pleyade-app\.vercel\.app", [r"literalevel-front\.static\.hf\.space"]),   # el Space estático solo vale como respaldo
    ("nombre de la app", r"Pléyade", []),
]
ARCHIVOS_CIFRAS = ["documento.md", "estrategia.md", "presentacion.tex", "guion_video_eos.md",
                   "guion_video.md", "guion_demo_en_vivo.md", "mensaje_profesor.md", "notebook_proyecto.py"]

FILAS: list[dict] = []


def fila(rubro: str, estado: str, prueba: str, evidencia: str) -> None:
    FILAS.append({"rubro": rubro, "estado": estado, "prueba": prueba, "evidencia": evidencia})


def _ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:  # noqa: BLE001
        return None


def _pdf(ruta: Path):
    """(páginas, texto) con pypdf; texto vacío si no se puede."""
    try:
        from pypdf import PdfReader
        r = PdfReader(str(ruta))
        return len(r.pages), "\n".join((p.extract_text() or "") for p in r.pages)
    except Exception as e:  # noqa: BLE001
        return 0, f"<sin texto: {type(e).__name__}>"


def _qr_en_imagen(img) -> str:
    try:
        import cv2
        texto, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        return texto or ""
    except Exception:  # noqa: BLE001
        return ""


# --- 0. Estado del repositorio y de lo publicado -------------------------------------

def git_y_publicado(sin_red: bool) -> None:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    sucios = [l for l in subprocess.run(["git", "status", "--short"], cwd=RAIZ, capture_output=True, text=True).stdout.splitlines()
              if not l.startswith("??")]
    fila("Repositorio", "OK" if not sucios else "AVISO", f"HEAD `{head}`",
         "árbol limpio" if not sucios else f"{len(sucios)} archivos con cambios sin commit: " + ", ".join(l[3:] for l in sucios[:6]))
    if sin_red:
        return
    try:
        html = urllib.request.urlopen(VERCEL + "/", timeout=30).read().decode("utf-8", "replace")
        m = re.search(r"main-([A-Za-z0-9_]{8})\.js", html)
        meta = re.search(r'name="literalevel-api"\s+content="([^"]*)"', html)
        clips = json.load(urllib.request.urlopen(VERCEL + "/eos/clips.json", timeout=30))
        fila("Interfaz", "OK", "front en Vercel",
             f"build `{m.group(1) if m else '?'}`, meta de la API «{meta.group(1) if meta else '?'}», {len(clips)} clips de Eos")
    except Exception as e:  # noqa: BLE001
        fila("Interfaz", "FALLO", "front en Vercel", f"{type(e).__name__}: {e}")
    try:
        d = json.load(urllib.request.urlopen(f"https://huggingface.co/api/spaces/{SPACE_REPO}", timeout=30))
        salud = json.load(urllib.request.urlopen(SPACE_API + "/api/salud", timeout=90))
        ok = salud.get("estado") == "ok" and d.get("runtime", {}).get("stage") == "RUNNING"
        fila("Interfaz", "OK" if ok else "FALLO", "API en el Space",
             f"revisión `{d.get('sha', '')[:7]}` ({d.get('lastModified', '')[:16]}), {d.get('runtime', {}).get('stage')}, "
             f"salud {salud.get('estado')}, buscador_listo {salud.get('buscador_listo')}")
    except Exception as e:  # noqa: BLE001
        fila("Interfaz", "FALLO", "API en el Space", f"{type(e).__name__}: {e}")


# --- 1. Documento y estrategia ------------------------------------------------------

def documento() -> None:
    tex, pdf = ENTREGA / "documento.tex", ENTREGA / "documento.pdf"
    if not tex.exists() or not pdf.exists():
        fila("Documento", "FALLO", "archivos", f"falta {'documento.tex' if not tex.exists() else 'documento.pdf'}")
        return
    secciones = re.findall(r"^\\section\*?\{([^}]*)\}", tex.read_text(encoding="utf-8", errors="replace"), re.M)
    posiciones = []
    for s in SECCIONES:
        idx = next((i for i, t in enumerate(secciones) if s.lower() in t.lower()), None)
        posiciones.append((s, idx))
        if idx is None:
            fila("Documento", "FALLO", "sección exigida", f"no encuentro «{s}» entre las \\section del .tex")
    orden = [i for _, i in posiciones if i is not None]
    fila("Documento", "OK" if orden == sorted(orden) else "FALLO", "orden de las secciones",
         "el orden de la rúbrica se respeta" if orden == sorted(orden) else "hay secciones fuera del orden de la rúbrica")
    paginas, texto = _pdf(pdf)
    huerfanas = len(re.findall(r"\[\?\]|\?\?", texto))
    fila("Documento", "OK" if huerfanas == 0 else "FALLO", "referencias resueltas en el PDF",
         f"{paginas} páginas; {huerfanas} marcas «??»/«[?]»")
    fila("Documento", "OK" if pdf.stat().st_mtime >= tex.stat().st_mtime else "FALLO", "PDF más nuevo que el .tex",
         f"tex {time.strftime('%d %b %H:%M', time.localtime(tex.stat().st_mtime))}, pdf {time.strftime('%d %b %H:%M', time.localtime(pdf.stat().st_mtime))}")
    for palabra, por_que in (("Kaggle", "la rúbrica lo prohíbe: hay que decir que no se usó"),
                             ("Angular", "el profesor pidió Angular; el documento debe decirlo"),
                             ("APA", "referencias en APA")):
        fila("Documento", "OK" if palabra.lower() in texto.lower() else "AVISO", f"menciona «{palabra}»", por_que)
    bib = ENTREGA / "referencias.bib"
    fila("Documento", "OK" if bib.exists() else "AVISO", "referencias.bib", f"{len(re.findall(r'^@', bib.read_text(encoding='utf-8', errors='replace'), re.M)) if bib.exists() else 0} entradas")


def estrategia() -> None:
    md = ENTREGA / "estrategia.md"
    if not md.exists():
        fila("Estrategia", "FALLO", "archivo", "falta estrategia.md")
        return
    t = md.read_text(encoding="utf-8", errors="replace").lower()
    for clave, nombre in (("accionable", "accionables concretos"), ("usuario", "descripción de usuarios"),
                          ("usabilidad", "usabilidad del modelo"), ("esmeralda", "ciclo con una lectora real")):
        n = t.count(clave)
        fila("Estrategia", "OK" if n else "FALLO", nombre, f"«{clave}» aparece {n} veces")
    pdf = ENTREGA / "estrategia.pdf"
    if pdf.exists():
        fila("Estrategia", "OK" if pdf.stat().st_mtime >= md.stat().st_mtime else "AVISO", "PDF al día", f"{_pdf(pdf)[0]} páginas")


# --- 2. Notebook ----------------------------------------------------------------------

def notebook() -> None:
    nb, py = ENTREGA / "notebook_proyecto.ipynb", ENTREGA / "notebook_proyecto.py"
    if not nb.exists():
        fila("Notebook", "FALLO", "archivo", "falta notebook_proyecto.ipynb")
        return
    d = json.load(open(nb, encoding="utf-8"))
    celdas = d.get("cells", [])
    codigo = [c for c in celdas if c.get("cell_type") == "code"]
    errores = sum(1 for c in codigo for o in c.get("outputs", []) if o.get("output_type") == "error")
    stderr = sum(1 for c in codigo for o in c.get("outputs", []) if o.get("name") == "stderr")
    sin_salida = sum(1 for c in codigo if not c.get("outputs"))
    fila("Notebook", "OK" if not errores and not stderr else "FALLO", "salidas guardadas",
         f"{len(celdas)} celdas, {len(codigo)} de código, {errores} errores, {stderr} stderr, {sin_salida} sin salida")
    if py.exists():
        fila("Notebook", "OK" if nb.stat().st_mtime >= py.stat().st_mtime else "AVISO", ".ipynb más nuevo que el .py",
             "se regenera con tools/a_notebook.py (edita el .py, no el .ipynb)")
    fila("Notebook", "AVISO", "ejecución en Colab limpio", "no la hace este guion: hay que repetirla a mano (SKILL §3)")


# --- 3. Presentación -----------------------------------------------------------------

def presentacion() -> None:
    pdf = ENTREGA / "presentacion.pdf"
    if not pdf.exists():
        fila("Presentación", "FALLO", "archivo", "falta presentacion.pdf")
        return
    paginas, texto = _pdf(pdf)
    fila("Presentación", "OK", "diapositivas", f"{paginas} diapositivas")
    qr = ""
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        import numpy as np
        import cv2
        doc = fitz.open(str(pdf))
        pix = doc[-1].get_pixmap(dpi=150)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        if pix.n == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        qr = _qr_en_imagen(img)
    except Exception as e:  # noqa: BLE001
        qr = f"<no leído: {type(e).__name__}>"
    fila("Presentación", "OK" if "vercel.app" in qr else "AVISO", "QR de la última diapositiva", f"decodifica a «{qr}»" if qr else "sin QR legible")
    fila("Presentación", "OK" if "vercel" in texto.lower() else "AVISO", "enlace de Vercel en texto", "búsqueda en el texto del PDF")


# --- 4. Vídeo y guion ----------------------------------------------------------------

def video() -> None:
    ff = _ffmpeg()
    mp4s = sorted(ENTREGA.glob("*.mp4"))
    if not mp4s:
        fila("Vídeo", "FALLO", "archivo", "no hay ningún .mp4 en entrega/")
        return
    for v in mp4s:
        if not ff:
            fila("Vídeo", "AVISO", v.name, "sin ffmpeg para medir")
            continue
        r = subprocess.run([ff, "-i", str(v)], capture_output=True, text=True)
        dur = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        seg = (int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3))) if dur else 0.0
        vid = re.search(r"Video: (\w+).*?(\d{3,5})x(\d{3,5})", r.stderr)
        aud = re.search(r"Audio: (\w+)", r.stderr)
        deco = subprocess.run([ff, "-v", "error", "-i", str(v), "-f", "null", "-"], capture_output=True, text=True)
        bien = seg and seg <= TOPE_VIDEO_S and deco.returncode == 0 and not deco.stderr.strip()
        # QR del último fotograma
        qr = ""
        try:
            import cv2
            tmp = Path(os.environ.get("TEMP", "/tmp")) / "auditar_ultimo.png"
            subprocess.run([ff, "-y", "-loglevel", "error", "-sseof", "-1", "-i", str(v), "-frames:v", "1", str(tmp)], check=True)
            qr = _qr_en_imagen(cv2.imread(str(tmp)))
        except Exception:  # noqa: BLE001
            pass
        fila("Vídeo", "OK" if bien else "FALLO", v.name,
             f"{seg / 60:.0f}:{seg % 60:04.1f} min ({'≤' if seg <= TOPE_VIDEO_S else '>'} 5:00), {vid.group(1) if vid else '?'} "
             f"{vid.group(2) + 'x' + vid.group(3) if vid else ''}, audio {aud.group(1) if aud else '?'}, {v.stat().st_size / 1e6:.1f} MB, "
             f"decodifica {'entero' if deco.returncode == 0 and not deco.stderr.strip() else 'CON ERRORES'}, QR final «{qr or '—'}»")
    contar = RAIZ / "tools" / "contar_guion.py"
    for g in ("guion_video_eos.md", "guion_video.md"):
        if contar.exists() and (ENTREGA / g).exists():
            r = subprocess.run([sys.executable, "-X", "utf8", str(contar), str(ENTREGA / g)], capture_output=True, text=True)
            lineas = [l for l in r.stdout.splitlines() if re.search(r"HABLADAS:\s*\d+", l, re.I)] or [l for l in r.stdout.splitlines() if re.search(r"\d+ palabras", l)][-1:] or [r.stderr.strip()[:120]]
            fila("Vídeo", "OK" if r.returncode == 0 else "AVISO", f"palabras habladas de {g}", lineas[0][:160])


# --- 5. Demo y entrega ----------------------------------------------------------------

def demo_y_entrega() -> None:
    g = ENTREGA / "guion_demo_en_vivo.md"
    if g.exists():
        t = g.read_text(encoding="utf-8", errors="replace")
        fila("Demo en vivo", "OK" if "10 de octubre" in t or "10 oct" in t else "AVISO", "fecha de la demo en el guion",
             "10 oct 2026, turno 5 (Classroom, leído el 26 sep)")
        fila("Demo en vivo", "OK" if "vercel" in t.lower() else "FALLO", "enlace de Vercel en el guion", "la demo se hace sobre pleyade-app.vercel.app")
    else:
        fila("Demo en vivo", "FALLO", "guion", "falta guion_demo_en_vivo.md")
    m = ENTREGA / "mensaje_profesor.md"
    if m.exists():
        t = m.read_text(encoding="utf-8", errors="replace")
        fila("Entrega", "OK" if "vercel" in t.lower() and "Pléyade" in t else "AVISO", "mensaje al profesor",
             f"Vercel {'sí' if 'vercel' in t.lower() else 'NO'}, Pléyade {'sí' if 'Pléyade' in t else 'NO'}; sin contraseñas: {'sí' if 'contraseña' not in t.lower() or 'aparte' in t.lower() else 'REVISAR'}")
    for nombre in ("documento.pdf", "estrategia.pdf", "notebook_proyecto.ipynb", "presentacion.pdf"):
        fila("Entrega", "OK" if (ENTREGA / nombre).exists() else "FALLO", nombre, "archivo del paquete")
    fila("Entrega", "AVISO", "plazo", "archivos antes del 4 oct 2026, 11:59 p.m.; demo 10 oct, turno 5 (confirmar en Classroom)")


# --- 6. Cifras repetidas ---------------------------------------------------------------

def cifras() -> None:
    textos = {a: (ENTREGA / a).read_text(encoding="utf-8", errors="replace") for a in ARCHIVOS_CIFRAS if (ENTREGA / a).exists()}
    for nombre, buena, viejas in CIFRAS:
        donde = [a for a, t in textos.items() if re.search(buena, t)]
        malas = [(a, v) for a, t in textos.items() for v in viejas if re.search(v, t)]
        # Una variante vieja es AVISO, no FALLO: puede estar citada como respaldo o como
        # historia fechada. Quien audita lee el párrafo y decide.
        estado = "AVISO" if malas else ("OK" if donde else "AVISO")
        fila("Cifras", estado, nombre, f"en {len(donde)} archivos" + (f"; variante vieja en {', '.join(a for a, _ in malas)}: leer el párrafo" if malas else ""))
    # la cuenta de palabras del guion tiene que ser una sola
    cuentas = set()
    for t in textos.values():
        cuentas |= set(re.findall(r"\b(5[01][0-9]) palabras", t))
    if len(cuentas) > 1:
        fila("Cifras", "FALLO", "palabras habladas del guion", f"se citan varias cuentas: {sorted(cuentas)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sin-red", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    git_y_publicado(a.sin_red)
    documento()
    estrategia()
    notebook()
    presentacion()
    video()
    demo_y_entrega()
    cifras()
    print(f"# Comprobación mecánica de la entrega — {time.strftime('%d %b %Y %H:%M')}\n")
    print("| Rubro | Estado | Prueba | Evidencia |\n|---|---|---|---|")
    for f in FILAS:
        print(f"| {f['rubro']} | {f['estado']} | {f['prueba']} | {f['evidencia'].replace('|', '/')} |")
    n = {e: sum(1 for f in FILAS if f["estado"] == e) for e in ("OK", "AVISO", "FALLO")}
    print(f"\n**{n['OK']} OK · {n['AVISO']} avisos · {n['FALLO']} fallos.** Lo que este guion no mide está en la SKILL.md.")
    if a.json:
        json.dump(FILAS, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
