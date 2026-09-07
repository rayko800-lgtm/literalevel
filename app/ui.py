"""Interfaz de LiteraLevel en Gradio: une los seis puntos en una sola app.

Cada pestana corresponde a un punto de la especificacion:

  1. Mi nivel      -> perfil.desde_cuestionario / desde_muestra
  2. Buscar        -> catalogo.buscar / por_nivel
  3. Leer          -> reader.cargar + scoring.Puntuador + lexicon.ConsultorLexico
  5. Pronunciacion -> voz.practicar / puntos_debiles
  6. Estado        -> diagnostico para la demo (claves, modelo, datos)

El punto 4 (diccionario, IPA y audio) vive dentro de la pestana de lectura, no
en una aparte: la especificacion pide consultar la palabra *mientras se lee*,
asi que la oracion de contexto se saca sola del capitulo abierto.

Arranque perezoso deliberado. Los tres recursos pesados -el modelo v4 (328 MB),
los embeddings del catalogo y el diccionario Kaikki (243 MB) con spaCy y
MiniLM- se cargan la primera vez que se usan, no al abrir la app. Asi la
interfaz aparece en el acto y una demo del buscador no paga el precio del
modelo de puntuacion.

Ningun manejador levanta excepciones hacia Gradio: lo que falla se devuelve
como texto legible en la propia interfaz.

Uso:  python -X utf8 app/ui.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
# Los modulos se importan planos entre si ("import config"), asi que app/ tiene
# que estar en sys.path aunque a ui.py se le llame desde la raiz del proyecto.
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import gradio as gr

import config
import perfil as perfil_mod
import reader
import scoring
import voz
from catalogo import Catalogo
from lexicon import ConsultorLexico

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO", str(RAIZ / "modelo_v4"))
NIVEL_POR_DEFECTO = 1.0   # se usa en la consulta lexica si aun no hay perfil


# --- Recursos pesados: uno por proceso, cargado al primer uso -------------

_puntuador = None
_catalogo = None
_consultor = None


def puntuador() -> scoring.Puntuador:
    global _puntuador
    if _puntuador is None:
        _puntuador = scoring.Puntuador(RUTA_MODELO)
    return _puntuador


def catalogo() -> Catalogo:
    global _catalogo
    if _catalogo is None:
        _catalogo = Catalogo()
    return _catalogo


def consultor() -> ConsultorLexico:
    global _consultor
    if _consultor is None:
        _consultor = ConsultorLexico()
    return _consultor


def _aviso(e) -> str:
    """Un fallo contado en cristiano, nunca un traceback en la cara."""
    return f"[!] {e}"


# --- Punto 1: nivel del lector -------------------------------------------

def _describir(p) -> str:
    if p is None:
        return ("Todavía no has fijado tu nivel. Responde el cuestionario "
                "o pega un texto que leas cómodo.")
    return perfil_mod.describir(p)


def _desde_cuestionario(p_actual, nombre, *valores):
    claves = [c for c, _, _ in perfil_mod.PREGUNTAS]
    respuestas = {k: v for k, v in zip(claves, valores) if v is not None}
    try:
        p = perfil_mod.desde_cuestionario(respuestas, nombre=nombre or "")
        p.guardar()
    except (ValueError, OSError) as e:
        # Se conserva el perfil anterior: un fallo al estimar no debe borrarlo.
        return p_actual, _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


def _desde_muestra(p_actual, nombre, texto):
    if not (texto or "").strip():
        return p_actual, "Pega un fragmento que leas sin dificultad."
    try:
        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or "")
        p.guardar()
    except (ValueError, FileNotFoundError, OSError) as e:
        return p_actual, _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


# --- Punto 2: buscador del catalogo --------------------------------------

def _tabla_libros(libros, aviso: str = "") -> str:
    if not libros:
        return _aviso(aviso or "Sin resultados.")
    filas = ["| Libro | Autor | Nivel | De qué va |", "|---|---|---|---|"]
    for b in libros:
        enlace = f"[{b.titulo}]({b.url_gutenberg})" if b.url_gutenberg else b.titulo
        gancho = (b.gancho or "").replace("\n", " ").replace("|", "/")
        if len(gancho) > 110:
            gancho = gancho[:107] + "..."
        filas.append(f"| {enlace} | {b.autor} | {b.nivel} | {gancho} |")
    if aviso:
        filas.append("")
        filas.append(f"_{aviso}_")
    return "\n".join(filas)


def _buscar(p, consulta, ajustar, n):
    try:
        cat = catalogo()
    except (FileNotFoundError, OSError) as e:
        return _aviso(e)
    nivel = p.nivel if (ajustar and p is not None) else None
    try:
        libros, aviso = cat.buscar(consulta, nivel_lector=nivel, n=int(n))
    except Exception as e:                      # red o modelo de embeddings
        return _aviso(e)
    cabecera = ""
    if ajustar and p is None:
        cabecera = "_Sin perfil todavía: busco solo por parecido._\n\n"
    return cabecera + _tabla_libros(libros, aviso)


def _recomendar(p, n):
    if p is None:
        return "Primero fija tu nivel en la pestaña **Mi nivel**."
    try:
        libros = catalogo().por_nivel(p.nivel, n=int(n))
    except Exception as e:
        return _aviso(e)
    lo, hi = p.rango_recomendado
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros))


# --- Punto 3: lector, y punto 4 dentro de el ------------------------------

def _abrir(archivo):
    vacio = gr.update(choices=[], value=None)
    if not archivo:
        return None, vacio, "", "Sube un `.epub`, `.pdf` o `.txt`."
    try:
        libro = reader.cargar(archivo)
    except (ValueError, OSError, KeyError) as e:
        return None, vacio, "", _aviso(e)
    if not libro.capitulos:
        return None, vacio, "", _aviso("El archivo no tiene texto legible.")
    opciones = [(f"{i + 1}. {c.titulo}", i) for i, c in enumerate(libro.capitulos)]
    resumen = (f"**{libro.titulo}** — {libro.autor or 'autor desconocido'} · "
               f"{len(libro.capitulos)} capítulos · {libro.palabras:,} palabras")
    return libro, gr.update(choices=opciones, value=0), "", resumen


def _capitulo(libro, idx):
    if libro is None or idx is None:
        return "", ""
    c = libro.capitulos[int(idx)]
    return c.texto, f"**{c.titulo}** · {c.palabras:,} palabras"


def _medir(libro, idx):
    if libro is None or idx is None:
        return "Abre un libro y elige un capítulo."
    c = libro.capitulos[int(idx)]
    try:
        r = puntuador().puntuar(c.texto)
    except (ValueError, FileNotFoundError) as e:
        return _aviso(e)
    return (f"**{r.puntuacion:.2f} / 2.00** ({r.banda}) · orientativo "
            f"**{r.nivel_orientativo}** · {r.n_bloques} bloques · "
            f"confianza {r.confianza}")


def _oracion_de(texto: str, palabra: str) -> str:
    """Primera oracion del capitulo que contiene la palabra."""
    if not texto or not palabra:
        return ""
    patron = re.compile(rf"\b{re.escape(palabra.strip())}\b", re.IGNORECASE)
    for frase in scoring.SENT_RE.findall(texto):
        if patron.search(frase):
            return " ".join(frase.split())
    return ""


def _ficha(r) -> str:
    """La consulta lexica en markdown, diciendo de donde sale cada cosa."""
    cab = f"## {r.palabra_superficie}"
    if r.lema_buscado and r.lema_buscado.lower() != r.palabra_superficie.lower():
        cab += f"  ·  _{r.lema_buscado}_"
    if r.categoria:
        cab += f"  ·  {r.categoria}"
    L = [cab]

    fon = []
    if r.ipa_uk:
        fon.append(f"UK {r.ipa_uk}")
    if r.ipa_us:
        fon.append(f"US {r.ipa_us}")
    if fon:
        L.append("**Pronunciación:** " + "  ·  ".join(fon))

    if r.sentido:
        L.append(f"**Diccionario** (Wiktionary): {r.sentido}")
        if r.etiquetas_sentido:
            L.append(f"_{', '.join(r.etiquetas_sentido)}_")
        if r.n_sentidos_candidatos > 1:
            sim = f", afinidad {r.similitud:.2f}" if r.similitud is not None else ""
            L.append(f"_Elegido entre {r.n_sentidos_candidatos} acepciones{sim}._")
    else:
        L.append("_No hay entrada de diccionario para esta palabra._")

    if r.definicion_contextual:
        L.append(f"**Aquí significa:** {r.definicion_contextual}")
    if r.explicacion_gramatical:
        L.append(f"**Gramática:** {r.explicacion_gramatical}")
    if r.explicacion_adaptada:
        L.append(f"**Para tu nivel ({r.banda_lector}):** {r.explicacion_adaptada}")
    if r.ejemplo_simplificado:
        L.append(f"**Ejemplo:** _{r.ejemplo_simplificado}_")

    pie = []
    if r.frecuencia_zipf is not None:
        rareza = ("muy común" if r.frecuencia_zipf >= 5 else
                  "frecuente" if r.frecuencia_zipf >= 4 else
                  "poco frecuente" if r.frecuencia_zipf >= 3 else "rara")
        pie.append(f"{rareza} (zipf {r.frecuencia_zipf:.1f})")
    if r.desde_cache:
        pie.append("desde caché")
    if r.audio_generado:
        pie.append("audio generado con tts-1")
    if pie:
        L.append("_" + " · ".join(pie) + "_")
    for a in r.avisos:
        L.append(f"[!] {a}")
    return "\n\n".join(L)


def _reproductores(r) -> str:
    """Audio remoto de Wiktionary. Los locales van al componente gr.Audio."""
    trozos = []
    for etiqueta, url in (("UK", r.audio_uk), ("US", r.audio_us)):
        if url and str(url).startswith("http"):
            trozos.append(
                f'<p style="margin:.2rem 0"><b>{etiqueta}</b><br>'
                f'<audio controls preload="none" src="{url}"></audio></p>')
    return "".join(trozos)


def _local(url):
    """Ruta reproducible por gr.Audio, o None si el audio es remoto."""
    if url and not str(url).startswith("http") and os.path.exists(str(url)):
        return str(url)
    return None


def _consultar(p, libro, idx, palabra, oracion_manual):
    palabra = (palabra or "").strip()
    if not palabra:
        return "Escribe la palabra que quieres consultar.", "", None
    if len(palabra.split()) > 4:
        return "Consulta una palabra (o un phrasal verb corto), no una frase.", "", None

    oracion = (oracion_manual or "").strip()
    origen = "de la oración que escribiste"
    if not oracion and libro is not None and idx is not None:
        oracion = _oracion_de(libro.capitulos[int(idx)].texto, palabra)
        origen = "localizada en el capítulo"
    if not oracion:
        oracion = palabra
        origen = "sin contexto: la desambiguación será peor"

    nivel = p.nivel if p is not None else NIVEL_POR_DEFECTO
    try:
        r = consultor().consultar(palabra, oracion, nivel)
    except (FileNotFoundError, OSError) as e:
        return _aviso(e), "", None
    ficha = _ficha(r) + f"\n\n> {oracion}\n\n_Contexto: {origen}._"
    return ficha, _reproductores(r), _local(r.audio_us) or _local(r.audio_uk)


def _frase_del_capitulo(libro, idx):
    """Manda la primera oracion de largo razonable a la practica de voz."""
    if libro is None or idx is None:
        return ""
    for frase in scoring.SENT_RE.findall(libro.capitulos[int(idx)].texto):
        limpia = " ".join(frase.split())
        if 6 <= len(limpia.split()) <= 25:
            return limpia
    return ""


# --- Punto 5: pronunciacion ----------------------------------------------

def _practicar(ruta_audio, frase):
    if not (frase or "").strip():
        return "Escribe la frase que vas a leer en voz alta.", None
    if not ruta_audio:
        return "Graba tu voz con el micrófono (o sube un audio).", None
    try:
        s = voz.practicar(ruta_audio, frase)
    except Exception as e:
        return _aviso(e), None

    ev = s.evaluacion
    L = [f"## {ev.puntuacion:.0f} / 100"]
    if not s.transcripcion_ok:
        L.append("[!] No se pudo transcribir (sin `OPENAI_API_KEY` o sin red). "
                 "La puntuación de arriba no es válida.")
    else:
        L.append(f"**Se te entendió:** _{ev.transcripcion or '(nada)'}_")
        if ev.palabras_falladas:
            L.append("**Falló:** " + ", ".join(f"`{w}`" for w in ev.palabras_falladas))
        else:
            L.append("Ni una palabra fallada. Sube el listón con una frase más larga.")

    if s.correccion:
        L.append(f"**Cómo corregirlo:** {s.correccion.resumen}")
        for d in s.correccion.detalles:
            L.append(f"- **{d.palabra}** — {d.sonido_que_falla}. "
                     f"{d.como_colocar_la_boca}")
    return "\n\n".join(L), s.audio_correcto


def _debiles():
    try:
        filas = voz.puntos_debiles(n=15)
    except Exception as e:
        return _aviso(e)
    if not filas:
        return "Aún no hay palabras registradas. Practica una frase primero."
    return ("Tus palabras más falladas:\n\n"
            + "\n".join(f"{i + 1}. **{w}** — {n} vez{'es' if n > 1 else ''}"
                        for i, (w, n) in enumerate(filas)))


# --- Punto 6: diagnostico para la demo -----------------------------------

def _diagnostico():
    L = ["### Claves", "```", config.estado(), "```"]
    if config.falta():
        L.append("Sin `OPENAI_API_KEY` la app sigue funcionando: diccionario, "
                 "IPA, audio de Wiktionary, buscador y puntuación no usan red. "
                 "Lo que se apaga es la explicación contextual y la voz.")

    L.append("### Recursos")
    modelo_ok = os.path.isdir(RUTA_MODELO)
    L.append(f"- Modelo v4: {'encontrado' if modelo_ok else 'FALTA'} — `{RUTA_MODELO}`")
    from lexicon import RUTA_DICCIONARIO
    dic = Path(RUTA_DICCIONARIO)
    tam = f"{dic.stat().st_size / 1e6:.0f} MB" if dic.exists() else "FALTA"
    L.append(f"- Diccionario Kaikki: {tam}")
    try:
        L.append(f"- Catálogo: {catalogo().resumen()}")
    except Exception as e:
        L.append(f"- Catálogo: {e}")

    L.append("### Cargado en memoria")
    L.append(f"- Puntuador: {'sí' if _puntuador else 'no (se carga al usarlo)'}")
    L.append(f"- Catálogo: {'sí' if _catalogo else 'no'}")
    L.append(f"- Consultor léxico: {'sí' if _consultor else 'no'}")
    return "\n".join(L)


# --- Montaje --------------------------------------------------------------

def construir() -> gr.Blocks:
    with gr.Blocks(title="LiteraLevel") as demo:
        gr.Markdown("# LiteraLevel\nLee en inglés al nivel que te toca.")
        est_perfil = gr.State(perfil_mod.cargar())
        est_libro = gr.State(None)

        with gr.Tab("Mi nivel"):
            perfil_md = gr.Markdown(_describir(perfil_mod.cargar()))
            nombre = gr.Textbox(label="Tu nombre (opcional)")
            with gr.Accordion("Cuestionario rápido", open=True):
                radios = [
                    gr.Radio(choices=[(t, v) for t, v in opciones], label=pregunta)
                    for _, pregunta, opciones in perfil_mod.PREGUNTAS
                ]
                b_cuest = gr.Button("Estimar mi nivel", variant="primary")
            with gr.Accordion("O mídelo con un texto que leas cómodo", open=False):
                muestra = gr.Textbox(lines=8, label="Pega aquí unas 200 palabras "
                                                   "en inglés que leas sin esfuerzo")
                b_muestra = gr.Button("Medir con este texto")
                gr.Markdown("_La primera vez tarda: carga el modelo v4 (328 MB)._")

            b_cuest.click(_desde_cuestionario, [est_perfil, nombre] + radios,
                          [est_perfil, perfil_md])
            b_muestra.click(_desde_muestra, [est_perfil, nombre, muestra],
                            [est_perfil, perfil_md])

        with gr.Tab("Buscar lectura"):
            with gr.Row():
                consulta = gr.Textbox(label="¿Qué te apetece leer?", scale=4,
                                      placeholder="una novela de detectives victoriana")
                n_res = gr.Number(value=10, label="Resultados", precision=0,
                                  minimum=1, maximum=50, scale=1)
            ajustar = gr.Checkbox(value=True, label="Ajustar a mi nivel")
            with gr.Row():
                b_buscar = gr.Button("Buscar", variant="primary")
                b_recom = gr.Button("Recomiéndame por nivel")
            resultados = gr.Markdown()
            gr.Markdown("_La primera búsqueda indexa el catálogo; luego va sola._")

            b_buscar.click(_buscar, [est_perfil, consulta, ajustar, n_res], resultados)
            consulta.submit(_buscar, [est_perfil, consulta, ajustar, n_res], resultados)
            b_recom.click(_recomendar, [est_perfil, n_res], resultados)

        with gr.Tab("Leer"):
            with gr.Row():
                archivo = gr.File(label="Tu libro (.epub, .pdf, .txt)",
                                  file_types=[".epub", ".pdf", ".txt"],
                                  type="filepath", scale=2)
                libro_md = gr.Markdown()
            with gr.Row():
                cap = gr.Dropdown(label="Capítulo", choices=[], scale=4)
                b_medir = gr.Button("Medir dificultad", scale=1)
            cap_md = gr.Markdown()
            texto = gr.Textbox(lines=20, max_lines=20, label="Texto")

            gr.Markdown("### Consultar una palabra\n"
                        "Escríbela como aparece en el texto: la oración de "
                        "contexto se busca sola en el capítulo abierto.")
            with gr.Row():
                palabra = gr.Textbox(label="Palabra", scale=2)
                oracion = gr.Textbox(label="Oración (opcional, si quieres forzarla)",
                                     scale=4)
                b_palabra = gr.Button("Consultar", variant="primary", scale=1)
            ficha = gr.Markdown()
            audio_web = gr.HTML()
            audio_local = gr.Audio(label="Pronunciación generada", type="filepath")

            archivo.change(_abrir, archivo, [est_libro, cap, texto, libro_md])
            cap.change(_capitulo, [est_libro, cap], [texto, cap_md])
            b_medir.click(_medir, [est_libro, cap], cap_md)
            b_palabra.click(_consultar,
                            [est_perfil, est_libro, cap, palabra, oracion],
                            [ficha, audio_web, audio_local])
            palabra.submit(_consultar,
                           [est_perfil, est_libro, cap, palabra, oracion],
                           [ficha, audio_web, audio_local])

        with gr.Tab("Pronunciación"):
            frase = gr.Textbox(label="Frase que vas a leer en voz alta",
                               placeholder="It is a truth universally acknowledged...")
            b_traer = gr.Button("Traer una frase del capítulo que estoy leyendo")
            mi_audio = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                label="Léela en voz alta")
            with gr.Row():
                b_practicar = gr.Button("Corrígeme", variant="primary")
                b_debiles = gr.Button("Mis puntos débiles")
            veredicto = gr.Markdown()
            audio_ref = gr.Audio(label="Cómo debería sonar", type="filepath")

            b_traer.click(_frase_del_capitulo, [est_libro, cap], frase)
            b_practicar.click(_practicar, [mi_audio, frase], [veredicto, audio_ref])
            b_debiles.click(_debiles, None, veredicto)

        with gr.Tab("Estado"):
            diag = gr.Markdown()
            gr.Button("Comprobar").click(_diagnostico, None, diag)
            demo.load(_diagnostico, None, diag)

    return demo


if __name__ == "__main__":
    construir().launch(theme=gr.themes.Soft(), inbrowser=True)
