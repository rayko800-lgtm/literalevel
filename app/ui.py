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

import html as _html
import json
import math
import os
import re
import sys
import threading
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
# Los modulos se importan planos entre si ("import config"), asi que app/ tiene
# que estar en sys.path aunque a ui.py se le llame desde la raiz del proyecto.
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

import gradio as gr

import articulacion
import biblioteca
import config
import cuaderno
import cuentas
import ficha as ficha
import fonemas
import paletas as paletas_mod
import perfil as perfil_mod
import reader
import scoring
import voz
from catalogo import Catalogo
from lexicon import ConsultorLexico

RUTA_MODELO = os.environ.get("LITERALEVEL_MODELO", str(RAIZ / "modelo_v4"))
NIVEL_POR_DEFECTO = 1.0   # se usa en la consulta lexica si aun no hay perfil

# Topes de entrada, aplicados en el servidor. Existen por dinero, no por
# estetica: la oracion y la frase acaban en llamadas de pago a OpenAI, y sin
# tope un visitante puede pegar cien mil caracteres y repetir.
LIMITE_ORACION = 400
LIMITE_FRASE_VOZ = 300
# La palabra tambien necesita tope, y no solo por dinero. Se validaba que no
# fueran mas de cuatro *palabras*, pero no su longitud: una sola "palabra" de
# miles de caracteres pasaba el filtro y salia como encabezado de la ficha,
# llenando la pantalla entera de letras. Ninguna palabra inglesa llega a 40;
# la mas larga de un diccionario normal ronda las 30.
LIMITE_PALABRA = 40
TAMANO_MAXIMO_SUBIDA = "20mb"   # un epub es un zip: sin tope, cabe una bomba

# Gradio solo sirve archivos del directorio de trabajo o del temporal del
# sistema. `lexicon.py` y `voz.py` guardan los audios de tts-1 en
# ~/.literalevel/audio, asi que sin declararla aqui la pronunciacion generada
# muere con InvalidPathError y no llega nunca al navegador.
#
# **Solo la subcarpeta de audio, nunca `~/.literalevel` entera.** Todo lo que
# cae bajo un allowed_path se sirve por GET /gradio_api/file=<ruta>, sin
# autenticacion cuando el Space es publico. Apuntar al directorio padre
# regalaba `cuaderno.db`, `voz.db`, `perfil.json` y `sesion.json` a cualquiera
# que escribiera la ruta, y los nombres estan en este mismo repositorio.
#
# Y la carpeta de los fonemas, que es otra cosa: mp3 pregrabados que viven en
# el repositorio (`fonemas.DIR_AUDIO`), no datos del lector. Solo hay audio.
# Los SVG animados del corte de la boca (`animacion_articulatoria`) se escriben
# aqui la primera vez que se piden. Generarlos cuesta milisegundos (85 en 0,11 s),
# pero en linea serian 800 KB dentro de la pestaña del IPA; como archivo, un
# <img loading="lazy"> dentro de un <details> no se descarga hasta abrirlo, y
# ningun saneador puede quitarles el <style> que los anima.
DIR_SVG_ARTICULACION = config.dir_datos() / "articulacion_svg"
RUTAS_PERMITIDAS = [str(config.dir_datos() / "audio"), str(fonemas.DIR_AUDIO),
                    str(articulacion.DIR_AUDIO_RP), str(DIR_SVG_ARTICULACION)]


# --- La tabla del AFI: cada simbolo suena al tocarlo ------------------------
# Miguel (13 sep): «un apartado con el International Phonetic Alphabet, que
# puedan picarle y escuchar; esos sonidos van a estar generados, no generan
# cobro», y una ficha «supertecnica» de articulacion, en americano y britanico.
#
# Todo en el navegador: la tabla se pinta UNA vez al construir la interfaz, y
# tocar un simbolo solo cambia el `src` de un <audio> -un mp3 del repositorio-,
# sin pasar por el servidor de Gradio ni por ninguna API. Cambiar de acento es
# mostrar u ocultar un bloque. Por eso no hay manejadores de Python que cablear.

def _src_audio(ruta: Path) -> str:
    """URL de un mp3 servido por `gradio_api/file=`, con `?v=` de tamaño y
    fecha: los mp3 se regeneran con el MISMO nombre, y sin eso el navegador
    seguia sirviendo el audio viejo de su cache."""
    from urllib.parse import quote
    try:
        st = ruta.stat()
        version = f"?v={st.st_size}-{int(st.st_mtime)}"
    except OSError:
        version = ""
    return "gradio_api/file=" + quote(ruta.as_posix(), safe="/:") + version


def _svg_en_disco(nombre: str, svg: str | None) -> str | None:
    """Escribe el SVG en `DIR_SVG_ARTICULACION` si falta o ha cambiado, y
    devuelve su URL para un <img>. `None` si no hay SVG o no se puede escribir."""
    if not svg:
        return None
    import os
    import threading
    ruta = DIR_SVG_ARTICULACION / nombre
    try:
        datos = svg.encode("utf-8")
        if not (ruta.is_file() and ruta.read_bytes() == datos):
            ruta.parent.mkdir(parents=True, exist_ok=True)
            temporal = ruta.with_name(f".{ruta.name}.{os.getpid()}.{threading.get_ident()}.tmp")
            temporal.write_bytes(datos)
            os.replace(temporal, ruta)
    except OSError:
        return None
    return _src_audio(ruta)


def _svg_sonido_src(simbolo: str, acento: str = "ga") -> str | None:
    """El corte de la boca animado de un sonido de la tabla, o `None`."""
    try:
        import animacion_articulatoria
        svg = animacion_articulatoria.svg_articulacion(simbolo, acento)
    except Exception:
        return None
    nombre = f"{acento}_" + "_".join(f"{ord(c):04x}" for c in simbolo) + ".svg"
    return _svg_en_disco(nombre, svg)


def _svg_palabra_src(ipa: str | None, acento: str = "ga") -> str | None:
    """La palabra entera, sonido a sonido, a partir de su IPA, o `None`."""
    if not ipa:
        return None
    import hashlib
    try:
        import animacion_articulatoria
        svg = animacion_articulatoria.svg_palabra(ipa, acento)
    except Exception:
        return None
    huella = hashlib.sha256(f"{acento}\x1f{ipa}".encode("utf-8")).hexdigest()[:20]
    return _svg_en_disco(f"palabra_{huella}.svg", svg)


_CSS_AFI = """<style>
#ll-afi{color:var(--ll-texto)}
#ll-afi .ll-afi-acentos{display:flex;gap:.5rem;flex-wrap:wrap;margin:.2rem 0 .8rem}
#ll-afi .ll-afi-acento{min-height:44px;padding:.4rem 1rem;border-radius:999px;
  border:1px solid var(--ll-borde);background:var(--ll-panel);color:var(--ll-texto);cursor:pointer}
#ll-afi .ll-afi-acento[aria-pressed="true"]{border-color:var(--ll-acento);color:var(--ll-acento);font-weight:700}
#ll-afi .ll-afi-inv[hidden]{display:none !important}
#ll-afi h3{margin:1.1rem 0 .5rem;color:var(--ll-acento)}
#ll-afi .ll-afi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(9.5rem,1fr));gap:.6rem}
#ll-afi .ll-afi-s{border:1px solid var(--ll-borde);border-radius:14px;padding:.55rem .6rem;
  background:var(--ll-lector-fondo)}
#ll-afi .ll-afi-btn{display:block;width:100%;min-height:3.4rem;border-radius:10px;
  border:1px solid var(--ll-borde);background:var(--ll-panel);color:var(--ll-texto);cursor:pointer;
  font:600 1.7rem/1 "Charis SIL","Doulos SIL","Gentium Plus","Noto Sans","Segoe UI",serif}
#ll-afi .ll-afi-btn.sonando{border-color:var(--ll-acento);color:var(--ll-acento);
  box-shadow:0 0 0 2px var(--ll-acento) inset}
#ll-afi .ll-afi-ej{display:block;margin:.35rem 0 .15rem;font-weight:600}
#ll-afi .ll-afi-nombre{display:block;font-size:.86rem;line-height:1.3}
#ll-afi details{margin-top:.4rem}
#ll-afi summary{cursor:pointer;font-size:.9rem;color:var(--ll-acento);min-height:32px;display:flex;align-items:center}
#ll-afi dl{margin:.4rem 0 0;font-size:.88rem;line-height:1.35}
#ll-afi dt{font-weight:700;margin-top:.35rem}
#ll-afi dd{margin:0}
#ll-afi .ll-afi-anim{display:block;width:100%;max-width:15rem;height:auto;margin:.4rem auto .2rem}
</style>"""


def _tabla_afi_html() -> str:
    """La tabla entera, con los dos acentos; el britanico nace oculto."""
    esc = lambda t: _html.escape(str(t), quote=True)  # noqa: E731
    p = [_CSS_AFI, '<div id="ll-afi">',
         '<div class="ll-afi-acentos" role="group" aria-label="Acento">']
    for i, (clave, nombre) in enumerate(articulacion.ACENTOS.items()):
        p.append(f'<button type="button" class="ll-afi-acento" data-acento="{clave}" '
                 f'aria-pressed="{"true" if i == 0 else "false"}">{esc(nombre)}</button>')
    p.append('</div><audio id="ll-afi-audio" preload="none"></audio>')
    etiquetas = [("rasgos", "Qué sonido es"), ("labios", "Labios"), ("lengua", "Lengua"),
                 ("boca", "Apertura de la boca"), ("cuerdas", "Cuerdas vocales"),
                 ("aire", "Salida del aire"), ("ga", "En americano"), ("rp", "En británico"),
                 ("trampa", "La trampa para hispanohablantes")]
    for n, acento in enumerate(articulacion.ACENTOS):
        p.append(f'<div class="ll-afi-inv" data-acento="{acento}"{" hidden" if n else ""}>')
        sonidos = articulacion.inventario(acento)
        for grupo, titulo in articulacion.GRUPOS:
            del_grupo = [s for s in sonidos if s.grupo == grupo]
            if not del_grupo:
                continue
            p.append(f'<h3>{esc(titulo)}</h3><div class="ll-afi-grid">')
            for s in del_grupo:
                filas = "".join(f"<dt>{esc(et)}</dt><dd>{esc(getattr(s.ficha, campo))}</dd>"
                                for campo, et in etiquetas if getattr(s.ficha, campo))
                src_anim = _svg_sonido_src(s.simbolo, acento)
                animacion = (
                    f'<img class="ll-afi-anim" loading="lazy" width="240" height="274" '
                    f'src="{esc(src_anim)}" alt="{esc(f"Corte de la boca: cómo se articula /{s.simbolo}/")}">'
                    if src_anim else "")
                p.append(
                    '<div class="ll-afi-s">'
                    f'<button type="button" class="ll-afi-btn" data-src="{esc(_src_audio(s.ruta))}" '
                    f'aria-label="{esc(f"Escuchar /{s.simbolo}/, como en {s.ejemplos[0]}")}">'
                    f'/{esc(s.simbolo)}/</button>'
                    f'<span class="ll-afi-ej">{esc(s.ejemplos[0])}</span>'
                    f'<span class="ll-afi-nombre">{esc(s.nombre)}</span>'
                    f'<details><summary>Cómo se articula</summary>{animacion}<dl>{filas}</dl></details>'
                    '</div>')
            p.append('</div>')
        p.append('</div>')
    p.append('</div>')
    return "".join(p)


# Un solo manejador para toda la pagina (delegacion): Gradio no ejecuta los
# <script> de un gr.HTML, y la tabla puede volver a pintarse.
JS_AFI = r"""
() => {
  if (window.__llAfi) return;
  window.__llAfi = true;
  document.addEventListener('click', (ev) => {
    const acento = ev.target.closest('.ll-afi-acento');
    if (acento) {
      const raiz = acento.closest('#ll-afi');
      raiz.querySelectorAll('.ll-afi-inv').forEach(d => { d.hidden = d.dataset.acento !== acento.dataset.acento; });
      raiz.querySelectorAll('.ll-afi-acento').forEach(b => b.setAttribute('aria-pressed', String(b === acento)));
      return;
    }
    const boton = ev.target.closest('.ll-afi-btn');
    if (!boton) return;
    const raiz = boton.closest('#ll-afi');
    const audio = raiz.querySelector('#ll-afi-audio');
    raiz.querySelectorAll('.ll-afi-btn.sonando').forEach(b => b.classList.remove('sonando'));
    audio.pause();
    audio.src = boton.dataset.src;
    boton.classList.add('sonando');
    audio.onended = () => boton.classList.remove('sonando');
    const promesa = audio.play();
    if (promesa && promesa.catch) promesa.catch(() => boton.classList.remove('sonando'));
  });
}
"""

# La voz del navegador para las palabras sin audio (ver `_reproductores`).
JS_VOZ_NAVEGADOR = r"""
() => {
  if (window.__llVozNav) return;
  window.__llVozNav = true;
  document.addEventListener('click', (ev) => {
    const b = ev.target.closest('.ll-voz-navegador');
    if (!b || !('speechSynthesis' in window)) return;
    const u = new SpeechSynthesisUtterance(b.dataset.texto || '');
    u.lang = b.dataset.lang || 'en-US';
    const voces = window.speechSynthesis.getVoices();
    const voz = voces.find(v => v.lang === u.lang) || voces.find(v => v.lang && v.lang.startsWith('en'));
    if (voz) u.voice = voz;
    u.rate = 0.85;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  });
}
"""

# --- Datos personales: uno por lector, no uno para todos ------------------
# En local hay un solo lector y todo vive en ~/.literalevel. En un despliegue
# el proceso es UNO para todos los visitantes, asi que un unico cuaderno.db,
# perfil.json o sesion.json significa que quien entra ve el libro que subio
# otro y las palabras que consulto otro. El marcapaginas es el caso mas feo:
# `demo.load` se ejecuta en cada carga de pagina y pintaria el capitulo del
# PDF privado del visitante anterior.

# Configurable por entorno (`LITERALEVEL_DATOS`, ver `config.dir_datos`) para
# dos cosas distintas. Una: que las PRUEBAS no escriban en los datos reales de
# quien ejecuta la app -la bateria abre libro.txt, vacio.txt, falso.txt... y los
# iba anotando en la biblioteca de verdad; Miguel abrio "Mis libros" en el movil
# y se encontro 24 archivos de prueba entre sus cuatro libros-. Y dos: que en un
# Space se pueda apuntar a un DISCO PERSISTENTE, porque el del contenedor se
# borra en cada reinicio y ahi vive todo lo del lector.
BASE_DATOS_LECTOR = config.dir_datos()
EN_LA_NUBE = bool(os.environ.get("SPACE_ID") or os.environ.get("PORT"))
_SESION_SEGURA = re.compile(r"[^A-Za-z0-9_-]")


# Identidad del lector: `session_hash` del navegador -> id estable del lector.
#
# Gradio estrena `session_hash` en CADA carga de pagina, asi que colgar los
# datos de ahi significa que recargar es estrenar carpeta: el lector fijaba su
# nivel, leia "Guardado", pulsaba F5 y volvia a "Todavia no has fijado tu
# nivel". Medido en el Space: `77zzh3u3pz5` antes de recargar, `rh9k3tdqku`
# despues.
#
# Y no basta con persistir: los datos de dos visitantes distintos no pueden
# mezclarse. Las dos cosas no salen del `session_hash`, asi que la identidad la
# pone el NAVEGADOR y la guarda en `localStorage`: sobrevive a recargar y a
# cerrar la pestana, y es distinta en cada navegador. `_registrar_lector` la
# ata a la sesion en curso y `_dir_lector` la consulta.
#
# Sigue SIN ser autenticacion, igual que antes: quien copie el identificador de
# otro entra en sus datos. Frena lo que de verdad importa -que un visitante
# tropiece con lo de otro sin buscarlo- y nada mas. Lo que cuesta dinero va
# detras de usuario y contrasena, que es otra puerta.
_LECTOR_POR_SESION: dict[str, str] = {}
_CANDADO_LECTOR = threading.Lock()


def _registrar_lector(id_navegador: str, peticion: gr.Request = None) -> None:
    """Ata la identidad que trae el navegador a esta sesion de Gradio.

    La llama `demo.load` en cada carga, ANTES que nada que lea datos: si
    `_perfil_inicial` o `_reanudar` corrieran primero, leerian la carpeta
    equivocada. Por eso van encadenados con `.then()` y no sueltos.
    """
    sesion = getattr(peticion, "session_hash", None) if peticion else None
    if not sesion:
        return
    # El id viene del navegador, o sea de fuera: se sanea igual que el
    # `session_hash`. Sin esto, un `../../` en `localStorage` escribiria donde
    # quisiera.
    limpio = _SESION_SEGURA.sub("", str(id_navegador or ""))[:64]
    if not limpio:
        return
    with _CANDADO_LECTOR:
        # `pop` y luego asignar, y no asignar encima: reasignar una clave que ya
        # existe NO la mueve al final en un dict de Python, asi que una sesion
        # vieja pero VIVA se quedaba en la cabecera de la fila y caia en la
        # siguiente poda. Con el pop, cada uso la manda al final.
        _LECTOR_POR_SESION.pop(str(sesion), None)
        _LECTOR_POR_SESION[str(sesion)] = limpio
        # Limpieza barata, como en `_gasto`: sin esto el diccionario crece con
        # cada carga de pagina y no se vacia nunca. Se tiran las MENOS usadas
        # hace mas tiempo, que con el pop de arriba y el de `_dir_lector` son
        # de verdad las mas antiguas y no solo las que entraron primero. Quien
        # caiga no pierde nada: vuelve a registrarse en la siguiente carga.
        if len(_LECTOR_POR_SESION) > 5000:
            for k in list(_LECTOR_POR_SESION)[:2500]:
                del _LECTOR_POR_SESION[k]


def _dir_lector(peticion=None) -> Path:
    """Carpeta de datos de ESTE lector.

    En local, la de siempre, para no partir en dos lo que ya haya guardado.
    Desplegada, una por lector: la identidad que trae el navegador si la hay, y
    si no el `session_hash`, que es lo que habia antes y sigue valiendo para la
    primera carga -mientras el `demo.load` de registro no haya llegado- y para
    quien tenga `localStorage` desactivado.
    """
    if not EN_LA_NUBE:
        return BASE_DATOS_LECTOR
    sesion = getattr(peticion, "session_hash", None) if peticion is not None else None
    propio = _lector_de_sesion(sesion)
    limpio = propio or (_SESION_SEGURA.sub("", str(sesion))[:64] if sesion else "")
    # Con cuenta, los datos son de la CUENTA y no del navegador (Miguel, 26 sep:
    # en el movil y en la tablet, con la misma cuenta, veia dos lectores).
    cuenta = _cuenta_atada(limpio)
    if cuenta:
        return BASE_DATOS_LECTOR / "cuentas" / cuenta
    return BASE_DATOS_LECTOR / "lectores" / (limpio or "anonimo")


# --- Datos por cuenta -------------------------------------------------------
# Al entrar con usuario y contrasena, el navegador queda ATADO a la cuenta, y
# `_dir_lector` le da la carpeta `cuentas/<nombre>`: la misma desde cualquier
# aparato. Sin cuenta, todo sigue como antes, por navegador. Las cuentas
# empezaron en cero el 26 sep: lo guardado antes en cada navegador se queda en
# `lectores/<id>` y no se copia (decision de Miguel).
#
# La atadura se guarda en disco (el bucket de /data en el Space) y no solo en
# memoria, como la sesion de pago: tras un reinicio del Space el lector sigue
# viendo lo de su cuenta aunque para lo que cuesta dinero tenga que volver a
# entrar. En disco va solo el NOMBRE de la cuenta, nunca la contrasena.
_ARCHIVO_ATADURAS = "cuentas_atadas.json"
_ATADURAS: dict[str, str] | None = None
_CANDADO_ATADURAS = threading.Lock()


def _nombre_cuenta(nombre: str | None) -> str:
    return _SESION_SEGURA.sub("", str(nombre or "").strip().lower())[:64]


def _ataduras() -> dict[str, str]:
    """Carga perezosa: la base de datos puede cambiar entre pruebas."""
    global _ATADURAS
    if _ATADURAS is None:
        try:
            crudo = json.loads((BASE_DATOS_LECTOR / _ARCHIVO_ATADURAS).read_text(encoding="utf-8"))
            _ATADURAS = {str(k): _nombre_cuenta(v) for k, v in crudo.items() if _nombre_cuenta(v)}
        except (OSError, ValueError, AttributeError):
            _ATADURAS = {}
    return _ATADURAS


def _guardar_ataduras() -> None:
    ruta = BASE_DATOS_LECTOR / _ARCHIVO_ATADURAS
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(".tmp")
        tmp.write_text(json.dumps(_ATADURAS or {}, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, ruta)
    except OSError as e:
        print(f"_guardar_ataduras: {type(e).__name__}: {e}", file=sys.stderr)


def _cuenta_atada(lector: str | None) -> str | None:
    if not lector:
        return None
    with _CANDADO_ATADURAS:
        return _ataduras().get(str(lector))


def _atar_cuenta(peticion, nombre: str | None) -> None:
    """Ata (o, con `nombre` vacio, desata) este navegador a una cuenta."""
    if not EN_LA_NUBE:
        return
    lector = _sesion_de(peticion)
    if not lector or lector == "local":
        return
    limpio = _nombre_cuenta(nombre)
    with _CANDADO_ATADURAS:
        tabla = _ataduras()
        if limpio:
            if tabla.get(lector) == limpio:
                return
            tabla[lector] = limpio
        elif tabla.pop(lector, None) is None:
            return
        _guardar_ataduras()


def _reiniciar_ataduras() -> None:
    """Solo para las pruebas: olvida lo cargado de disco."""
    global _ATADURAS
    with _CANDADO_ATADURAS:
        _ATADURAS = None


def _lector_de_sesion(sesion) -> str | None:
    """La identidad que el navegador ató a esta sesion, o None.

    Aparte de `_dir_lector` porque `_dir_lector` se corta antes en local -
    devuelve la carpeta de siempre y no llega a mirar el diccionario-, y
    entonces la parte que de verdad hay que probar no se ejecutaba nunca fuera
    del Space. Lo encontro una prueba nueva: fallaba diciendo "consultar no
    cuenta como uso para la poda" y tenia razon, porque en local no consultaba.
    """
    if not sesion:
        return None
    with _CANDADO_LECTOR:
        propio = _LECTOR_POR_SESION.get(str(sesion))
        if propio is not None:
            # Al final de la fila: esto es lo que convierte la poda en "las
            # menos usadas" y no "las que entraron primero".
            _LECTOR_POR_SESION.pop(str(sesion), None)
            _LECTOR_POR_SESION[str(sesion)] = propio
    return propio


# --- Freno de gasto: cuantas veces por hora puede costar dinero -----------
# Cada consulta lexica puede llamar a gpt-5 y generar audio con tts-1, y cada
# practica de voz usa whisper-1, gpt-5 y tts-1. Todo eso lo paga la clave del
# dueño. Recortar las entradas abarata el peor caso; esto lo *frena*.
#
# Los limites son por IP y por hora, generosos para leer de verdad -treinta
# palabras consultadas en una hora es mucha lectura- y estrechos para un bot.
# Las acciones que no cuestan dinero (leer, buscar, medir un capitulo) no se
# limitan: son locales.

LIMITE_CONSULTAS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_CONSULTAS", "30"))
LIMITE_VOZ_HORA = int(os.environ.get("LITERALEVEL_LIMITE_VOZ", "10"))
# La sinopsis son cuatro pasajes de 900 palabras a la API por pulsacion, y
# nunca acierta en cache si el archivo cambia una palabra. Es la mas cara por
# uso de las tres, asi que su tope es el mas bajo.
LIMITE_SINOPSIS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_SINOPSIS", "6"))
# Descargar de Gutenberg no cuesta dinero, pero son hasta tres peticiones de 45
# s que ocupan un hueco de la cola mientras esperan: es la unica peticion lenta
# que puede dejar a los demas sin servicio. Alto a proposito: veinte libros
# NUEVOS en una hora no es leer, y los ya descargados no cuentan.
LIMITE_DESCARGAS_HORA = int(os.environ.get("LITERALEVEL_LIMITE_DESCARGAS", "20"))
# Intentos FALLIDOS de entrar por IP y por hora. `compare_digest` hace que el
# tiempo de respuesta no diga nada, pero sin freno se puede probar un
# diccionario de contrasenas corrientes contra `LITERALEVEL_CUENTAS` a la
# velocidad de la red. Solo gastan ficha los intentos que fallan: quien acierta
# puede entrar las veces que quiera. Quince y no tres porque la contrasena del
# profesor va por WhatsApp y el dia de la demo nadie quiere un candado.
LIMITE_INTENTOS_ENTRAR = int(os.environ.get("LITERALEVEL_LIMITE_INTENTOS", "15"))
# Y por USUARIO, ademas de por IP. El cubo por IP solo frena a quien no puede
# cambiar de IP, y la IP salia de una cabecera que escribe el cliente (revision
# de api.py en 2a49bf2, hallazgo 1). Las contrasenas son dos palabras de 50 y
# tres cifras: 2.205.000 combinaciones. Con 20 fallos por usuario y hora son 480
# al dia por perfil; con los diez perfiles, un mes da en torno a un 6,5 % de
# acertar alguno. Por encima de los 15 por IP a proposito: si no, quien falla
# desde una IP dejaria fuera al dueño que entra desde otra antes de agotar la
# suya. El precio: quien conozca un usuario puede cerrarle la puerta una hora.
LIMITE_INTENTOS_USUARIO = int(os.environ.get("LITERALEVEL_LIMITE_INTENTOS_USUARIO", "20"))
_VENTANA = 3600.0

_gasto: dict[str, list[float]] = {}
_CANDADO_GASTO = threading.Lock()

# Cuantos proxies de confianza hay delante de la app. Vacio: se toma la ultima
# direccion PUBLICA de x-forwarded-for, la que añadio el primer proxy que vio
# al visitante. "0": no se mira la cabecera. "N": la N-esima empezando por la
# derecha. Ver `_ip`.
_SALTOS_PROXY = os.environ.get("LITERALEVEL_SALTOS_PROXY", "").strip()
# Redes que no son un visitante sino un proxy o la red del contenedor. A mano y
# no con `is_private`: Python cuenta como privadas las redes de documentacion
# (203.0.113.0/24 y compañia), que son las que usan las pruebas.
_REDES_INTERNAS = ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10",
                   "127.0.0.0/8", "169.254.0.0/16", "::1/128", "fc00::/7", "fe80::/10")
_IP_DIAGNOSTICADA = False


def _direccion(texto: str):
    """La direccion IP de un trozo de x-forwarded-for, o None si no lo es."""
    import ipaddress
    try:
        return ipaddress.ip_address(str(texto).strip().strip("[]"))
    except ValueError:
        return None


def _es_interna(direccion) -> bool:
    import ipaddress
    return any(direccion.version == red.version and direccion in red
               for red in (ipaddress.ip_network(r) for r in _REDES_INTERNAS))


def _ip(peticion) -> str:
    """La IP del visitante, para los topes por hora y el freno de la puerta.

    Detras de un proxy viene en x-forwarded-for, pero el PRIMER valor de esa
    cabecera lo escribe el cliente: los proxies AÑADEN al final. Antes se tomaba
    ese primero, y cambiandolo en cada peticion no habia freno de contrasenas ni
    tope por hora (revision de api.py en 2a49bf2, hallazgo 1). Ahora se toma la
    ultima direccion publica: lo que el cliente se invente queda a su izquierda.
    Si todas son internas, la ultima. `LITERALEVEL_SALTOS_PROXY` fija el numero
    exacto de proxies si se conoce.

    La primera vez que llega la cabecera se escribe en el registro su FORMA
    -cuantos saltos, cuales son internos y cual se usa, sin las direcciones-,
    para comprobar en el Space que se elige bien.
    """
    global _IP_DIAGNOSTICADA
    if peticion is None:
        return "local"
    cabeceras = getattr(peticion, "headers", None) or {}
    try:
        reenviada = cabeceras.get("x-forwarded-for")
    except AttributeError:
        reenviada = None
    cliente = getattr(peticion, "client", None)
    directa = str(getattr(cliente, "host", None) or "desconocida")[:64]
    if not reenviada or _SALTOS_PROXY == "0":
        return directa
    cadena = [t.strip() for t in str(reenviada).split(",") if t.strip()]
    if not cadena:
        return directa
    if _SALTOS_PROXY.isdigit():
        n = int(_SALTOS_PROXY)
        elegida = cadena[-n] if len(cadena) >= n else cadena[0]
    else:
        ips = [(t, d) for t, d in ((t, _direccion(t)) for t in cadena) if d is not None]
        elegida = next((t for t, d in reversed(ips) if not _es_interna(d)),
                       ips[-1][0] if ips else None)
    if not _IP_DIAGNOSTICADA:
        _IP_DIAGNOSTICADA = True
        forma = ", ".join(
            "no-ip" if d is None else ("interna" if _es_interna(d) else "publica")
            for d in (_direccion(t) for t in cadena))
        posicion = cadena.index(elegida) + 1 if elegida in cadena else "ninguna (la directa)"
        print(f"_ip: x-forwarded-for con {len(cadena)} valores ({forma}); se usa el {posicion}. "
              "Ajustable con LITERALEVEL_SALTOS_PROXY.", file=sys.stderr)
    return (elegida or directa)[:64]


def _minutos_para_la_siguiente(cubo: str, peticion, clave: str | None = None) -> int:
    """Cuanto falta para que se libere una ficha de este cubo, en minutos.

    El aviso de tope decia siempre "60 minutos", que es la ventana entera y
    casi nunca lo que falta: quien agoto el cupo hace cincuenta y ocho minutos
    leia que tenia que esperar una hora mas. Se calcula con la marca mas
    antigua que sigue viva.

    `clave` sustituye a «cubo:IP» cuando el cubo no va por IP (el freno por
    usuario de la puerta).
    """
    clave = clave or f"{cubo}:{_ip(peticion)}"
    ahora = time.time()
    with _CANDADO_GASTO:
        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]
    if not marcas:
        return 0
    faltan = _VENTANA - (ahora - min(marcas))
    return max(1, int(faltan // 60) + (1 if faltan % 60 else 0))


def _cubo_agotado(peticion, cubo: str, tope: int, clave: str | None = None) -> bool:
    """Si el cubo ya no tiene fichas. MIRA, no consume.

    Hace falta para la puerta de entrada: ahi la ficha la gasta el intento
    fallido, asi que preguntar y cobrar no pueden ser la misma operacion como
    en `_dentro_del_limite`.
    """
    if tope <= 0:
        return False
    clave = clave or f"{cubo}:{_ip(peticion)}"
    ahora = time.time()
    with _CANDADO_GASTO:
        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]
    return len(marcas) >= tope


def _dentro_del_limite(peticion, cubo: str, tope: int, clave: str | None = None) -> bool:
    """Consume una ficha del cubo. False si ya no quedan en esta hora."""
    if tope <= 0:
        return True                        # 0 o negativo = sin limite
    clave = clave or f"{cubo}:{_ip(peticion)}"
    ahora = time.time()
    with _CANDADO_GASTO:
        marcas = [t for t in _gasto.get(clave, []) if ahora - t < _VENTANA]
        if len(marcas) >= tope:
            _gasto[clave] = marcas
            return False
        marcas.append(ahora)
        _gasto[clave] = marcas
        # Limpieza barata: sin esto el diccionario crece con cada IP nueva.
        if len(_gasto) > 5000:
            for k in [k for k, v in _gasto.items()
                      if not any(ahora - t < _VENTANA for t in v)]:
                del _gasto[k]
    return True


# --- Perfiles de acceso a lo que cuesta dinero ----------------------------
# El perfil con el que se entra se guarda por sesion de navegador, en memoria,
# y no viaja en los componentes de la interfaz: asi no acaba en un `gr.State`
# que se serializa al navegador ni se cuela en una traza de error. Se pierde
# al reiniciar el proceso, y esta bien que sea asi: se vuelve a entrar y ya.
_CODIGO_SESION: dict[str, str] = {}
_CANDADO_CODIGO = threading.Lock()


def _sesion_de(peticion) -> str:
    """La clave con la que se recuerda con QUE perfil entro este visitante.

    La identidad del NAVEGADOR primero, y el `session_hash` solo si no la
    hay. Gradio estrena `session_hash` en cada carga de pagina, asi que
    indexar por el significaba que recargar cerraba la sesion de pago: los
    datos del lector volvian -esos ya cuelgan de `localStorage`- y la consulta
    lexica le decia otra vez "necesita que entres con tu perfil". En una demo,
    teclear usuario y contrasena delante del profesor cada vez que se recarga.

    Sigue SIN ser autenticacion, igual que para los datos: quien copie el
    identificador de otro hereda su sesion. Lo que cambia es que recargar deja
    de ser un cierre de sesion.
    """
    h = getattr(peticion, "session_hash", None) if peticion is not None else None
    return str(_lector_de_sesion(h) or h or "local")


def _codigo_de(peticion) -> str | None:
    with _CANDADO_CODIGO:
        return _CODIGO_SESION.get(_sesion_de(peticion))


# Centinela de `_puede_pagar`: «lee el codigo de la sesion». No es None, que ya
# significa «sin entrar», ni `cuentas._SIN_CODIGO`, que es un texto (f4, reinicio 27).
_LEER_DE_LA_SESION = object()


def _puede_pagar(peticion, codigo=_LEER_DE_LA_SESION) -> tuple[bool, str]:
    """Comprueba el cupo Y lo consume, en una sola operacion.

    Antes esto solo preguntaba, y quien llamaba apuntaba el uso despues con
    `_apuntar_uso`. Entre las dos cosas cabia una condicion de carrera, y esta
    reproducida: con un codigo de tope 2 y veinte peticiones simultaneas
    pasaban las veinte. `cuentas.consumir` hace las dos bajo el mismo candado.

    Con `codigo`, cobra a ese (incluido None) y no vuelve a leer la sesion: quien
    luego devuelve el uso (la voz sin voz) cobra y devuelve a la misma cuenta aunque
    la sesion cambie entre medias (reinicio 27).
    """
    if codigo is _LEER_DE_LA_SESION:
        codigo = _codigo_de(peticion)
    return cuentas.consumir(BASE_DATOS_LECTOR, codigo)


def _entrar(usuario: str, clave: str, peticion: gr.Request = None) -> str:
    """Comprueba usuario y contrasena, y los recuerda para esta sesion.

    Antes esto pedia un codigo suelto y vivia en un acordeon cerrado dentro de
    la pestana de Pronunciacion. Nadie lo encontraba, empezando por el autor.
    """
    if not cuentas.hay_codigos():
        return ("No hace falta entrar: esta copia no tiene perfiles "
                "configurados y todo está disponible.")
    # El freno va ANTES de comprobar nada: si ya se agotaron los intentos, esta
    # peticion no llega a `verificar` y no sirve para descartar contrasenas.
    # Dos cubos: por IP y por USUARIO (en minusculas, exista o no, para que el
    # freno no diga que usuarios hay). El segundo para a quien cambia de IP
    # en cada intento.
    por_usuario = f"entrar-usuario:{str(usuario or '').strip().lower()[:80]}"
    if (_cubo_agotado(peticion, "entrar", LIMITE_INTENTOS_ENTRAR)
            or _cubo_agotado(peticion, "entrar-usuario", LIMITE_INTENTOS_USUARIO,
                             clave=por_usuario)):
        faltan = max(_minutos_para_la_siguiente("entrar", peticion),
                     _minutos_para_la_siguiente("entrar-usuario", peticion, clave=por_usuario))
        return (f"**Demasiados intentos fallidos.** Vuelve a probar en "
                f"{faltan} minuto{'s' if faltan != 1 else ''}.")
    # Este manejador lo toca TODO visitante, y era el unico que no cumplia la
    # regla del modulo: una ene en la contrasena hacia que `compare_digest`
    # lanzase TypeError y la interfaz ensenaba un "Error" pelado. La causa ya
    # esta arreglada en `cuentas.verificar`, pero la puerta de entrada no puede
    # depender de que nada mas vuelva a fallar nunca: si el disco del cupo se
    # queda sin sitio o el secreto llega mal formado, el visitante tiene que
    # leer una frase, no un traceback.
    try:
        c = cuentas.verificar(usuario, clave)
        if c is None:
            with _CANDADO_CODIGO:
                _CODIGO_SESION.pop(_sesion_de(peticion), None)
            _atar_cuenta(peticion, None)
            # La ficha la gasta el que falla, no el que entra: una de cada cubo.
            _dentro_del_limite(peticion, "entrar", LIMITE_INTENTOS_ENTRAR)
            _dentro_del_limite(peticion, "entrar-usuario", LIMITE_INTENTOS_USUARIO,
                               clave=por_usuario)
            return ("**No he podido entrar.** Revisa el usuario y la contraseña; "
                    "se distinguen mayúsculas en la contraseña, no en el usuario.")
        with _CANDADO_CODIGO:
            _CODIGO_SESION[_sesion_de(peticion)] = f"{usuario.strip()}:{clave.strip()}"
        _atar_cuenta(peticion, c.nombre)
        resto = cuentas.queda(BASE_DATOS_LECTOR, c)
    except Exception as e:
        # El detalle va al registro del Space y NO a la pantalla: aqui, a
        # diferencia de los demas manejadores, el mensaje de error lo lee quien
        # esta probando contrasenas, y no tiene por que aprender si el fallo
        # fue del usuario, de la clave o de la base de datos del cupo.
        print(f"_entrar: {type(e).__name__}: {e}", file=sys.stderr)
        return ("**No he podido entrar.** Ha fallado algo al comprobar el "
                "perfil; vuelve a intentarlo.")
    return _bienvenida(c, resto)


def _bienvenida(c, resto: int | None) -> str:
    """El «Has entrado como...», que lo dicen dos sitios: el boton de entrar y
    la carga de la pagina."""
    if resto is None:
        return (f"Has entrado como **{c.nombre}**. Sin límite de usos: ya "
                "tienes la explicación en contexto, «¿de qué trata?» y la "
                "corrección de pronunciación.")
    return (f"Has entrado como **{c.nombre}**. Te quedan **{resto}** usos de "
            "la explicación en contexto, «¿de qué trata?» y la pronunciación.")


def _estado_de_entrada(peticion: gr.Request = None) -> str:
    """Lo que dice la caja de entrada al CARGAR la pagina.

    La sesion de pago ya sobrevive a recargar -la identidad la pone el
    navegador-, pero la caja volvia vacia y sin el «Has entrado como...». El
    visitante no tenia forma de saber si seguia dentro hasta que consultaba
    una palabra, asi que volvia a teclear usuario y contrasena por si acaso.

    Va encadenado DESPUES de `_registrar_lector`, como `_perfil_inicial`: si
    corriera suelto, `_sesion_de` leeria un `session_hash` recien estrenado y
    no encontraria la sesion de pago que si existe.
    """
    codigo = _codigo_de(peticion)
    if not codigo:
        return ""
    usuario, _, clave = codigo.partition(":")
    try:
        c = cuentas.verificar(usuario, clave)
        if c is None:
            # El secreto del Space pudo cambiar con la sesion viva.
            with _CANDADO_CODIGO:
                _CODIGO_SESION.pop(_sesion_de(peticion), None)
            _atar_cuenta(peticion, None)
            return ""
        return _bienvenida(c, cuentas.queda(BASE_DATOS_LECTOR, c))
    except Exception as e:
        print(f"_estado_de_entrada: {type(e).__name__}: {e}", file=sys.stderr)
        return ""


def _salir(peticion: gr.Request = None) -> str:
    """Olvida el perfil de esta sesion. Util en un ordenador compartido."""
    with _CANDADO_CODIGO:
        _CODIGO_SESION.pop(_sesion_de(peticion), None)
    _atar_cuenta(peticion, None)
    return "Has salido. Lo gratuito sigue funcionando."


def _cuanto_falta(minutos: int, idioma: str = "es") -> str:
    """«en 1 minuto» / «en unos 12 minutos»: la prueba de f4 encontró «1 minutos»."""
    m = max(1, int(minutos))
    if idioma == "en":
        return "in 1 minute" if m == 1 else f"in about {m} minutes"
    return "en 1 minuto" if m == 1 else f"en unos {m} minutos"


def _reloj_llano(minutos: int) -> str:
    """`ficha.reloj` con «1 minuto» en singular (ficha.py es de f4 y dice «1 minutos»)."""
    t = ficha.reloj(minutos)
    return "1 minuto" if t == "1 minutos" else t


def _rango_de_tiempo(comodo: int, exigente: int) -> str:
    """«entre 12 minutos y 18 minutos», o uno solo si los dos se dicen igual:
    un cuento corto daba «entre 1 minuto y 1 minuto» (Central, 15 sep)."""
    a, b = _reloj_llano(comodo), _reloj_llano(exigente)
    return a if a == b else f"entre {a} y {b}"


# Que se acabo y que sigue, por cubo. El texto de antes decia «consultas» en los
# cinco caminos que lo comparten, asi que en Pronunciar nombraba el cubo del
# diccionario (30/h) y no el de la voz (10/h), que era el agotado: a Miguel le
# mando a mirar el limite equivocado (16 sep 2026). Y prometia que medir un
# capitulo «no cuesta nada», que dejo de ser verdad con los topes de medidas;
# eso ya lo decia el comentario de `_mensaje_tope_medir` en api.py.
_LIMITES = {
    "voz": ("correcciones de pronunciación",
            "Grabarte y escucharte, leer y buscar siguen funcionando."),
    "lexico": ("explicaciones en contexto",
               "El diccionario, leer y buscar siguen funcionando."),
    "sinopsis": ("resúmenes",
                 "La ficha del libro, leer y buscar siguen funcionando."),
    "subidas": ("libros subidos",
                "Leer y buscar siguen funcionando."),
}


def _mensaje_limite(idioma: str, minutos: int, cubo: str = "") -> str:
    """El aviso del tope por hora, diciendo QUE se ha acabado.

    `cubo` es opcional a proposito: sin el sale el generico, que es lo que ve
    quien llame sin decirlo. En ingles no se reparte por cubo porque el unico
    camino que pasa `idioma` es el del lexico.
    """
    if idioma == "en":
        return (f"You have reached one of this hour's limits. "
                f"Try again {_cuanto_falta(minutos, 'en')}. Reading and searching keep working.")
    que, sigue = _LIMITES.get(cubo, ("", "Leer y buscar siguen funcionando."))
    cabeza = (f"Has llegado al límite de {que} de esta hora." if que
              else "Has llegado a un límite de esta hora.")
    return f"{cabeza} Vuelve a intentarlo {_cuanto_falta(minutos)}. {sigue}"


def _archivo_lector(nombre: str, peticion=None) -> str:
    d = _dir_lector(peticion)
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return str(d / nombre)


# --- Aspecto: hielo sobre espacio ----------------------------------------
# Azul de iceberg -claro arriba, profundo abajo- sobre negro espacial con
# estrellas. Los tonos frios y oscuros son deliberados: se lee de noche y el
# texto tiene que ser lo unico que brille.

HIELO = gr.themes.Color(
    name="hielo",
    c50="#eef9fd", c100="#d3f0fa", c200="#a8e2f4", c300="#79d0ea",
    c400="#4bb8da", c500="#2e9cc4", c600="#237ea6", c700="#1d6285",
    c800="#1b4d68", c900="#173d53", c950="#0e2534",
)
NOCHE = gr.themes.Color(
    name="noche",
    c50="#eef1f7", c100="#d6dcea", c200="#aeb8d0", c300="#8090b3",
    c400="#5a6b92", c500="#3f4f72", c600="#2e3b58", c700="#222c44",
    c800="#171e30", c900="#0e1320", c950="#05070d",
)
TEMA = gr.themes.Base(primary_hue=HIELO, secondary_hue=HIELO, neutral_hue=NOCHE)


def _estrellas(n: int = 90) -> str:
    """Campo de estrellas en CSS puro, sin imagenes ni peticiones de red.

    Semilla fija: el cielo tiene que ser el mismo en cada arranque, si no
    parpadea de una recarga a otra y distrae.
    """
    import random
    r = random.Random(20260906)
    capas = []
    for _ in range(n):
        x, y = r.uniform(0, 100), r.uniform(0, 100)
        tam = r.choice([1, 1, 1, 1.4, 1.8])
        op = r.uniform(0.25, 0.95)
        capas.append(f"radial-gradient({tam}px {tam}px at {x:.1f}% {y:.1f}%,"
                     f"rgba(226,242,252,{op:.2f}) 50%,transparent 51%)")
    return ",".join(capas)


# Estructura, no color. Todos los colores salen de las variables que pone
# `paletas.py`, asi que una paleta nueva no puede romper la maquetacion.
#
# Y hay una correccion que NO es de gusto y va para todas las paletas: la
# primera lectora real de la app, de quince anos, dijo que la pagina se siente
# antigua, "todo muy recto, muy marcado". Tenia razon. Esquinas de 14 px,
# bordes finos y sombras suaves en vez de aristas y contraste duro.
_RADIO = "14px"

# Las estrellas se calculan una vez y se le pasan a la paleta que las quiera.
_ESTRELLAS_CSS = _estrellas()


def _css_paleta(clave: str) -> str:
    """El `<style>` de la paleta elegida. Nunca lanza: si la clave no existe
    -un valor viejo guardado en el navegador, por ejemplo- vuelve a la de
    siempre en vez de dejar la pagina sin colores."""
    try:
        return paletas_mod.css(str(clave), _ESTRELLAS_CSS)
    except Exception:
        return paletas_mod.css(paletas_mod.POR_DEFECTO, _ESTRELLAS_CSS)

_CSS_GLOBAL = f"""<style>
/* El bloque que transporta esta hoja de estilo no debe ocupar sitio; un
   <style> sigue aplicandose aunque su contenedor este oculto. */
#ll-css,#ll-paleta-css{{display:none}}
/* El indice de un libro puede tener 366 capitulos. Sin altura maxima empuja
   toda la pagina y hay que recorrerla entera para volver al texto. */
#ll-indice .wrap{{max-height:46vh;overflow-y:auto}}
h1{{
  background:linear-gradient(96deg,var(--ll-titulo-1) 0%,
    var(--ll-titulo-2) 40%,var(--ll-titulo-3) 100%);
  -webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;color:transparent;
  letter-spacing:-.015em;
  filter:drop-shadow(0 0 26px var(--ll-sombra-titulo))}}
/* Paneles translucidos, no cajas opacas. */
.block,.form,.panel,.gr-box{{
  background-color:var(--ll-panel) !important;
  border-color:var(--ll-borde) !important;
  border-radius:{_RADIO} !important}}
/* El desenfoque, solo con raton. Laura (12 sep), en el movil: «deslizo con el
   dedo y dos, tres segundos y la pagina se empieza a mover». Un
   `backdrop-filter` en CADA bloque -son mas de cien- obliga al telefono a
   recomponer todo lo que hay detras de cada panel en cada fotograma del
   desplazamiento. Con paneles al 86-90 % de opacidad casi no se ve. */
@media (hover:hover) and (pointer:fine){{
  .block,.form,.panel,.gr-box{{backdrop-filter:blur(7px)}}}}
/* El texto ya no toca el borde redondeado. Laura: «no dejas un espacio entre
   el cuadro y lo que escribes… se come el palito de la P». Un Markdown de
   Gradio es un bloque SIN relleno (`hide-container`), pero aqui todo bloque
   lleva fondo de panel, asi que el texto quedaba pegado al canto y la curva
   de la esquina se comia las letras. Solo cuando tiene contenido: uno vacio
   con relleno seria una franja sin nada. Y solo Markdown: un gr.HTML tambien
   lleva `.prose` (dentro de `.html-container`) y el lector, que ya trae su
   relleno, perdia otros 30 px de ancho en el movil. Lo encontro Codex. */
.block.hide-container:not(:has(.html-container)):has(.prose *){{
  padding:.6rem .95rem !important}}
/* Nada de aristas: botones, cajas de texto, desplegables y pestanas. */
button,.gr-button,input,textarea,select,
.wrap-inner,.secondary-wrap,.gr-input,.gr-text-input{{
  border-radius:{_RADIO} !important}}
button,.gr-button{{
  transition:transform .08s ease,box-shadow .18s ease,filter .18s ease}}
button:hover,.gr-button:hover{{filter:brightness(1.06)}}
button:active,.gr-button:active{{transform:translateY(1px)}}
button.primary,.primary button{{
  background:linear-gradient(180deg,var(--ll-boton-alto),
    var(--ll-acento-hondo)) !important;
  border-color:var(--ll-borde) !important;
  color:var(--ll-boton-texto) !important;
  box-shadow:0 2px 14px var(--ll-sombra-titulo)}}
/* Gradio 6 ya no tiene `.tab-nav`: la barra es `.tab-wrapper > .tab-container`
   y con el selector viejo esta regla no se aplicaba a nada. */
.tab-container button.selected{{
  color:var(--ll-acento) !important;
  border-bottom-color:var(--ll-acento) !important}}
/* La barra de pestanas hace de barra de navegacion: se queda arriba al bajar
   por la pagina y va centrada. Laura (12 sep) queria «un navbar arriba» con
   las funciones, y en la laptop todo se veia cargado a un lado. */
/* `!important` porque Gradio le pone `position:relative` con su clase de
   Svelte, que es mas especifica: sin el, la barra se iba con el resto. */
/* Y `clip` en vez del `overflow:hidden` que trae el contenedor de Gradio: un
   `hidden` convierte al contenedor en caja de desplazamiento y ningun
   `sticky` de dentro llega a pegarse. `clip` recorta igual y no lo impide. */
.gradio-container{{overflow:clip !important}}
.tab-wrapper{{
  position:sticky !important;top:0;z-index:30;
  background:var(--ll-fondo);border-radius:0 0 {_RADIO} {_RADIO}}}
/* Centrada solo donde sobra sitio. En el movil Gradio manda al menu «...» lo
   que no cabe, y centrar dejaba 130 px vacios a la izquierda que se comian
   una pestana entera. */
@media (min-width:641px){{.tab-container{{justify-content:center}}}}
/* El boton de ajustes en la esquina de la cabecera, fuera del flujo: como
   elemento de la fila, en el movil dejaba la cabecera a media anchura.
   ABAJO a la derecha, no arriba: en el Space la cabecera fija de Hugging Face
   (#huggingface-space-header, la insignia con el nombre del Space) queda
   encima de la esquina superior derecha y el boton no se podia pulsar, ni en
   el telefono ni en la laptop. Medido con document.elementFromPoint; un
   clic desde JavaScript lo atravesaba y la prueba decia que funcionaba. El
   relleno inferior reserva su sitio para que no pise la ultima linea. */
#ll-cabecera{{position:relative}}
#ll-cabecera .block.hide-container{{padding-bottom:3.1rem !important}}
#ll-b-ajustes{{position:absolute !important;top:auto !important;bottom:.7rem;
  right:.7rem;z-index:5;width:auto !important;min-width:0 !important}}
#ll-ajustes{{
  background:var(--ll-panel);border:1px solid var(--ll-borde);
  border-radius:{_RADIO};padding:.8rem}}
/* En el movil caben mas funciones a la vista si cada pestana no gasta 32 px
   de relleno: con 16 por lado solo cabian «Mi nivel» y «Buscar lectura». */
@media (max-width:640px){{
  .tab-container button[role="tab"]{{padding:0 6px !important}}
  /* Gradio deja 32 px de margen a cada lado en cualquier ancho. En 390 px eso
     es la sexta parte de la pantalla, y con el relleno del panel y del lector
     encima la columna de lectura se quedaba en cinco o seis palabras por
     linea. Con 12 px caben las cuatro funciones en la barra. */
  .main.fillable{{padding-left:12px !important;padding-right:12px !important}}}}
/* Las opciones de una lista, como fichas que se pueden tocar. En un movil un
   circulito de radio es un blanco de 12 px; la ficha entera es de 44. */
label:has(input[type="radio"]),label:has(input[type="checkbox"]){{
  border-radius:{_RADIO} !important;padding:.55rem .7rem}}
#ll-lector{{
  background:var(--ll-lector-fondo);border-color:var(--ll-borde);
  border-radius:{_RADIO};color:var(--ll-lector-texto)}}
#ll-lector::selection,#ll-lector p::selection{{
  background:var(--ll-seleccion)}}
#ll-voz{{
  background:var(--ll-lector-fondo);border-color:var(--ll-borde);
  border-radius:{_RADIO}}}
footer{{opacity:.78}}
/* El reproductor trae un boton de descarga que aqui no pinta nada: el
   audio es para oirlo en el momento, no para llevarselo. */
#ll-audio-ref a[download],#ll-audio-palabra a[download],
#ll-audio-ref a[href^="blob:"],#ll-audio-palabra a[href^="blob:"]{{
  display:none !important}}
</style>"""


# --- Recursos pesados: uno por proceso, cargado al primer uso -------------

_puntuador = None
_catalogo = None
_consultor = None

# Sin candado, dos peticiones que llegan a la vez construyen DOS modelos y
# duplican la memoria: el Puntuador son 278 MB de RSS y el catalogo 285 MB.
# La comprobacion "if es None" no es atomica frente a la carga que viene
# detras, que dura segundos.
_CANDADO = threading.Lock()


def puntuador() -> scoring.Puntuador:
    global _puntuador
    if _puntuador is None:
        with _CANDADO:
            if _puntuador is None:      # otro hilo pudo cargarlo mientras se esperaba
                _puntuador = scoring.Puntuador(RUTA_MODELO)
    return _puntuador


def catalogo() -> Catalogo:
    global _catalogo
    if _catalogo is None:
        with _CANDADO:
            if _catalogo is None:
                _catalogo = Catalogo()
    return _catalogo


def consultor() -> ConsultorLexico:
    global _consultor
    if _consultor is None:
        with _CANDADO:
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


def _claves_cuestionario() -> list[str]:
    """Las claves, en el mismo orden en que se pintan los controles.

    Primero las preguntas de opinion y despues los fragmentos de lectura.
    `perfil.desde_cuestionario` los distingue por la clave: promedia las
    opiniones y se queda con el techo mas dificil de los fragmentos.
    """
    return ([p[0] for p in perfil_mod.PREGUNTAS]
            + [f["clave"] for f in getattr(perfil_mod, "FRAGMENTOS", [])])


def _desde_cuestionario(p_actual, nombre, peticion: gr.Request, *valores):
    """Estima el nivel con las respuestas del cuestionario y lo guarda.

    OJO CON EL ORDEN DE LA FIRMA. `peticion` va ANTES de `*valores`, y no al
    final como en los demas manejadores. Gradio solo inyecta el `Request` en
    parametros posicionales: su `special_args` recorre la firma y **corta en el
    primer parametro que no lo sea** (`gradio/helpers.py`). Con `*valores`
    delante, `peticion` era keyword-only, no se inspeccionaba nunca y llegaba
    `None` siempre.

    Y `None` aqui no era inofensivo: desplegada, `_archivo_lector(..., None)`
    resuelve a `lectores/anonimo/`, UNA carpeta para todos los visitantes. Cada
    "Estimar mi nivel" pisaba el perfil del anterior -con su nombre dentro-, y
    al recargar la pagina `_perfil_inicial`, que si recibe el Request, buscaba
    en la carpeta de la sesion y no encontraba nada: el lector volvia a
    "Todavia no has fijado tu nivel" despues de leer "Guardado". En local no se
    nota, y por eso nadie lo habia visto.

    Poner `peticion` en la tercera posicion SI funciona, aunque parezca que
    desplazaria las respuestas: `special_args` inserta el Request en el indice
    de su parametro, asi que las entradas quedan alineadas. Comprobado
    ejecutando `special_args` con las dos firmas.
    """
    claves = _claves_cuestionario()
    respuestas = {k: v for k, v in zip(claves, valores) if v is not None}
    try:
        p = perfil_mod.desde_cuestionario(respuestas, nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    except (ValueError, OSError) as e:
        # Se conserva el perfil anterior: un fallo al estimar no debe borrarlo.
        return p_actual, _aviso(e), _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas.", _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


# En cuantas partes se trocea un libro para situar al lector con el. La usan
# `_muestra_de_libro`, que lo hace, y `_nivel_desde_libro`, que lo cuenta.
PARTES_MUESTRA = 8


def _cuerpo_para_muestra(libro):
    """Los capitulos de los que se puede sacar muestra, en orden.

    Esta aparte porque el mensaje que lee el lector tiene que contar LO MISMO
    que se midio: decia "tomando muestras de 8 partes" mirando
    `len(libro.capitulos)`, mientras la muestra salia de estos, que son los de
    300 palabras o mas. Con doce capitulos cortos y uno largo, anunciaba ocho
    partes y usaba una.
    """
    cuerpo = [c for c in libro.capitulos
              if c.palabras >= 300 and not _RELLENO_RE.search(c.titulo)]
    if not cuerpo:
        cuerpo = [c for c in libro.capitulos if c.palabras >= 100] or libro.capitulos
    return cuerpo


def _muestra_de_libro(libro, palabras: int = 2400) -> str:
    """Un extracto representativo del libro, para medir su dificultad.

    No vale con coger el principio: los primeros capitulos suelen ser
    portadilla, prologo o dedicatoria, y ademas muchos libros empiezan facil.
    Se toman trozos repartidos por toda la obra, saltandose el paratexto, para
    que la medida se parezca a lo que el lector va a encontrarse de verdad.
    """
    cuerpo = _cuerpo_para_muestra(libro)
    cuantos = min(PARTES_MUESTRA, len(cuerpo))
    if cuantos == 0:
        return ""
    # Repartidos por el libro, no los ocho primeros.
    paso = max(1, len(cuerpo) // cuantos)
    elegidos = cuerpo[::paso][:cuantos]
    por_capitulo = max(260, palabras // cuantos)
    trozos = []
    for c in elegidos:
        ws = ficha.para_medir(c.texto).split()
        # Desde un poco despues del principio: los titulillos viven ahi.
        inicio = min(40, max(0, len(ws) - por_capitulo))
        trozos.append(" ".join(ws[inicio:inicio + por_capitulo]))
    return "\n\n".join(trozos)


def _nivel_desde_libro(p_actual, nombre, archivo, peticion: gr.Request = None):
    """Situa al lector midiendo un libro entero que dice leer comodo.

    Pedirle que copie y pegue doscientas palabras es trabajo suyo que puede
    hacer la maquina: si ya tiene el libro, que lo suba.
    """
    if not archivo:
        pide = "Sube un `.epub`, `.pdf` o `.txt` que ya hayas leído."
        return p_actual, pide, pide
    try:
        libro = reader.cargar(archivo)
    except Exception as e:
        roto = _aviso(f"No pude abrir el archivo ({type(e).__name__}): {e}")
        return p_actual, roto, roto
    muestra = _muestra_de_libro(libro)
    if len(muestra.split()) < 150:
        corto = _aviso("Ese archivo tiene muy poco texto corrido para medirlo. "
                       "Prueba con un libro completo, o pega un fragmento a mano.")
        return p_actual, corto, corto
    try:
        p = perfil_mod.desde_muestra(muestra, puntuador(), nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    # `Exception` y no `(ValueError, OSError)`: lo que lanza torch al quedarse
    # sin memoria es `RuntimeError` -DefaultCPUAllocator: not enough memory- y
    # lo que lanza `safetensors` con una descarga del Hub cortada tampoco
    # desciende de OSError. El invariante de la cabecera no dice "casi nunca".
    except Exception as e:
        return p_actual, _aviso(e), _aviso(e)
    partes = min(PARTES_MUESTRA, len(_cuerpo_para_muestra(libro)))
    texto = (f"Medido con **{libro.titulo}**"
             + (f" — {libro.autor}" if libro.autor else "")
             + f", tomando muestras de {partes} "
               f"{'parte' if partes == 1 else 'partes'} "
               f"del libro.\n\n" + _describir(p)
             + "\n\nGuardado. Ya puedo recomendarte lecturas.")
    return p, texto, texto


def _desde_muestra(p_actual, nombre, texto, peticion: gr.Request = None):
    if not (texto or "").strip():
        pide = "Pega un fragmento que leas sin dificultad."
        return p_actual, pide, pide
    # El filtro ANTES de `puntuador()`. Python evalua los argumentos antes de
    # llamar, asi que pegar una lista o una carta de menu obligaba a cargar los
    # 328 MB del modelo para leer "esto no parece prosa". El mensaje al lector
    # no cambia: es el mismo `continuous_prose` + `_MOTIVOS` que aplica
    # `puntuar`, solo que consultado antes de pagar la carga.
    ok, motivo = scoring.continuous_prose(texto)
    if not ok:
        aviso = _aviso(scoring._MOTIVOS.get(motivo, motivo))
        return p_actual, aviso, aviso
    try:
        p = perfil_mod.desde_muestra(texto, puntuador(), nombre=nombre or "")
        p.guardar(_archivo_lector("perfil.json", peticion))
    # `Exception` y no `(ValueError, OSError)`: lo que lanza torch al quedarse
    # sin memoria es `RuntimeError` -DefaultCPUAllocator: not enough memory- y
    # lo que lanza `safetensors` con una descarga del Hub cortada tampoco
    # desciende de OSError. El invariante de la cabecera no dice "casi nunca".
    except Exception as e:
        return p_actual, _aviso(e), _aviso(e)
    return p, _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas.", _describir(p) + "\n\nGuardado. Ya puedo recomendarte lecturas."


# --- Punto 2: buscador del catalogo --------------------------------------

# La letra que sale al lado de cada libro NO la mide el modelo v4: viene del
# catalogo heredado de la version 1, y el propio documento la declara poco
# fiable (Cuadro 3, limitacion 3). En una demo en vivo eso se nota mucho mas
# que en una tabla: «Sorprendeme» propone un B2 a un lector de 1,20, el lector
# lo abre, pulsa "¿Como de dificil es este capitulo?" y la app le contesta C1.
# La app desmentida por la app cuatro clics despues.
#
# Hasta que el catalogo este remedido entero con el v4 -esta en marcha-, lo
# honesto es decirlo donde se ve la etiqueta, y no solo en el PDF.
NOTA_NIVEL_HEREDADO = (
    "La letra de cada libro es la etiqueta del catálogo, heredada y **sin "
    "medir con el modelo**. Al abrirlo, «¿Cómo de difícil es este capítulo?» "
    "mide el texto de verdad; cuando no coinciden, manda el número del modelo."
)

# Y cuando el catalogo YA esta medido, decir "heredada y sin medir" seria
# mentir en la otra direccion. La letra de un libro medido sale del numero del
# v4 sobre el libro entero (`catalogo.Catalogo`, con `scoring.anchor_cefr`).
# Los cuentos cortos de los corpus libres (StoryWeaver, African Storybook, Let's
# Read, VOA) no se miden uno a uno: van en bloques de 250 palabras o mas por
# fuente y nivel. Decir «entero, capitulo a capitulo» de ellos no era verdad
# (prueba como persona de f4, 14 sep).
NOTA_NIVEL_MEDIDO = (
    "La letra de cada libro sale de **medirlo con el modelo**: los libros, "
    "enteros y capítulo a capítulo; los cuentos cortos, en un bloque con otros "
    "de su misma fuente y nivel. Es orientativa: el modelo ordena bien los "
    "niveles, pero no certifica ninguno. Al abrir un libro largo, la curva dice "
    "dónde se pone cuesta arriba."
)


def _nota_nivel() -> str:
    """La nota al pie de las letras del catalogo, segun de donde salgan."""
    try:
        return NOTA_NIVEL_MEDIDO if getattr(catalogo(), "medido", False) else NOTA_NIVEL_HEREDADO
    except Exception:
        return NOTA_NIVEL_HEREDADO


def _abrible(id_libro) -> bool:
    """¿Se abre en el lector? Gutenberg se descarga; los corpus libres
    (StoryWeaver, African Storybook, VOA...) traen su texto en el catalogo.

    Antes era `startswith("PG")` repetido en cinco sitios: bien mientras solo
    Gutenberg tenia texto, y falso en cuanto el catalogo trajo cuentos libres."""
    try:
        return bool(catalogo().es_abrible(id_libro))
    except Exception:
        pid = str(id_libro or "").upper()
        return pid.startswith("PG") and any(c.isdigit() for c in pid)


def _tabla_libros(libros, vacio: str = "", nota: str = "") -> str:
    """`vacio` SUSTITUYE a la tabla cuando no hay libros; `nota` va al pie
    cuando si los hay.

    Antes era un solo parametro y se pintaba en los dos casos, asi que
    "Sorpendeme" ensenaba diez libros bajo el titulo "Lo mas leido entre 0.88 y
    1.38" y debajo de la tabla "No hay libros etiquetados entre 0.88 y 1.38".
    La pantalla se contradecia sola, y es la segunda del recorrido de la demo.
    """
    if not libros:
        return _aviso(vacio or "Sin resultados.")
    # Tres columnas, no cinco: a 390 px una tabla de cinco se aplasta hasta
    # dejar una palabra por linea. El autor y el nivel caben debajo del titulo.
    abiertos = [_abrible(b.id) for b in libros]
    abribles = sum(abiertos)
    cabecera = []
    # Con el catalogo medido TODOS se abren: decir "los demas no tienen texto"
    # de una lista sin demas es mentirle a quien lo lee.
    if abribles == len(libros):
        cabecera.append("**▸** Se abren aquí mismo, con el botón de debajo "
                        "de la tabla.")
    elif abribles:
        cabecera.append(f"**▸ {abribles} de {len(libros)}** se abren aquí "
                        f"mismo, con el botón de debajo de la tabla. De los "
                        f"demás no hay texto disponible para abrirlos.")
    else:
        cabecera.append("Ninguno de estos se puede abrir aquí: no hay texto "
                        "disponible. Prueba a describirlo de otra manera.")
    # La leyenda va ARRIBA: si va debajo, en un movil el simbolo ▸ queda a una
    # pantalla de distancia de lo que lo explica.
    filas = cabecera + ["", "| | Libro | De qué va |", "|---|---|---|"]
    for b, aqui in zip(libros, abiertos):
        # Sin enlace: tocar el titulo en un movil sacaba de la app a
        # gutenberg.org, cuando lo que se quiere es abrirlo AQUI.
        enlace = b.titulo
        gancho = (b.gancho or "").replace("\n", " ").replace("|", "/")
        if len(gancho) > 70:
            gancho = gancho[:67] + "..."
        ficha = f"**{enlace}**<br><small>{_autor_corto(b.autor)} · {b.nivel}</small>"
        filas.append(f"| {'▸' if aqui else ''} | {ficha} | {gancho} |")
    if nota:
        filas += ["", f"_{nota}_"]
    return "\n".join(filas)


_TITULOS_NOBILIARIOS = {
    "graf", "grafin", "gräfin", "count", "countess", "comte", "comtesse", "conde",
    "condesa", "baron", "baroness", "baronne", "freiherr", "sir", "dame", "lord",
    "lady", "earl", "viscount", "marquis", "marquise", "marqués", "duke", "duchess",
    "prince", "princess", "knyaz", "principe", "príncipe"}


def _autor_corto(autor) -> str:
    """El primer autor, sin fechas ni papel, y «y otros» si hay mas.

    El catalogo medido trae el campo de autor de Gutenberg tal cual, y en una
    antologia son diecisiete nombres con fechas y «[Contributor]»: en la tabla
    del buscador ocupaban media pantalla por libro. Los traductores no cuentan
    como «otros»: «Dostoyevsky, Fyodor» sigue siendo de Dostoyevsky.
    """
    partes = [p.strip() for p in str(autor or "").split(";") if p.strip()]
    if not partes:
        return ""

    def limpio(p):
        p = re.sub(r"\[[^\]]*\]", "", p)
        p = re.sub(r",?\s*\d{3,4}\??\s*-\s*(\d{3,4}\??)?\s*$", "", p.strip())
        # Gutenberg escribe «Apellido, Nombre, titulo»: «Tolstoy, Leo, graf»,
        # «Doyle, Arthur Conan, Sir», y en la cabecera del lector el titulo
        # parecia parte del nombre. Se quitan SOLO titulos reconocidos: quedarse
        # con las dos primeras partes, que era el primer arreglo, se comia
        # «Alger, Horatio, Jr.», «Appleton, Victor, II» y partia un parentesis
        # («Allen, George (Vicar of St. Thomas's, Islington)»). Lo encontro Codex.
        trozos = [t.strip() for t in p.split(",")]
        while len(trozos) > 2 and trozos[-1].lower().rstrip(".") in _TITULOS_NOBILIARIOS:
            trozos.pop()
        p = ", ".join(trozos)
        return p.strip(" ,").replace("|", "/")

    otros = [p for p in partes[1:] if "translator" not in p.lower()]
    return limpio(partes[0]) + (" y otros" if otros else "")


def _opciones_libros(libros):
    """Los resultados, listos para abrirse en el lector con un clic.

    Los de StoryWeaver se listan igual pero marcados: no estan en Gutenberg y
    no hay de donde bajarlos. Mas vale decirlo en la etiqueta que dejar que el
    usuario lo descubra al pulsar.
    """
    # **Solo los que se pueden abrir.** Antes se listaban todos, marcando los
    # de StoryWeaver como "no descargable", y como son 1.049 de los 1.197 del
    # catalogo, el desplegable se llenaba de opciones inservibles: habia que
    # rebuscar entre ellas el unico libro que si se abria. Un desplegable
    # donde casi nada funciona es peor que uno corto donde todo funciona.
    opciones = [(f"{b.titulo} — {_autor_corto(b.autor)} ({b.nivel})", b.id)
                for b in libros if _abrible(b.id)]
    return gr.update(choices=opciones,
                     value=opciones[0][1] if opciones else None)


def _buscar(p, consulta, ajustar, n):
    try:
        cat = catalogo()
    except (FileNotFoundError, OSError) as e:
        return _aviso(e), gr.update(choices=[], value=None)
    nivel = p.nivel if (ajustar and p is not None) else None
    # Vaciar la casilla "¿Cuántos te propongo?" hace que `gr.Number` mande
    # None, y el `int(None)` de dentro del try le ensenaba al lector un
    # "int() argument must be a string... not 'NoneType'". No es un aviso: es
    # un error de Python en la cara de quien solo borro un numero.
    n = int(n or 10)
    try:
        libros, aviso = cat.buscar(consulta, nivel_lector=nivel, n=n)
    except Exception as e:                      # red o modelo de embeddings
        return _aviso(e), gr.update(choices=[], value=None)
    cabecera = ""
    if ajustar and p is None:
        cabecera = "_Sin perfil todavía: busco solo por parecido._\n\n"
    # Aqui el mismo texto vale en los dos huecos: `catalogo.buscar` devuelve
    # "ningun libro supera el umbral" cuando la lista sale vacia y "se
    # descartaron N por parecido bajo" cuando trae resultados, nunca las dos.
    nota = _nota_nivel()
    pie = f"{aviso} {nota}" if aviso else nota
    return (cabecera + _tabla_libros(libros, vacio=aviso, nota=pie),
            _opciones_libros(libros))


# Bajo la raiz configurable, no bajo `~` a pelo: si el Space monta un disco
# persistente, los libros descargados sobreviven al reinicio y no hay que
# volver a pedirlos a gutenberg.org.
RUTA_LIBROS = BASE_DATOS_LECTOR / "libros"


def _esta_cacheado(id_libro: str) -> bool:
    """¿Este libro ya esta en disco? Entonces abrirlo no sale a la red.

    Se usa para no gastarle una ficha del tope de descargas a quien vuelve a
    abrir un libro que ya tiene. La comprobacion es la misma que hace
    `_descargar_gutenberg` antes de pedir nada.
    """
    pid = str(id_libro or "").strip()
    # Un libro de un corpus libre trae el texto en el propio catalogo: abrirlo
    # no sale a la red, asi que no gasta ficha del tope. Y sin este desvio,
    # "SWV369" sacaba sus digitos y preguntaba por el pg369 de Gutenberg.
    if pid and not pid.upper().startswith("PG"):
        return _abrible(pid)
    num = "".join(c for c in pid if c.isdigit())
    if not num:
        return False
    for ext in (".epub", ".txt"):
        p = RUTA_LIBROS / f"pg{num}{ext}"
        try:
            if p.exists() and p.stat().st_size > 2000:
                return True
        except OSError:
            return False
    return False


def _descargar_gutenberg(id_libro: str) -> str:
    """Baja un libro de Project Gutenberg y devuelve la ruta local.

    Se cachea en disco: el mismo libro no se vuelve a bajar nunca. Existe
    porque sin esto el bucle de la app estaba roto -el buscador encontraba el
    libro y despedia al lector a gutenberg.org a descargarlo y volver a
    subirlo, justo en el momento de mas ganas de leer.
    """
    import urllib.request

    texto_id = str(id_libro).strip()
    num = "".join(c for c in texto_id if c.isdigit())
    # Los corpus libres (StoryWeaver, African Storybook, VOA, Let's Read) no se
    # descargan: su texto, con la atribucion que exige la licencia, viene en
    # corpus_abierto.parquet. Se escribe una vez como .txt para que el lector lo
    # abra por el mismo camino que un libro de Gutenberg.
    if not texto_id.upper().startswith("PG"):
        try:
            abierto = catalogo().texto_abierto(texto_id)
        except Exception:
            abierto = None
        if abierto and abierto.get("texto"):
            RUTA_LIBROS.mkdir(parents=True, exist_ok=True)
            destino = RUTA_LIBROS / f"{re.sub(r'[^0-9A-Za-z]', '', texto_id).lower()}.txt"
            # Se reescribe si el texto del catalogo cambio (una correccion o una
            # atribucion nueva); antes cualquier copia no vacia valia para
            # siempre y el lector seguia ensenando la version vieja (auditoria de
            # Codex, 12 de septiembre de 2026). Son cuentos cortos: comparar es barato.
            try:
                vigente = destino.read_text(encoding="utf-8") if destino.exists() else None
            except OSError:
                vigente = None
            if vigente != abierto["texto"]:
                destino.write_text(abierto["texto"], encoding="utf-8")
            return str(destino)
    if not texto_id.upper().startswith("PG") or not num:
        raise ValueError(
            "De este libro no hay texto disponible para abrirlo aquí (no es de "
            "Project Gutenberg ni de un corpus libre). Consíguelo y súbelo con "
            "el selector de archivo.")

    RUTA_LIBROS.mkdir(parents=True, exist_ok=True)
    destino = RUTA_LIBROS / f"pg{num}.epub"
    # Se miran las DOS extensiones. Cuando el epub falla se baja el `.txt`, y
    # esta comprobacion solo miraba el `.epub`: un libro ya descargado como
    # texto no acertaba nunca en la cache y se volvia a pedir a Gutenberg las
    # tres veces, cada vez que el lector lo abria.
    #
    # Y el `.txt` va PRIMERO, que no es por gusto: es el texto con el que se
    # midio el catalogo en Colab, y solo con el mismo formato los capitulos del
    # lector son los de la curva medida. Medido el 12 de septiembre de 2026: el
    # EPUB de *Pride and Prejudice* trae 15 secciones donde el `.txt` trae 61
    # capitulos, y con el EPUB no se le puede sugerir un capitulo concreto. El
    # lector pinta bien el `.txt`: une las lineas cortadas y parte por parrafos.
    # Un EPUB que ya estuviera guardado se sigue usando si el `.txt` no llega.
    txt = destino.with_suffix(".txt")
    if txt.exists() and txt.stat().st_size > 2000:
        return str(txt)
    epub = destino.with_suffix(".epub")

    fuentes = [
        (f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt", ".txt"),
        (f"https://www.gutenberg.org/ebooks/{num}.txt.utf-8", ".txt"),
        (f"https://www.gutenberg.org/ebooks/{num}.epub.noimages", ".epub"),
    ]
    ultimo = None
    for url, ext in fuentes:
        if ext == ".epub" and epub.exists() and epub.stat().st_size > 2000:
            return str(epub)          # sin `.txt`, el EPUB que ya habia vale
        try:
            pedido = urllib.request.Request(
                url, headers={"User-Agent": "LiteraLevel/1.0 (proyecto educativo)"})
            with urllib.request.urlopen(pedido, timeout=45) as r:
                datos = r.read()
            if len(datos) < 2000:
                raise ValueError("el archivo llegó vacío")
            final = destino.with_suffix(ext)
            final.write_bytes(datos)
            return str(final)
        except Exception as e:
            ultimo = e
    raise ConnectionError(f"No pude descargarlo de Gutenberg: {ultimo}")


def _abrir_del_catalogo(id_libro, peticion: gr.Request = None):
    """Abre en el lector un libro elegido en el buscador, sin salir de la app.

    Es generadora y su primer valor va a un aviso de la pestana del BUSCADOR,
    no de la de lectura. Descargar de Gutenberg puede tardar, y antes el
    usuario pulsaba el boton y no veia nada: ni espera, ni error, porque todas
    las salidas estaban en una pestana a la que no se saltaba si algo fallaba.
    """
    # El desplegable de capitulos NO SE TOCA mientras esto trabaja. Vaciarlo
    # era el recuadro rojo de la auditoria 16: si ya hay un libro abierto -y lo
    # hay siempre que se haya leido algo antes, porque `_reanudar` lo repinta
    # al cargar-, quitarle las opciones a un componente que conserva su valor
    # hace que Gradio pinte «Value: 1 is not in the list of choices: []» encima
    # del libro. Reproducido y aislado en el Space: con marcapaginas sale, sin
    # el no. Y ademas vaciarlo estaba mal por si solo: pulsar «Leerlo ahora»
    # sin elegir nada te borraba el indice del libro que estabas leyendo.
    sin_tocar = gr.update()
    # Y mientras trabaja NO SE TOCA EL LECTOR ENTERO, no solo el desplegable.
    # Antes esto ponia el libro a `None` y borraba el texto: pulsar «Leerlo
    # ahora» sin elegir nada, o que se cayera la descarga, te dejaba sin el
    # libro que estabas leyendo y con el desplegable lleno de sus capitulos.
    # Mandos vivos sobre un lector vacio. `gr.skip()` deja cada salida como
    # esta; lo unico que cambia es el aviso, que es lo que hay que decir.
    quieto = (gr.skip(), sin_tocar, gr.skip(), gr.skip(), gr.Tabs())
    if not id_libro:
        yield quieto[:3] + (gr.skip(), gr.Tabs(),
                            "Elige un libro de la lista.")
        return
    # Esta SI lleva tope por hora, aunque no cueste dinero, y no contradice la
    # regla de la cabecera -"lo que no cuesta dinero no se limita: es local"-
    # porque esto no es local: son hasta tres peticiones a gutenberg.org con 45
    # s de plazo cada una, y mientras esperan ocupan uno de los ocho huecos de
    # la cola. Ocho ids distintos sin cache dejan la aplicacion sin huecos
    # durante minutos, y ese es el unico camino que puede dejar sin servicio a
    # los demas sin gastar un centimo. El tope es alto a proposito: nadie abre
    # veinte libros nuevos en una hora leyendo, y los ya descargados no pasan
    # por aqui -aciertan en la cache de disco antes-.
    if not _esta_cacheado(id_libro) and not _dentro_del_limite(
            peticion, "descargas", LIMITE_DESCARGAS_HORA):
        yield quieto[:3] + (gr.update(), gr.Tabs(), _aviso(
            f"Has abierto {LIMITE_DESCARGAS_HORA} libros nuevos en esta hora y "
            f"cada descarga tarda. Espera "
            f"{_cuanto_falta(_minutos_para_la_siguiente('descargas', peticion))[3:]}, o "
            f"sigue leyendo los que ya tienes en «Mis libros»."))
        return
    yield quieto[:3] + (gr.update(), gr.Tabs(),
                        "Descargando de Project Gutenberg… la primera vez "
                        "puede tardar; después queda guardado.")
    try:
        ruta = _descargar_gutenberg(id_libro)
    # OSError incluido: `RUTA_LIBROS.mkdir(...)` de la cache queda fuera del
    # `try` interno, asi que un problema de disco -carpeta ocupada por un
    # archivo, permisos, disco lleno- salia hacia Gradio. Era el unico error de
    # disco que un manejador dejaba escapar.
    except (ValueError, ConnectionError, OSError) as e:
        yield quieto[:3] + (gr.update(), gr.Tabs(), _aviso(e))
        return
    libro, upd, html, resumen = _abrir(ruta, peticion)
    if libro is None:
        # Tampoco aqui se tira el lector. Que el libro NUEVO no se pueda abrir
        # no es razon para dejarte sin el que estabas leyendo; se dice lo que
        # ha pasado y se queda todo como estaba.
        yield gr.skip(), sin_tocar, gr.skip(), gr.skip(), gr.Tabs(), _aviso(resumen)
        return
    yield libro, upd, html, resumen, gr.Tabs(selected="leer"), ""


# La holgura con la que "Sorprendeme" busca por nivel. NO es un numero nuevo:
# se lee de `perfil`, que es donde vive el unico, porque `perfil.describir` lo
# anuncia en la pestana "Mi nivel" antes de que aqui se filtre nada. Tenerlo
# dos veces ya salio mal dos veces: primero el rotulo de esta pestana anunciaba
# `rango_recomendado` -nivel-0,10 a nivel+0,15- mientras `por_nivel` filtraba
# con 0,25 simetrico; se arreglo aqui y quedo la pestana de al lado prometiendo
# "entre 1.03 y 1.28" mientras esta decia "entre 0.88 y 1.38" del mismo lector.
HOLGURA_POR_NIVEL = perfil_mod.HOLGURA


def _recomendar(p, n):
    vacio = gr.update(choices=[], value=None)
    if p is None:
        return "Primero fija tu nivel en la pestaña **Mi nivel**.", vacio
    # `gr.Number` vacio llega como None, y el `int(None)` de dentro del try
    # devolvia al lector un "int() argument must be... not 'NoneType'".
    n = int(n or 10)
    try:
        libros = catalogo().por_nivel(p.nivel, holgura=HOLGURA_POR_NIVEL,
                                      n=n)
    except Exception as e:
        return _aviso(e), vacio

    # NUNCA dejar al principiante en un callejon. Del catalogo heredado solo
    # 148 de 1.197 libros se pueden abrir aqui -los de Project Gutenberg-, y
    # estan repartidos asi:
    #
    #     A1  0 de 723      B1  10 de 69      C1  25 de 53
    #     A2  2 de 185      B2  12 de 52      C2  99 de 115
    #
    # O sea que un lector A1 recibia diez titulos y un desplegable VACIO: los
    # 723 libros de su nivel son de StoryWeaver y no hay de donde bajarlos. El
    # camino de quien mas ayuda necesita terminaba en nada. La causa no es un
    # error de programacion, es que Project Gutenberg apenas tiene material
    # elemental, y el catalogo lo rellenaba con libros que no puede servir.
    #
    # Mientras la remedicion del catalogo no termine, esto al menos ofrece lo
    # mas facil que SI se puede abrir, y lo dice en vez de disimularlo.
    rescate = ""
    if libros and not any(_abrible(b.id) for b in libros):
        try:
            faciles = [b for b in catalogo().por_nivel(p.nivel, holgura=3.0, n=200)
                       if _abrible(b.id)]
        except Exception:
            faciles = []
        if faciles:
            faciles.sort(key=lambda b: scoring.ANCHORS.index(b.nivel)
                         if b.nivel in scoring.ANCHORS else 9)
            libros = faciles[:int(n)]
            rescate = ("Ninguno de los libros de tu nivel se puede abrir aquí: "
                       "son de StoryWeaver y no hay de dónde descargarlos. "
                       "**Estos son los más fáciles que sí puedes leer ahora "
                       "mismo**, aunque queden por encima de tu nivel. Ve "
                       "despacio y usa el doble clic sobre las palabras.\n\n")

    # El rango que se ANUNCIA tiene que ser el que se uso para filtrar. Antes
    # aqui se leia `p.rango_recomendado`, que es otra cosa -el rango de reto
    # del lector- y no lo que `por_nivel` acababa de aplicar.
    lo = max(0.0, p.nivel - HOLGURA_POR_NIVEL)
    hi = min(2.0, p.nivel + HOLGURA_POR_NIVEL)
    # Los niveles del catalogo son seis valores discretos, asi que un lector
    # que salga del cuestionario en 0.62 puede no tener NINGUN libro dentro de
    # la holgura. Decirlo y decir que hacer, en vez del generico "Sin
    # resultados" que dejaba en un callejon.
    si_no_hay = (f"No hay libros etiquetados entre {lo:.2f} y {hi:.2f}. Prueba "
                 f"a describir lo que te apetece leer en el buscador de "
                 f"arriba: ahí sí se ajusta a tu nivel sin exigir una "
                 f"coincidencia exacta.")
    if rescate:
        return (rescate + _tabla_libros(libros, vacio=si_no_hay,
                                        nota=_nota_nivel()),
                _opciones_libros(libros))
    return (f"Lo más leído entre **{lo:.2f}** y **{hi:.2f}**:\n\n"
            + _tabla_libros(libros, vacio=si_no_hay, nota=_nota_nivel()),
            _opciones_libros(libros))


# --- Punto 3: lector, y punto 4 dentro de el ------------------------------

# Tres decisiones de este bloque no son de gusto, y conviene dejarlas dichas
# porque las tres estaban al reves y las tres las sufrio una lectora real.
#
# 1. SIN `max-height` ni `overflow-y`. Antes el lector era una caja con su
#    propio desplazamiento dentro de una pagina que tambien se desplaza. En el
#    movil eso es una loteria: el dedo unas veces mueve el texto y otras la
#    pagina, segun donde caiga, y no hay forma de saberlo de antemano. Es el
#    candidato numero uno a lo que Esmeralda, 15 anos, describio como "esta
#    bien dificil de usar en celular". El texto ahora fluye con la pagina.
#
# 2. `max-width: 66ch` en los parrafos. Sin tope, el lector ocupaba el ancho
#    entero del bloque: en un portatil de 1440 px con Georgia a 19 px son del
#    orden de 130 caracteres por linea. Al ojo le cuesta encontrar el principio
#    del renglon siguiente cuando el salto es tan largo.
#
# 3. SIN `text-align: justify`. El criterio 1.4.8 de las WCAG lo desaconseja
#    explicitamente -"Text is not justified"- porque los rios de espacio en
#    blanco despistan la vista. En una columna estrecha de movil el problema
#    empeora, no mejora. Quitado el justificado, `hyphens` deja de hacer falta;
#    y ademas Gradio sirve la pagina con lang="en", asi que partia las palabras
#    con reglas inglesas.
_CSS_LECTOR = """<style>
#ll-lector{padding:1.4rem 1.8rem;
  /* El gris clavado de antes -rgba(128,128,128,.28)- le ganaba al
     `border-color:var(--ll-borde)` que pone el bloque de la paleta, porque
     este `border` abreviado va despues y lo reescribe entero. */
  border:1px solid var(--ll-borde);border-radius:10px;
  font-family:Georgia,"Iowan Old Style","Times New Roman",serif;
  font-size:var(--ll-lectura, 19px);line-height:1.75;
  /* Era `color:inherit`, que gana al `--ll-lector-texto` de mas arriba y
     dejaba esa variable muerta en las cinco paletas. Heredaba `--ll-texto`,
     asi que se leia; pero la paleta declara un color propio para el cuerpo
     del libro y era el que no se usaba nunca. */
  /* `!important` porque `gr.HTML` pinta esto dentro de un `div.prose`, y la
     regla `.prose *{color:var(--ll-texto) !important}` de la paleta -la que
     sostiene el arreglo del critico C1- le ganaba. `--ll-lector-texto` volvia
     a ser codigo muerto: medido en el navegador, el color pintado era
     `--ll-texto`. Un `#id` con `!important` gana por especificidad sin tocar
     la regla de `.prose`, que sigue haciendo su trabajo en todo lo demas. */
  color:var(--ll-lector-texto) !important;
  text-align:left}
#ll-lector p{color:var(--ll-lector-texto) !important}
#ll-lector p{margin:0 0 1.05em;max-width:66ch}
#ll-lector p:first-child{margin-top:0}
/* El amarillo estaba CLAVADO aqui, y este bloque va despues del de arriba
   con la misma especificidad, asi que ganaba el amarillo y `--ll-seleccion`
   era codigo muerto en las cinco paletas. Sobre las tres claras el resaltado
   quedaba en 1,20-1,22:1, o sea invisible: y seleccionar una palabra es COMO
   SE CONSULTA EL DICCIONARIO, el gesto central de la aplicacion. */
#ll-lector::selection,#ll-lector p::selection{
  background:var(--ll-seleccion);color:var(--ll-lector-texto)}
#ll-lector .ll-vacio{font-style:italic;opacity:.78;text-align:left}
@media (max-width:640px){
  #ll-lector{padding:1.1rem 1.15rem;font-size:var(--ll-lectura, 18px)}
  #ll-lector p{max-width:none}
}
</style>"""


def _html_lectura(texto: str) -> str:
    """El capitulo como prosa legible, no como volcado en un textarea."""
    if not texto:
        return _CSS_LECTOR + ('<div id="ll-lector"><span class="ll-vacio">'
                              'Abre un libro y elige un capitulo.</span></div>')
    parrafos = [" ".join(t.split()) for t in re.split(r"\n\s*\n", texto)]
    cuerpo = "".join(f"<p>{_html.escape(t)}</p>" for t in parrafos if t)
    return _CSS_LECTOR + f'<div id="ll-lector">{cuerpo}</div>'


# Doble clic (o arrastrar) sobre una palabra del lector la copia a la caja de
# consulta. Se engancha a document una sola vez y sobrevive a que Gradio
# vuelva a dibujar el capitulo.
# La identidad del lector, puesta por el navegador y guardada en
# `localStorage`. Se elige `localStorage` y no `sessionStorage` a proposito:
# el segundo se borra al cerrar la pestana, y lo que promete la aplicacion es
# que "Mis libros" siga ahi manana, no solo hasta que cierres.
#
# `crypto.randomUUID` no existe en contextos inseguros ni en navegadores
# viejos, asi que hay respaldo. Y todo va en try/catch: en una ventana privada
# o con las cookies bloqueadas, `localStorage` LANZA al tocarlo, y si eso
# reventara el `demo.load` la pagina entera arrancaria en error. Sin
# identidad, `_dir_lector` cae en el `session_hash` de siempre.
JS_IDENTIDAD = r"""
() => {
  const CLAVE = 'literalevel_lector';
  try {
    let id = localStorage.getItem(CLAVE);
    if (!id) {
      id = (crypto && crypto.randomUUID)
           ? crypto.randomUUID()
           : String(Date.now()) + '-' + Math.random().toString(36).slice(2);
      localStorage.setItem(CLAVE, id);
    }
    return id;
  } catch (e) {
    return '';
  }
}
"""

# Al cambiar de capitulo, arriba del texto. Se descuenta la barra de pestanas,
# que va fija arriba y taparia las primeras lineas.
#
# Subir UNA vez no basta, medido en el navegador: el boton solo cambia el
# numero de capitulo y el texto nuevo llega despues, por `cap.change`. Al
# sustituirse, el navegador recoloca la pagina para no mover lo que se estaba
# viendo (scroll anchoring) y deshacia el salto: se quedaba a media altura del
# capitulo nuevo. Asi que sube, espera a que el texto del lector cambie -como
# mucho 6 s- y vuelve a subir, sin animacion para que nada la interrumpa.
JS_AL_TEXTO = r"""
() => {
  // Hay mas de un #ll-lector en la pagina (el de otras pestanas, oculto) y
  // `getElementById` devolvia el primero, invisible: se tomaba su posicion,
  // que es 0, y no se movia nada. Vale el que se ve.
  const lector = () => [...document.querySelectorAll('#ll-lector')]
    .find(e => e.offsetParent !== null) || null;
  const ir = () => {
    const el = lector();
    if (!el) return;
    el.scrollTop = 0;
    const barra = document.querySelector('.tab-wrapper');
    const alto = barra ? barra.getBoundingClientRect().height : 0;
    const y = el.getBoundingClientRect().top + window.scrollY - alto - 12;
    window.scrollTo({ top: Math.max(0, y), behavior: 'auto' });
  };
  const inicio = () => {
    const el = lector();
    return el ? el.textContent.slice(0, 300) : '';
  };
  // Tres cosas que encontro Codex. (1) Al vencer el plazo SIN que cambie el
  // texto -«Siguiente» en el ultimo capitulo- ya no se desplaza: antes subia
  // 6 s despues y sacaba de su sitio a quien ya estaba leyendo. (2) Una
  // pulsacion nueva cancela la espera de la anterior. (3) Si el lector toca,
  // rueda o teclea mientras se espera, manda el: se deja de esperar.
  if (window.__llAlTexto) window.__llAlTexto();
  const antes = inicio();
  ir();
  let vueltas = 0;
  let reloj = null;
  const gestos = ['wheel', 'touchstart', 'keydown'];
  const parar = () => {
    clearInterval(reloj);
    gestos.forEach(t => window.removeEventListener(t, parar));
    if (window.__llAlTexto === parar) window.__llAlTexto = null;
  };
  gestos.forEach(t => window.addEventListener(t, parar, { passive: true }));
  window.__llAlTexto = parar;
  reloj = setInterval(() => {
    if (inicio() !== antes) {
      parar();
      ir();
      setTimeout(ir, 250);
    } else if (++vueltas > 40) {
      parar();
    }
  }, 150);
}
"""

# «Otra frase» deja la caja vacia; esto la pone a la vista. Sin `focus()`: en el
# movil abriria el teclado encima de la frase que se quiere traer.
JS_A_LA_FRASE = r"""
() => {
  const el = document.getElementById('ll-frase');
  if (!el) return;
  const barra = document.querySelector('.tab-wrapper');
  const alto = barra ? barra.getBoundingClientRect().height : 0;
  const y = el.getBoundingClientRect().top + window.scrollY - alto - 12;
  window.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
}
"""

JS_SELECCION = r"""
() => {
  if (window.__llSel) return;
  window.__llSel = true;

  // Antes esto solo escuchaba 'mouseup', y por eso en el movil no pasaba
  // nada: al seleccionar una palabra con el dedo, iOS **no** emite mouseup.
  // Lo unico que llega de forma fiable en tactil es 'selectionchange', que
  // ademas se dispara muchas veces mientras se arrastra, asi que hay que
  // esperar a que la seleccion se estabilice.
  var espera = null;

  function enElLector(nodo) {
    if (!nodo) return false;
    var el = nodo.nodeType === 1 ? nodo : nodo.parentElement;
    return !!(el && el.closest && el.closest('#ll-lector'));
  }

  function capturar() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    var txt = (sel.toString() || '').trim();
    // Una palabra o un phrasal verb corto. Si es mas, se esta subrayando
    // para leer, no para consultar.
    if (!txt || txt.split(/\s+/).length > 4 || txt.length > 40) return;
    if (!enElLector(sel.anchorNode)) return;
    var caja = document.querySelector('#ll-palabra textarea, #ll-palabra input');
    if (!caja || caja.value === txt) return;
    // Svelte no se entera si se asigna .value a secas: hay que usar el setter
    // nativo del prototipo y despues emitir 'input'.
    var proto = caja.tagName === 'TEXTAREA' ? HTMLTextAreaElement : HTMLInputElement;
    var setter = Object.getOwnPropertyDescriptor(proto.prototype, 'value').set;
    setter.call(caja, txt);
    caja.dispatchEvent(new Event('input', { bubbles: true }));
    // En un movil la caja queda fuera de pantalla, encima del lector: sin
    // esto el usuario selecciona una palabra y no ve que haya pasado nada.
    try { caja.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
    catch (e) { caja.scrollIntoView(); }
  }

  function programar(ms) {
    clearTimeout(espera);
    espera = setTimeout(capturar, ms);
  }

  // Tactil: la seleccion tarda en asentarse y las manijas de iOS siguen
  // moviendola un rato.
  document.addEventListener('selectionchange', function () { programar(400); });
  document.addEventListener('touchend', function () { programar(400); });
  // Raton: llega enseguida y no hace falta esperar.
  document.addEventListener('mouseup', function () { programar(10); });
}
"""


def _mover(libro, idx, paso):
    """Capitulo anterior / siguiente, sin salirse del libro."""
    if libro is None or idx is None:
        return gr.update()
    # `int(idx)` pelado lanzaba ValueError con cualquier indice que no fuera un
    # numero. `_capitulo` y `_medir` ya pasaban por `_cap`, que lo valida; este
    # se habia quedado fuera.
    try:
        actual = int(idx)
    except (TypeError, ValueError):
        return gr.update()
    return gr.update(value=max(0, min(len(libro.capitulos) - 1, actual + paso)))


# Titulos que en un epub casi siempre son paratexto y no la obra en si.
# `RELLENO_RE` y el filtro de capitulos viven en `ficha.py`: el precalculo
# masivo en Colab necesita el MISMO filtro que la app.
_RELLENO_RE = ficha.RELLENO_RE


# Se conserva por compatibilidad con lo ya guardado en local y con las
# pruebas; el marcapaginas real se resuelve por lector con `_ruta_sesion`.
RUTA_SESION = BASE_DATOS_LECTOR / "sesion.json"


def _ruta_sesion(peticion=None) -> Path:
    if not EN_LA_NUBE:
        return RUTA_SESION
    return Path(_archivo_lector("sesion.json", peticion))


def _guardar_sesion(ruta_libro: str, titulo: str, capitulo: int,
                    peticion=None) -> None:
    """Deja constancia de por donde ibas. Nunca estorba si falla."""
    destino = _ruta_sesion(peticion)
    try:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(
            {"ruta": str(ruta_libro), "titulo": titulo, "capitulo": int(capitulo)},
            ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass          # no poder guardar el marcapaginas no puede romper la lectura


def _leer_sesion(peticion=None) -> dict | None:
    try:
        d = json.loads(_ruta_sesion(peticion).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    # `isinstance` y no solo `d.get`: un `sesion.json` que sea JSON VALIDO pero
    # no un objeto -`[]`, `"hola"`, `3`- pasaba el `except` y reventaba en el
    # `.get` con un AttributeError. Y esto lo llama `_reanudar`, que corre en
    # `demo.load`, o sea que la pagina entera arrancaba con error para ese
    # lector hasta que alguien borrara el archivo a mano.
    if not isinstance(d, dict):
        return None
    # Y la `ruta` tiene que ser una CADENA. Con `d.get("ruta")` bastaba para que
    # `{"ruta": ["x"]}` -JSON valido, objeto, con la clave puesta- llegara a
    # `os.path.exists` y lanzara TypeError. Mismo estropicio que el de arriba y
    # en el mismo sitio: `_reanudar` corre en `demo.load`, asi que la pagina
    # entera arrancaba en error para ese lector.
    if not isinstance(d.get("ruta"), str):
        return None
    return d if os.path.exists(d["ruta"]) else None


def _perfil_inicial(peticion: gr.Request = None):
    """El perfil de ESTE lector, al abrir la app.

    No puede resolverse al construir la interfaz: eso ocurre una vez por
    proceso, y desplegada la app hay un proceso para todos los visitantes.
    Quien entrara segundo se encontraria con el nombre y el nivel del primero.
    """
    p = perfil_mod.cargar(_archivo_lector("perfil.json", peticion))
    return p, _describir(p)


def _reanudar(peticion: gr.Request = None):
    """Al abrir la app, vuelve al libro y al capitulo donde lo dejaste.

    Es la mecanica de retencion mas barata que hay: no premia ni castiga, solo
    evita que quien vuelve tenga que reconstruir donde estaba. Si el archivo
    ya no existe, no se dice nada y se empieza limpio.

    Desplegada, el marcapaginas es el de ESTA sesion de navegador. Si no lo
    fuera, cada visitante abriria la app en el libro del anterior.
    """
    vacio = (None, gr.update(choices=[], value=None), _html_lectura(""), "",
             gr.Tabs())
    s = _leer_sesion(peticion)
    if not s:
        return vacio
    libro, upd, html, resumen = _abrir(s["ruta"], peticion)
    if libro is None:
        return vacio
    idx = s.get("capitulo", 0)
    if not (isinstance(idx, int) and 0 <= idx < len(libro.capitulos)):
        idx = upd["value"]
    c = libro.capitulos[idx]
    aviso = (f"**{libro.titulo}** — seguías en el capítulo {idx + 1} de "
             f"{len(libro.capitulos)}: _{c.titulo}_.")
    return (libro, gr.update(choices=upd["choices"], value=idx),
            _html_lectura(c.texto), aviso, gr.Tabs(selected="leer"))


def _limpiar_consulta():
    """Lo que hay que borrar al abrir un libro nuevo.

    Miguel abrio The Brothers Karamazov y se encontro abajo la ficha de
    "strip", una palabra que habia consultado en el libro ANTERIOR. Parecia
    que la app le habia devuelto al vocabulario. Un libro nuevo empieza sin
    restos del anterior.
    """
    return ("", gr.update(value=""), gr.update(value=""), "",
            gr.update(value=None, visible=False))


def _abrir(archivo, peticion: gr.Request = None):
    vacio = gr.update(choices=[], value=None)
    if not archivo:
        return None, vacio, _html_lectura(""), "Sube un `.epub`, `.pdf` o `.txt`."
    try:
        libro = reader.cargar(archivo)
    except Exception as e:
        # A proposito se atrapa todo: pypdf lanza PdfStreamError y zipfile
        # BadZipFile, que no descienden de OSError. Un archivo corrupto no
        # puede tumbar la interfaz, y el nombre de la excepcion ya orienta.
        return None, vacio, _html_lectura(""), _aviso(
            f"No pude abrir el archivo ({type(e).__name__}): {e}")
    if not libro.capitulos:
        return None, vacio, _html_lectura(""), _aviso(
            "El archivo no tiene texto legible.")
    # De que libro del catalogo es, si lo es: `pg1342.txt` -> PG1342. Se apunta
    # aqui porque es el punto por el que pasan los tres caminos que abren un
    # libro -el buscador, «retomar» y «Mis libros»-, y las sugerencias por
    # capitulo lo necesitan para leer la curva medida del catalogo.
    m_pg = re.search(r"(?i)\bpg(\d+)\.(?:txt|epub)$", os.path.basename(str(archivo)))
    libro.id_catalogo = f"PG{m_pg.group(1)}" if m_pg else None
    # Los corpus libres se abren como `swv369.txt`, `asb0141.txt`, `voa7997203.txt`
    # o `lrd<uuid>.txt` (ver _descargar_gutenberg): tambien son del catalogo.
    if not m_pg:
        m_ext = re.search(r"(?i)\b((?:swv|asb|voa|lrd)[0-9a-z]+)\.txt$",
                          os.path.basename(str(archivo)))
        libro.id_catalogo = m_ext.group(1).upper() if m_ext else None
    # El .txt de Gutenberg no trae metadatos: la cabecera decia "pg2554.txt —
    # autor desconocido" de un libro cuyo titulo y autor estan en el catalogo.
    # El TITULO solo se cambia en la cabecera: `libro.titulo` entra en la clave
    # de los analisis guardados y en la sesion, y tocarlo los dejaria huerfanos.
    titulo_visible = libro.titulo
    if libro.id_catalogo:
        try:
            df = catalogo().df
            fila = df.loc[df["id"].astype(str) == libro.id_catalogo]
            if len(fila):
                if re.fullmatch(r"(?i)(?:pg\d+|(?:swv|asb|voa|lrd)[0-9a-z]+)(\.\w+)?",
                                str(libro.titulo or "")):
                    titulo_visible = str(fila.iloc[0]["title"]) or libro.titulo
                libro.autor = libro.autor or str(fila.iloc[0]["author"])
        except Exception:
            pass
    # El recuento va en la etiqueta porque muchos epub traen los titulos
    # repetidos ("I", "II"...) en dos partes y ademas portadillas sueltas:
    # sin las palabras no hay forma de distinguir el capitulo del relleno.
    opciones = _opciones_capitulos(libro)

    # No abrir en la portadilla. Solo el recuento de palabras no basta: el
    # apendice de "Notes from a Dead House" trae 2,143 y aparece el segundo,
    # por delante del capitulo I. Asi que ademas se descarta por titulo.
    def _cuerpo(c):
        return c.palabras >= 500 and not _RELLENO_RE.search(c.titulo)

    inicial = next((i for i, c in enumerate(libro.capitulos) if _cuerpo(c)),
                   next((i for i, c in enumerate(libro.capitulos)
                         if c.palabras >= 500), 0))

    # El MISMO recuento que la ficha de abajo. Aqui se pintaba
    # `libro.palabras` -crudo, con portadilla y licencia dentro- y tres lineas
    # mas abajo la ficha pinta el descontado: en *Metamorphosis* salia
    # "25.077 palabras" arriba y "21.938 palabras" debajo, en la misma
    # pantalla. Dos cifras distintas de lo mismo a tres lineas de distancia es
    # lo primero que alguien compara, y no hay explicacion que lo salve.
    try:
        palabras = ficha.caracteristicas(libro).palabras or libro.palabras
    except Exception:
        palabras = libro.palabras      # la cabecera nunca puede tumbar el libro
    # El singular importa: con un .txt de un capitulo la cabecera decia
    # "1 capítulos" y la ficha, tres lineas mas abajo, "1 capítulo".
    n_caps = len(libro.capitulos)
    resumen = (f"**{titulo_visible}** — {_recortar(_autor_corto(libro.autor), 80) or 'autor desconocido'} · "
               f"{n_caps} {'capítulo' if n_caps == 1 else 'capítulos'} · "
               f"{ficha.miles(palabras)} palabras")
    if inicial:
        resumen += (f"\n\n_Empiezo en el capítulo {inicial + 1}: "
                    f"los anteriores son portadilla._")
    _guardar_sesion(archivo, libro.titulo, inicial, peticion)
    biblioteca.anotar(ruta_libro=archivo, titulo=libro.titulo,
                      autor=libro.autor, capitulos=len(libro.capitulos),
                      capitulo=inicial, palabras=libro.palabras,
                      ruta=_archivo_lector("biblioteca.json", peticion))
    return (libro, gr.update(choices=opciones, value=inicial),
            _html_lectura(libro.capitulos[inicial].texto), resumen)


def _opciones_capitulos(libro) -> list:
    """Las etiquetas de los capitulos, en UN solo sitio.

    Las usan el desplegable de arriba y el indice de abajo, y tienen que decir
    exactamente lo mismo: son dos mandos del mismo estado. El recuento de
    palabras va en la etiqueta porque muchos epub repiten los titulos ("I",
    "II") en dos partes y traen portadillas sueltas, y sin las palabras no hay
    forma de saber cual es el capitulo de verdad.
    """
    fuera = []
    for i, c in enumerate(libro.capitulos):
        t = c.titulo if len(c.titulo) <= 46 else c.titulo[:43] + "..."
        fuera.append((f"{i + 1}. {t} · {ficha.miles(c.palabras)} pal.", i))
    return fuera


def _indice_de(libro, actual=None):
    """Opciones Y valor del indice, SIEMPRE juntos y validados contra ESTE libro.

    Las dos cosas son la misma correccion. Al abrir un libro desde el buscador
    saltaba un recuadro rojo de Gradio —«Value: 1 is not in the list of
    choices: []»— porque `_abrir_del_catalogo` es una generadora: su primer
    `yield` VACIA el desplegable de capitulos mientras descarga, y con las
    opciones vacias cualquier valor que llegue a destiempo es invalido. El
    libro se abria bien; lo que no se puede es ensenar un Error rojo en el paso
    estrella de la demo.

    Vale para los dos mandos -el indice y el desplegable-, que es lo que
    permite que ninguno de los dos mande nunca un valor suelto.
    """
    if libro is None or not getattr(libro, "capitulos", None):
        return gr.update(choices=[], value=None)
    # Un indice que no es de este libro no se pinta: mejor sin seleccion que
    # con una seleccion que no existe.
    try:
        valido = 0 <= int(actual) < len(libro.capitulos)
    except (TypeError, ValueError):
        valido = False
    return gr.update(choices=_opciones_capitulos(libro),
                     value=int(actual) if valido else None)


def _cap(libro, idx):
    """El capitulo `idx`, o None si el indice no sirve.

    El desplegable de Gradio puede devolver un indice viejo justo despues de
    cambiar de libro, o `None`, o incluso una cadena. Antes eso reventaba con
    IndexError contra la interfaz.
    """
    if libro is None or idx is None or not libro.capitulos:
        return None
    try:
        i = int(idx)
    except (TypeError, ValueError):
        return None
    return libro.capitulos[i] if 0 <= i < len(libro.capitulos) else None


def _capitulo(libro, idx, peticion: gr.Request = None):
    c = _cap(libro, idx)
    if c is None:
        return _html_lectura(""), ""
    # Mueve el marcapaginas. Se conserva la ruta ya guardada y solo se cambia
    # el capitulo, y solo si el marcador es de este mismo libro.
    s = _leer_sesion(peticion)
    if s and s.get("titulo") == libro.titulo:
        _guardar_sesion(s["ruta"], libro.titulo, int(idx), peticion)
        biblioteca.anotar(ruta_libro=s["ruta"], titulo=libro.titulo,
                          autor=libro.autor, capitulos=len(libro.capitulos),
                          capitulo=int(idx), palabras=libro.palabras,
                          ruta=_archivo_lector("biblioteca.json", peticion))
    return (_html_lectura(c.texto),
            f"**{c.titulo}** · {ficha.miles(c.palabras)} palabras · "
            f"capítulo {int(idx) + 1} de {len(libro.capitulos)}")


def _medir(libro, idx, como="cifra"):
    """Mide el capitulo con el modelo v4, avisando de la espera.

    La primera vez construye el `Puntuador`, que son 328 MB. Sin este primer
    `yield` la pantalla se queda quieta cerca de un minuto y parece colgada.
    """
    c = _cap(libro, idx)
    if c is None:
        yield "Abre un libro y elige un capítulo."
        return
    if _puntuador is None:
        yield ("Midiendo… la primera vez carga el modelo v4 (328 MB) y puede "
               "tardar cerca de un minuto. Después es inmediato.")
    else:
        yield "Midiendo el capítulo…"
    try:
        r = puntuador().puntuar(ficha.para_medir(c.texto))
    # OSError y no solo FileNotFoundError. La segunda solo cubre la carpeta
    # local que no existe; desplegada, `LITERALEVEL_MODELO` es un repositorio
    # del Hub y `from_pretrained` lanza OSError si el Hub no responde, si el
    # repositorio se renombra o si la descarga se corta en el arranque en frio.
    # Los otros tres manejadores que cargan el modelo ya atrapaban OSError;
    # este -el boton "¿Como de dificil es este capitulo?"- se habia quedado
    # fuera. `FileNotFoundError` desciende de `OSError`, asi que el mensaje de
    # la carpeta ausente sigue saliendo igual.
    # `Exception` y no `(ValueError, OSError)`: lo que lanza torch al quedarse
    # sin memoria es `RuntimeError` -DefaultCPUAllocator: not enough memory- y
    # lo que lanza `safetensors` con una descarga del Hub cortada tampoco
    # desciende de OSError. El invariante de la cabecera no dice "casi nunca".
    except Exception as e:
        yield _aviso(e)
        return
    yield (_nivel_dicho(r.puntuacion, r.banda, como)
           + f" · {r.n_bloques} bloques · confianza {r.confianza}")


# --- Las dos formas de decir el mismo numero ------------------------------
# La escala de LiteraLevel es 0..2 y es la que el modelo produce. El MCER
# (A1..C2) es el ancla con la que se entreno, no un certificado: por eso va
# siempre acompanado de la cifra y del aviso, nunca solo.

def _cefr(publico: float) -> str:
    """Ancla MCER mas cercana a una puntuacion de la escala publica 0..2.

    Redondea los empates HACIA ARRIBA, y no con `round()`, que en Python
    redondea al par: `round(2.5)` da 2 y `round(4.5)` da 4. Con esa regla un
    1.00 clavado salia B1 y un 1.80 salia C1, justo los limites que aparecen
    escritos en la tabla de la interfaz. Un usuario que comparase su cifra con
    la tabla habria encontrado dos respuestas distintas para el mismo numero.

    `scoring.anchor_cefr` se queda como esta: es del modelo y no se toca. Aqui
    hay una sola regla para todo lo que ve el lector, y es esta.
    """
    try:
        interno = float(publico) * 2.5
    except (TypeError, ValueError):
        return scoring.ANCHORS[0]
    i = int(math.floor(min(5.0, max(0.0, interno)) + 0.5))
    return scoring.ANCHORS[min(i, len(scoring.ANCHORS) - 1)]


def _nivel_dicho(publico: float, banda: str = "", como: str = "cifra") -> str:
    """El nivel escrito como lo quiera leer el usuario, con lo otro al lado.

    Nunca se da una de las dos solo. Quien elige MCER sigue viendo la cifra
    -que es lo que mide el modelo- y quien elige la cifra sigue viendo el
    ancla, que es lo que le suena de su escuela de idiomas.
    """
    b = f" ({banda})" if banda else ""
    if como == "cefr":
        return f"**{_cefr(publico)}** · {publico:.2f} / 2.00{b}"
    return f"**{publico:.2f} / 2.00**{b} · orientativo **{_cefr(publico)}**"


_TABLA_CEFR = """#### De 0–2 a A1–C2

| LiteraLevel | MCER | Qué suele significar |
|---|---|---|
| 0.00 – 0.20 | **A1** | frases muy cortas, vocabulario de andar por casa |
| 0.20 – 0.60 | **A2** | narración sencilla, poca subordinación |
| 0.60 – 1.00 | **B1** | novela juvenil, prosa clara |
| 1.00 – 1.40 | **B2** | novela adulta corriente |
| 1.40 – 1.80 | **C1** | prosa literaria densa, vocabulario amplio |
| 1.80 – 2.00 | **C2** | clásicos exigentes, sintaxis larga |

**LiteraLevel no certifica ningún nivel del MCER**, y esta columna no equivale
a un examen. El modelo se entrenó con textos anclados a esas etiquetas y
aprendió a colocar un texto nuevo en esa recta: lo que devuelve es una
posición en una escala continua, y la letra es la etiqueta más cercana. Sirve
para elegir qué leer, no para acreditar nada ante nadie."""


RUTA_ANALISIS = BASE_DATOS_LECTOR / "analisis"


def _clave_libro(libro) -> str:
    """Identifica un libro por su contenido, no por el nombre del archivo.

    Con el TEXTO dentro. La v3 solo miraba titulo, palabras y titulos de
    capitulo, y la carpeta de analisis es comun a todos los lectores: un epub
    subido con el titulo y los recuentos de un libro del catalogo -todo eso lo
    elige quien sube el archivo- escribia la curva y la sinopsis que veian todos
    los lectores del libro de verdad (revision de api.py en 2a49bf2, hallazgo
    4). Con el texto, dos claves solo coinciden si el texto es el mismo, y
    entonces compartir el analisis es correcto. Hashear un libro de 1 MB son
    milisegundos.

    Lo ya guardado con la v3 no se tira: `_heredar_clave_vieja`.
    """
    import hashlib
    # La version entra en la clave: al empezar a recortar la licencia de
    # Gutenberg antes de puntuar, los analisis ya guardados dejaron de ser
    # comparables con los nuevos. Sin esto seguirian sirviendose los viejos.
    h = hashlib.sha256(
        f"v4-con-texto\x1f{libro.titulo}\x1f{libro.palabras}".encode("utf-8"))
    for c in libro.capitulos:
        h.update(f"\x1e{c.titulo}\x1f".encode("utf-8"))
        h.update(c.texto.encode("utf-8"))
    return h.hexdigest()[:20]


def _clave_libro_v3(libro) -> str:
    """La clave anterior, sin el texto. Solo para heredar lo ya calculado."""
    import hashlib
    h = hashlib.sha256(
        f"v3-sin-portadilla\x1f{libro.titulo}\x1f{libro.palabras}".encode("utf-8"))
    for c in libro.capitulos[:40]:
        h.update(f"{c.titulo}\x1f{c.palabras}".encode("utf-8"))
    return h.hexdigest()[:20]


def _heredar_clave_vieja(libro, ruta_nueva, sufijo: str) -> None:
    """Si falta el archivo con la clave nueva, trae el de la v3, pero SOLO para
    libros del catalogo.

    Asi no se recalcula lo ya pagado: las sinopsis cuestan un uso cada una. Un
    libro subido no hereda nunca, porque una clave v3 es justo lo que ese libro
    podia suplantar. Se COPIA, no se mueve: si un archivo subido en Gradio se
    llama `pg1342.epub` y tiene otro texto, heredaria una copia y el libro de
    verdad conservaria la suya.
    """
    try:
        if ruta_nueva.exists() or not getattr(libro, "id_catalogo", None):
            return
        vieja = RUTA_ANALISIS / f"{_clave_libro_v3(libro)}{sufijo}.json"
        if vieja.is_file():
            import shutil
            shutil.copyfile(vieja, ruta_nueva)
    except OSError:
        pass


def _palabras_del_cuerpo(libro) -> int:
    """Las palabras del LIBRO, sin portadilla ni licencia.

    El mismo recuento que la cabecera y la ficha. El resumen de la curva
    imprimia `libro.palabras` crudo, asi que la misma pantalla decia 129.589
    arriba y "sobre 130.104 en total" debajo de la grafica, y la cifra que
    el guion del video dice a camara era la segunda. Una pantalla con dos
    recuentos de lo mismo es lo primero que alguien compara.
    """
    try:
        return ficha.caracteristicas(libro).palabras or libro.palabras
    except Exception:
        return libro.palabras      # un recuento jamas puede tumbar el analisis


def _es_numero(x) -> bool:
    """Numero de verdad, y `True` no lo es.

    `isinstance(True, int)` da True en Python, y un `"dificultad": true` en un
    JSON pasaria por numero y luego sumaria 1 sin que nadie lo notara.
    """
    # Y FINITO. `json.loads` acepta `NaN` y `1e400`, y los dos revientan al
    # formatear o al convertir a entero. El caso no es solo de disco
    # corrupto: `_analizar_libro` guarda `round(sum(vs)/len(vs), 3)` y
    # `np.clip(nan)` es `nan`, asi que un NaN del modelo se PERSISTE y
    # revienta la siguiente vez que se abra ese libro.
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def _ruta_analisis(libro, modo="completo"):
    """El completo se guarda sin sufijo: es el bueno y el que se busca primero."""
    sufijo = "" if modo == "completo" else f"-{modo}"
    return RUTA_ANALISIS / f"{_clave_libro(libro)}{sufijo}.json"


def _analisis_guardado(libro, modo="completo"):
    """El analisis guardado de este libro, o None si no vale.

    Se comprueba la FORMA, no solo que el JSON parsee. Es el mismo fallo que ya
    se corrigio en `sesion.json` y en `perfil.json`: un archivo valido pero con
    otra estructura -una lista, o filas sin la clave `dificultad`- pasaba el
    `except` y reventaba mas adelante con un KeyError hacia la interfaz. Los
    escribe la app, no un usuario, pero un archivo a medias de un reinicio en
    mitad de la escritura tiene exactamente esta pinta.
    """
    ruta = _ruta_analisis(libro, modo)
    _heredar_clave_vieja(libro, ruta, "" if modo == "completo" else f"-{modo}")
    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    filas = d.get("filas")
    # Lista y NO VACIA: `_resumen_analisis` hace `min(filas, ...)`, que sobre una
    # lista vacia lanza ValueError.
    if not isinstance(filas, list) or not filas:
        return None
    for f in filas:
        if (not isinstance(f, dict) or "capitulo" not in f
                or not _es_numero(f.get("dificultad"))):
            return None
    # Y el resto de la forma. Comprobar solo `filas` no bastaba: un archivo con
    # filas validas y sin `ventanas` pasaba esta puerta y reventaba con un
    # KeyError dentro de `_resumen_analisis`, que es lo que este validador
    # existe para evitar. Se rellenan con 0 en vez de rechazar el archivo: la
    # curva -que es lo que el lector espera- se puede dibujar sin ellas.
    for clave in ("ventanas", "palabras"):
        if not _es_numero(d.get(clave)):
            d[clave] = 0
    for clave in ("capitulos_medidos", "capitulos_totales"):
        if clave in d and not _es_numero(d[clave]):
            d[clave] = len(filas)
    # El titulo y el autor los sabe el libro que tenemos delante, asi que un
    # archivo al que le falten no hay por que tirarlo.
    if not isinstance(d.get("titulo"), str):
        d["titulo"] = str(getattr(libro, "titulo", "") or "")
    if not isinstance(d.get("autor"), str):
        d["autor"] = str(getattr(libro, "autor", "") or "")
    for f in filas:
        if not isinstance(f.get("titulo"), str):
            f["titulo"] = f"capítulo {f['capitulo']}"
    return d


def _guardar_analisis(libro, datos, modo="completo") -> None:
    try:
        RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
        _ruta_analisis(libro, modo).write_text(
            json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass          # el analisis es util, no imprescindible


# Cuantos capitulos mira el vistazo rapido, y cuantas ventanas de cada uno.
#
# El numero no es redondo por gusto: en esta CPU el modelo hace 4,4 ventanas
# por segundo (medido, no estimado), asi que 30 x 2 = 60 ventanas son unos 14
# segundos. Con 40 capitulos se iba a 23 s, que ya no es un vistazo. Si algun
# dia el modelo corre en GPU, esto puede subir sin tocar nada mas.
RAPIDO_CAPITULOS = 30
RAPIDO_VENTANAS = 2


def _capitulos_de_cuerpo(libro):
    return ficha.capitulos_de_cuerpo(libro)


def _analizar_libro(libro, modo="completo", como="cifra", paleta=None,
                    peticion: gr.Request = None):
    """Perfil de dificultad del libro, capitulo a capitulo.

    Dos velocidades, porque son dos preguntas distintas:

    - **completo**: cada capitulo, ventana a ventana, sin muestrear. Es la
      respuesta a "¿de verdad lo lee todo?" y con un libro de 500.000 palabras
      son minutos. Se guarda en disco: se paga una vez por libro.
    - **rapido**: hasta `RAPIDO_CAPITULOS` capitulos repartidos por la obra y
      `RAPIDO_VENTANAS` de cada uno. Da la forma de la curva en segundos. Es
      un vistazo, y se dice que lo es. (Aqui decia "hasta 40 capitulos y 2
      ventanas", que era el valor de antes de bajarlo a 30: el comentario de
      las constantes explica por que se bajo y este docstring se quedo con la
      cifra vieja. Mejor no repetir el numero y nombrar la constante.)

    Va dibujando la grafica MIENTRAS mide, no al final. Es la diferencia entre
    esperar mirando una barra de progreso y ver aparecer la curva: el trabajo
    tarda lo mismo pero deja de parecer que la aplicacion se ha colgado.
    """
    if libro is None or not libro.capitulos:
        yield "Abre un libro primero, en esta misma pestaña.", None
        return

    rapido = (modo == "rapido")
    # El analisis completo vale tambien como rapido -es estrictamente mejor-,
    # asi que si ya esta hecho no se vuelve a medir peor a proposito.
    datos = _analisis_guardado(libro) or (_analisis_guardado(libro, "rapido")
                                          if rapido else None)
    if datos is None:
        cuerpo = _capitulos_de_cuerpo(libro)
        if not cuerpo:
            yield ("Este libro no tiene capítulos con prosa suficiente para "
                   "analizarlos."), None
            return
        if rapido and len(cuerpo) > RAPIDO_CAPITULOS:
            import numpy as np
            idx = np.linspace(0, len(cuerpo) - 1, RAPIDO_CAPITULOS)
            cuerpo = [cuerpo[i] for i in sorted(set(idx.round().astype(int).tolist()))]
        # El `try` cubria SOLO `puntuador()`, o sea la construccion. La
        # llamada que de verdad puntua -`perfil_de_texto`, mas abajo- estaba
        # fuera de todo `try`, y es la que puede quedarse sin memoria a mitad
        # de un libro de 366 capitulos. Se envuelve el trabajo entero.
        try:
            p = puntuador()
        except Exception as e:
            yield _aviso(e), None
            return

        filas, ventanas = [], 0
        total = len(cuerpo)
        # Cada cuanto se repinta. Redibujar 366 veces cuesta mas que medir.
        cada = 1 if total <= 30 else max(2, total // 30)
        for n, (i, c) in enumerate(cuerpo, 1):
            try:
                vs = p.perfil_de_texto(ficha.para_medir(c.texto),
                                       tope=RAPIDO_VENTANAS if rapido else 0)
            except Exception as e:
                # Un capitulo que revienta no puede llevarse el libro entero:
                # lo que ya se midio vale y se ensena, con el aviso al lado.
                if filas:
                    parcial = {"titulo": libro.titulo, "autor": libro.autor,
                               "palabras": _palabras_del_cuerpo(libro), "ventanas": ventanas,
                               "filas": filas, "modo": modo}
                    yield (_aviso(e) + f"\n\nMedidos {len(filas)} capitulos "
                           f"antes de fallar.", _grafica_analisis(parcial, paleta))
                else:
                    yield _aviso(e), None
                return
            if vs:
                ventanas += len(vs)
                filas.append({"capitulo": n, "titulo": c.titulo[:40],
                              "indice": i, "dificultad": round(sum(vs) / len(vs), 3),
                              "min": round(min(vs), 3), "max": round(max(vs), 3),
                              "ventanas": len(vs), "palabras": c.palabras})
            if filas and (n % cada == 0 or n == total):
                parcial = {"titulo": libro.titulo, "autor": libro.autor,
                           "palabras": _palabras_del_cuerpo(libro), "ventanas": ventanas,
                           "filas": filas, "modo": modo}
                yield (f"Midiendo con el modelo v4: capítulo **{n} de {total}** · "
                       f"{ficha.miles(ventanas)} ventanas leídas."
                       + ("" if rapido else
                          "\n\nEsto se calcula una sola vez y queda guardado."),
                       _grafica_analisis(parcial, paleta))

        if not filas:
            yield "No pude medir ningún capítulo de este libro.", None
            return
        datos = {"titulo": libro.titulo, "autor": libro.autor,
                 "palabras": _palabras_del_cuerpo(libro), "ventanas": ventanas,
                 "filas": filas, "modo": modo,
                 "capitulos_medidos": total,
                 "capitulos_totales": len(_capitulos_de_cuerpo(libro))}
        _guardar_analisis(libro, datos, modo)

    yield _resumen_analisis(datos, como), _grafica_analisis(datos, paleta)


def _filas_del_catalogo(libro) -> list:
    """La curva del catalogo medido, con los indices traducidos a ESTE libro.

    Solo si los capitulos cuadran uno a uno (`ficha.alinear_con_catalogo`):
    la curva se midio sobre el `.txt`, y un EPUB puede partir el libro de otra
    manera. Si no cuadran, lista vacia, y la sugerencia espera a que el lector
    mida el libro aqui."""
    pid = getattr(libro, "id_catalogo", None)
    if not pid:
        return []
    try:
        filas = catalogo().capitulos_de(pid)
    except Exception:
        return []
    mapa = ficha.alinear_con_catalogo(libro, filas)
    if not mapa:
        return []
    return [dict(f, indice=mapa[int(f["capitulo"])]) for f in filas]


def _capitulos_sugeridos(libro, p=None):
    """«Este libro te queda grande, pero estos capitulos no.»

    Solo aparece cuando se juntan tres cosas: hay perfil, la curva del libro ya
    esta medida, y el libro entero va por encima de ese perfil. Sin curva no se
    sugiere nada, igual que la ficha no afirma un ritmo que todavia no sabe.

    La seleccion es `ficha.capitulos_a_tu_nivel`, con `perfil.RETO` como margen:
    la misma funcion que usara el buscador del catalogo y el mismo margen con el
    que la ficha dice "va por encima de tu nivel", para que ninguna pantalla
    pueda contradecir a otra.

    Las opciones son indices REALES de `libro.capitulos`. Al elegir una se salta
    con `_indice_de`, que valida contra este libro: el mismo camino que el
    indice de abajo, para no abrir otra puerta al recuadro rojo.
    """
    oculto = gr.update(choices=[], value=None, visible=False)
    if libro is None or p is None or not getattr(libro, "capitulos", None):
        return oculto
    try:
        # La curva medida aqui manda; si no la hay, la del catalogo, pero solo
        # con los capitulos alineados (`_filas_del_catalogo`).
        guardado = _analisis_guardado(libro)
        filas = guardado["filas"] if guardado else _filas_del_catalogo(libro)
        if not filas:
            return oculto
        if ficha.dificultad_global(filas) <= p.nivel + perfil_mod.RETO:
            return oculto          # el libro entero ya esta a su alcance
        sel = [f for f in ficha.capitulos_a_tu_nivel(filas, p.nivel, perfil_mod.RETO)
               if 0 <= int(f["indice"]) < len(libro.capitulos)]
    except Exception:
        return oculto              # una sugerencia es un adorno; jamas tapa el libro
    if not sel:
        return oculto
    opciones = [(f"{libro.capitulos[int(f['indice'])].titulo[:50]} · "
                 f"{ficha.miles(f['palabras'])} palabras", int(f["indice"]))
                for f in sel]
    return gr.update(choices=opciones, value=None, visible=True,
                     label="Este libro va por encima de tu nivel, pero estos "
                           "capítulos están a tu alcance")


def _ficha_libro(libro, p=None) -> str:
    """Como es de leer este libro. Se calcula contando, asi que es instantaneo.

    Sale solo al abrir el libro y no cuesta nada: no hay red, no hay modelo, no
    hay nada que pueda fallar salvo que el libro este vacio. Lo que si depende
    del lector es el tiempo estimado, porque leer por encima de tu nivel no es
    la misma velocidad que leer por debajo.
    """
    if libro is None or not libro.capitulos:
        return ""
    try:
        c = ficha.caracteristicas(libro)
    except Exception:
        return ""          # una ficha es un adorno; jamas puede tapar el libro
    if not c.palabras:
        return ""
    # Sin nivel del lector no se puede decir si el libro le queda cuesta
    # arriba, asi que se dan las dos velocidades en vez de elegir una al azar.
    if p is None:
        tiempo = f"{_rango_de_tiempo(c.minutos(False), c.minutos(True))} de lectura"
    else:
        guardado = _analisis_guardado(libro)
        nivel_libro = (ficha.dificultad_global(guardado["filas"])
                       if guardado else None)
        if nivel_libro is None:
            # Con perfil pero SIN medir el libro no se sabe si le queda cuesta
            # arriba, asi que se dan las dos velocidades, igual que sin perfil.
            # Antes se daba por bueno el ritmo comodo y se rotulaba "a tu ritmo
            # de lectura": el mismo libro y el mismo lector leian "18 h 52 min
            # a tu ritmo" antes de calcular la curva y "30 h 52 min (va por
            # encima de tu nivel)" despues. Doce horas de diferencia, y la
            # primera cifra afirmaba algo que la aplicacion no sabia todavia.
            tiempo = (f"{_rango_de_tiempo(c.minutos(False), c.minutos(True))} de lectura, "
                      f"según lo que te cueste")
        else:
            # `perfil.RETO` y no un 0.15 a mano: es el mismo margen con el que
            # `_capitulos_sugeridos` decide que un capitulo SI esta a tu
            # alcance. Con dos numeros, la ficha podria decir "va por encima"
            # y a la vez no sugerir nada, o al reves.
            exigente = nivel_libro > p.nivel + perfil_mod.RETO
            tiempo = _reloj_llano(c.minutos(exigente))
            tiempo += (" (va por encima de tu nivel)" if exigente
                       else " a tu ritmo de lectura")
    lineas = [
        "#### Cómo es de leer",
        f"- **{ficha.miles(c.palabras)} palabras** en {c.capitulos} "
        f"{'capítulo' if c.capitulos == 1 else 'capítulos'} · {tiempo}",
        f"- Frases de **{c.frase_media:.0f} palabras** de media",
        f"- Diálogo: **{c.dialogo * 100:.0f}%** de las frases llevan voz — "
        f"{c.forma_del_dialogo}",
        f"- Variedad de vocabulario: **{c.riqueza * 100:.1f}** palabras "
        f"distintas por cada 100",
    ]
    if c.distintivas:
        lineas.append("- Lo que más se repite: "
                      + ", ".join(f"`{w}`" for w in c.distintivas[:10]))
    lineas.append("\n_Todo esto está contado sobre el texto del archivo, "
                  "no lo dice ningún modelo._")
    return "\n".join(lineas)


def _sinopsis_guardada(libro):
    """La sinopsis guardada, o None si el archivo no tiene la forma esperada.

    Mismo caso que `_analisis_guardado`: un JSON valido que fuera una lista o
    una cadena pasaba el `except` y reventaba en el `.get`, y un campo numerico
    reventaba en el `.strip()`. Se normaliza a texto lo que se vaya a tratar
    como texto.
    """
    try:
        ruta = RUTA_ANALISIS / f"{_clave_libro(libro)}-sinopsis.json"
        _heredar_clave_vieja(libro, ruta, "-sinopsis")
        d = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    # `temas` es la UNICA lista; lo demas es texto. Antes se dejaba pasar
    # cualquier lista tal cual, y `de_que_trata` o `para_quien` con una lista
    # dentro levantaban un AttributeError en el `.strip()` de quien la pinta.
    # Y al reves: `temas` con una cadena se pintaba letra a letra
    # -"u · n · a · c · a · d · e · n · a"-.
    fuera = {}
    for k, v in d.items():
        if v is None:
            continue
        if k == "temas":
            fuera[k] = [str(x) for x in (v if isinstance(v, list) else [v])]
        else:
            fuera[k] = " ".join(str(x) for x in v) if isinstance(v, list) else str(v)
    return fuera


def _de_que_trata(libro, peticion: gr.Request = None):
    """Resumen en espanol de que va el libro. Es lo unico de la ficha que sale
    a la red, asi que va detras de un boton y se guarda: un libro se resume una
    vez y ya. Generadora, porque tarda unos segundos.

    **Esta es la TERCERA cosa que cuesta dinero**, y durante un tiempo fue la
    unica que estaba abierta. No recibia `gr.Request`, no pasaba por el codigo
    de acceso, no tenia tope por hora y no apuntaba el uso: en una direccion
    publica, cualquiera podia subir un .txt, pulsar el boton, cambiar una
    palabra del archivo -la cache va por titulo, palabras y titulos de
    capitulo- y repetir. Cada pulsacion son cuatro pasajes de 900 palabras a la
    API. Lo encontro una auditoria del codigo, no del documento.
    """
    if libro is None or not libro.capitulos:
        yield "Abre un libro primero."
        return
    datos = _sinopsis_guardada(libro)
    if datos is None:
        # El tope por hora frena el GASTO, no el uso: si el visitante no puede
        # pagar -no ha entrado, agoto su cupo, o no hay clave-, esta pulsacion
        # no puede costar un centimo y no debe gastar ficha del cubo. Se
        # arreglo primero en `_consultar` y estas dos puertas se quedaron sin
        # el mismo trato: un visitante sin perfil agotaba en seis clics el cubo
        # de TODA la IP y bloqueaba a quien si habia entrado.
        va_a_costar = (not config.falta()
                       and cuentas.permite(BASE_DATOS_LECTOR,
                                           _codigo_de(peticion))[0])
        if va_a_costar and not _dentro_del_limite(
                peticion, "sinopsis", LIMITE_SINOPSIS_HORA):
            yield _aviso(_mensaje_limite(
                "es", _minutos_para_la_siguiente("sinopsis", peticion), "sinopsis"))
            return
        puede, motivo_pago = _puede_pagar(peticion)
        if not puede:
            yield motivo_pago
            return
        # `consultor()` construye el ConsultorLexico ENTERO, que abre el
        # diccionario Kaikki y lanza `FileNotFoundError` si el `.db` no esta.
        # El resumen no necesita el diccionario -ni spaCy, ni MiniLM-: solo
        # quiere un cliente de OpenAI. Sin este `try`, en el Space con el
        # dataset mal montado la pestana Leer funcionaba, la ficha contada
        # funcionaba, y este boton devolvia un "Error" pelado. En `_consultar`
        # la misma construccion si estaba protegida.
        try:
            cliente = consultor()._cliente()
        except Exception as e:
            # Aqui SI se devuelve: la excepcion es al CONSTRUIR el consultor
            # -el diccionario que falta- y ocurre antes de cualquier llamada a
            # la API. Faltaba, y era la rama que este mismo `try` vino a cubrir:
            # el Space con el dataset mal montado cobraba un uso por un boton
            # que ni salio a la red.
            cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
            yield _aviso(f"No pude preparar el resumen ({type(e).__name__}). "
                         "El resto de la ficha no lo necesita y sigue arriba.")
            return
        if cliente is None:
            # Sin cliente no hay llamada, asi que el uso cobrado por
            # `_puede_pagar` se devuelve. Este caso ademas se sabe ANTES de
            # cobrar y no tiene excusa: al lector se le descontaba un uso de su
            # cupo por pulsar un boton que ni salio a la red.
            cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
            yield ("Para el resumen hace falta la clave de OpenAI. Todo lo "
                   "demás de la ficha —lo que está contado sobre el texto— "
                   "ya lo tienes arriba y no necesita clave.")
            return
        yield "Leyendo pasajes del principio, del medio y del final…"
        datos, causa = ficha.sinopsis(libro, cliente)
        if datos is None:
            # El uso vuelve SOLO si no salio nada a la red. `_puede_pagar`
            # cobra antes de saber si se va a gastar, y el mensaje de abajo
            # invita a reintentar: sin esto, cada "vuelve a intentarlo"
            # costaba un uso por un fallo que no era del lector. Y al reves:
            # devolverlo cuando la peticion SI salio seria regalar tokens ya
            # pagados.
            if causa in ("sin_red", "sin_pasajes"):
                cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
            yield ("No pude preparar el resumen ahora mismo. Vuelve a "
                   "intentarlo; el resto de la ficha no depende de esto."
                   + ("" if causa in ("sin_red", "sin_pasajes")
                      else " Este intento sí ha consumido uno de tus usos."))
            return
        try:
            RUTA_ANALISIS.mkdir(parents=True, exist_ok=True)
            (RUTA_ANALISIS / f"{_clave_libro(libro)}-sinopsis.json").write_text(
                json.dumps(datos, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    partes = ["#### De qué trata", datos.get("de_que_trata", "").strip()]
    temas = [t for t in (datos.get("temas") or []) if str(t).strip()]
    if temas:
        partes.append("**Temas:** " + " · ".join(str(t) for t in temas))
    if datos.get("para_quien", "").strip():
        partes.append(f"**Para quién:** {datos['para_quien'].strip()}")
    if datos.get("aviso", "").strip():
        partes.append(f"**Antes de empezar:** {datos['aviso'].strip()}")
    partes.append("\n_Resumen escrito por un modelo de lenguaje a partir de "
                  "pasajes del propio archivo. Las cifras de arriba no: esas "
                  "están contadas._")
    yield "\n\n".join(partes)


def _suavizar(valores, ventana: int) -> list[float]:
    """Media movil centrada. Sin numpy ni pandas: son cuatro lineas y asi la
    grafica no depende de nada que pueda no estar en el despliegue."""
    if ventana < 2 or len(valores) < ventana:
        return list(valores)
    salida, mitad = [], ventana // 2
    for i in range(len(valores)):
        a, b = max(0, i - mitad), min(len(valores), i + mitad + 1)
        salida.append(sum(valores[a:b]) / (b - a))
    return salida


def _colores_paleta(clave):
    """Los colores de una paleta, para lo que NO es CSS.

    Plotly no sabe leer variables CSS: dibuja una imagen con los
    colores que se le den y ahi se acaba. Por eso la grafica estaba
    clavada en azul hielo aunque la paleta fuera "papel", y sobre el
    panel blanco de las paletas claras la letra de los ejes -#c8dbe6-
    daba 1,3:1. No hay un color que valga para las cinco paletas: para
    pasar AA sobre el fondo mas oscuro hace falta luminancia >= 0,186 y
    sobre el mas claro <= 0,174. Las dos condiciones no se cumplen a la
    vez, asi que el color TIENE que venir de la paleta.
    """
    d = paletas_mod.PALETAS.get(clave) or paletas_mod.PALETAS[
        paletas_mod.POR_DEFECTO]
    return d["vars"]


def _rgba(color: str, alfa: float) -> str:
    """`#rrggbb` -> `rgba(r,g,b,alfa)`. Si ya viene en rgb/rgba se
    devuelve tal cual: las paletas mezclan los dos formatos."""
    c = color.strip()
    if not c.startswith("#"):
        return c
    c = c[1:]
    if len(c) == 3:
        c = "".join(x * 2 for x in c)
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alfa})"


def _grafica_analisis(datos, paleta: str = None):
    """Curva de dificultad del libro, continua y con zoom.

    Era un diagrama de barras y con War and Peace -366 capitulos- se convertia
    en un bloque azul macizo del que no se leia nada. Con una linea se ve la
    forma, y con la barra de herramientas de Plotly se puede ampliar un tramo
    concreto, que es lo que uno quiere cuando hay cientos de capitulos.

    Van dos trazos a proposito: el fino y translucido es el dato real, capitulo
    a capitulo; el grueso es la media movil. Con 366 puntos el dato crudo es
    ruido y la tendencia -"empieza duro y se suelta"- solo se ve suavizada. Con
    pocos capitulos la media movil se desactiva sola y queda la linea real.
    """
    import plotly.graph_objects as go

    filas = datos["filas"]
    x = [f["capitulo"] for f in filas]
    y = [f["dificultad"] for f in filas]
    titulos = [f.get("titulo", "") for f in filas]

    # La ventana crece con el libro: 366 capitulos piden mas suavizado que 13.
    ventana = 1 if len(y) < 12 else max(3, round(len(y) / 25))
    nivel_general = _suavizar(y, ventana)

    # Los colores salen de la paleta elegida, no de una constante. Ver
    # `_colores_paleta`: con la paleta clavada, la grafica era ilegible
    # en papel, menta y amanecer.
    v = _colores_paleta(paleta or paletas_mod.POR_DEFECTO)
    c_texto, c_acento = v["--ll-texto"], v["--ll-acento"]
    c_borde, c_fondo = v["--ll-borde"], v["--ll-fondo"]

    fig = go.Figure()
    # Un trazo de lineas con un solo punto no pinta nada (el cuento de Kian salio
    # con la grafica vacia): con un capitulo, el dato va como un punto visible.
    solo = len(y) == 1
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers" if solo else "lines", name="capítulo a capítulo",
        line=dict(color=c_acento, width=1), opacity=1 if solo else 0.35,
        marker=dict(color=c_acento, size=10),
        customdata=titulos,
        hovertemplate="Capítulo %{x}<br>%{customdata}<br>"
                      "<b>%{y:.2f}</b> / 2.00<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=x, y=nivel_general, mode="lines", name="nivel general",
        line=dict(color=c_acento, width=2.5, shape="spline", smoothing=0.6),
        fill="tozeroy",
        # El degradado es lo que pidio Miguel: el azul hielo se desvanece hacia
        # abajo en vez de cortar en un bloque plano.
        # El degradado se apaga del todo abajo. La escala publica llega a 2.00
        # y casi ningun libro baja de 1.4, asi que rellenar desde cero con
        # color solido devolvia el mismo bloque macizo que tenian las barras.
        # Asi el color acompana a la linea y el resto respira.
        fillgradient=dict(type="vertical", colorscale=[
            (0.00, _rgba(c_acento, 0.00)), (0.62, _rgba(c_acento, 0.04)),
            (0.86, _rgba(c_acento, 0.16)), (1.00, _rgba(c_acento, 0.38))]),
        hoverinfo="skip"))

    fig.update_layout(
        margin=dict(l=48, r=16, t=16, b=40), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=c_texto, size=12),
        hovermode="x unified", dragmode="zoom",
        # La etiqueta flotante la pintaba Plotly con sus colores por
        # defecto: sobre una paleta clara salia letra clara en caja clara.
        hoverlabel=dict(bgcolor=c_fondo, bordercolor=c_borde,
                        font=dict(color=c_texto)),
        showlegend=len(y) >= 12,
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(title_text="Capítulo", gridcolor=c_borde,
                     zeroline=False, showspikes=True, spikethickness=1,
                     spikecolor=_rgba(c_acento, 0.5), spikemode="across")
    fig.update_yaxes(title_text="Dificultad", range=[0, 2.05],
                     gridcolor=c_borde, zeroline=False,
                     dtick=0.5)
    return fig


def _repintar_grafica(libro, clave):
    """Vuelve a dibujar la curva con la paleta nueva, si hay curva.

    Cambiar de paleta cambia el CSS al momento, pero la grafica es una
    imagen ya pintada: se quedaba con los colores de la paleta anterior
    hasta que volvieras a medir el libro.
    """
    if libro is None:
        return gr.update()
    datos = _analisis_guardado(libro) or _analisis_guardado(libro, "rapido")
    if not datos or not datos.get("filas"):
        return gr.update()
    return _grafica_analisis(datos, clave)


def _resumen_analisis(datos, como="cifra") -> str:
    filas = datos["filas"]
    medias = [f["dificultad"] for f in filas]
    # Ponderada por ventanas, no media de medias: ver `ficha.dificultad_global`.
    global_ = ficha.dificultad_global(filas)
    facil = min(filas, key=lambda f: f["dificultad"])
    dificil = max(filas, key=lambda f: f["dificultad"])
    mitad = len(medias) // 2 or 1
    principio = sum(medias[:mitad]) / mitad
    final = sum(medias[mitad:]) / max(1, len(medias) - mitad)
    if len(filas) == 1:
        # Con un solo capitulo la segunda mitad esta vacia, `final` vale 0 y salia
        # «se va soltando»; «lo mas llevadero» y «lo mas exigente» eran el mismo.
        forma = "es un texto de **un solo capítulo**: no tiene curva que dibujar"
    elif final - principio > 0.12:
        forma = "**se va complicando**: la segunda mitad es más dura que la primera"
    elif principio - final > 0.12:
        forma = "**se va soltando**: cuesta más al principio que al final"
    else:
        forma = "mantiene un nivel **parejo de principio a fin**"
    # Como se midio, dicho sin adornos. El vistazo rapido NO puede presumir de
    # recorrer el libro entero: son dos cosas distintas y hay que distinguirlas
    # o la cifra rapida acabaria citandose como si fuera la completa.
    if datos.get("modo") == "rapido":
        medidos = datos.get("capitulos_medidos", len(filas))
        totales = datos.get("capitulos_totales", medidos)
        detalle = (f"**vistazo rápido**: {ficha.miles(datos['ventanas'])} ventanas de 250 "
                   f"palabras tomadas de {medidos} capítulos"
                   + (f" repartidos entre los {totales} del libro"
                      if totales > medidos else "")
                   + ". Da la forma de la curva, no el número definitivo; "
                     "para eso está *Analizar el libro entero*.")
    else:
        detalle = (f"medido leyendo **{ficha.miles(datos['ventanas'])} ventanas** de 250 "
                   f"palabras sobre {ficha.miles(datos['palabras'])} en total. Aquí no se "
                   f"muestrea: el modelo recorre cada capítulo entero.")
    return (
        f"### {datos['titulo']}" + (f" — {datos['autor']}" if datos["autor"] else "")
        + f"\n\n{_nivel_dicho(global_, scoring.public_band(global_), como)} "
          f"de media, {detalle}\n\n"
        + f"El libro {forma}."
        + ("" if len(filas) == 1 else
           "\n\n"
           + f"- Lo más llevadero: **capítulo {facil['capitulo']}** "
             f"({facil['titulo']}) con {facil['dificultad']:.2f}\n"
           + f"- Lo más exigente: **capítulo {dificil['capitulo']}** "
             f"({dificil['titulo']}) con {dificil['dificultad']:.2f}\n"
           + f"- Recorrido de dificultad entre capítulos: "
             f"{min(medias):.2f} a {max(medias):.2f}"))


# Abreviaturas que llevan punto y NO acaban la frase. `scoring.SENT_RE`
# corta en cada punto -es el partidor con el que se entreno el modelo y no se
# toca-, pero lo que se le ensena a una persona no puede salir partido: la
# practica de voz ofrecia "on the afternoon of May 7, 1915." como frase para
# leer en alto, que es la mitad de la primera frase de *The Secret Adversary*,
# y el contexto que viaja a OpenAI en *Orgullo y prejuicio* acababa en
# "the advent of Mr.". Medido: 13,1 % de las candidatas de ese libro eran
# fragmentos.
_ABREVIATURAS = ("Mr", "Mrs", "Ms", "Dr", "St", "Prof", "Sr", "Jr", "Rev",
                 "Hon", "Col", "Gen", "Capt", "Lt", "Sgt", "Esq", "vs",
                 "etc", "No", "Vol", "pp", "cf", "viz", "approx")
_PUNTO = "\x00"          # marcador que no aparece en un libro
_ABREV_RE = re.compile(
    r"\b(?:" + "|".join(_ABREVIATURAS) + r")\.|\b[ap]\.?m\.|\b[A-Z]\.(?=[ \t]*[A-Z])",
    re.IGNORECASE)


def _oraciones(texto: str) -> list[str]:
    """Las oraciones de un texto, RESPETANDO las abreviaturas.

    Se esconde el punto de la abreviatura tras un marcador, se parte con el
    mismo `SENT_RE` de siempre y se devuelve el punto a su sitio. Asi el
    partidor del modelo sigue siendo el del modelo y lo que ve el lector deja
    de salir a medias.
    """
    protegido = _ABREV_RE.sub(lambda m: m.group(0).replace(".", _PUNTO), texto)
    trozos = []
    for frase in scoring.SENT_RE.findall(protegido):
        limpia = " ".join(frase.replace(_PUNTO, ".").split())
        if not limpia:
            continue
        # La comilla de cierre que `SENT_RE` deja al principio del trozo
        # siguiente es de la frase ANTERIOR: «“… I shall be late!”» se partia en
        # «“… I shall be late!» y «” (when she thought it over…». Se le
        # devuelve a la anterior antes de limpiar.
        m = re.match(r"[”»]+", limpia)
        if m and trozos:
            trozos[-1] += m.group(0)
            limpia = limpia[m.end():].strip()
            if not limpia:
                continue
        trozos.append(limpia)
    fuera = []
    for trozo in trozos:
        limpia = _sin_comillas_sueltas(_sin_cursiva_gutenberg(trozo))
        if limpia:
            fuera.append(limpia)
    return fuera


def _sin_cursiva_gutenberg(frase: str) -> str:
    """«something _to do_» -> «something to do»: la cursiva de Gutenberg.

    Se colaba en la oracion que guarda «Mis palabras» y en la frase para leer en
    voz alta (f4, informe final, captura 18). La API ya la quitaba al responder,
    pero no en lo que se guarda.
    """
    return re.sub(r"(?<![\w_])_([^_\n]+)_(?![\w_])", r"\1", frase)


def _sin_comillas_sueltas(frase: str) -> str:
    """La frase sin comillas DOBLES si no van emparejadas.

    `SENT_RE` corta dentro de un parlamento de varias oraciones, y la comilla de
    cierre se queda en el trozo siguiente: «“I wonder how many miles I’ve fallen
    by this time?» salia para leer en voz alta con la comilla abierta, y la
    siguiente empezaba por «”». Medido: 107 de 306 candidatas en *Alicia* y 378
    de 2.742 en *Orgullo y prejuicio*. Las simples no se tocan: «’» es tambien
    el apostrofo de «don’t». Para leer en voz alta la comilla sobra, y la
    evaluacion de voz ignora la puntuacion.
    """
    abre = frase.count("“") + frase.count("«")
    cierra = frase.count("”") + frase.count("»")
    if abre != cierra:
        frase = re.sub(r"[“”«»]", "", frase)
    if frase.count('"') % 2:
        frase = frase.replace('"', "")
    return " ".join(frase.split())


def _sin_encabezado(parrafo: str) -> str:
    """El parrafo sin el titulillo en versales que lleva pegado delante.

    Muchos epub repiten el encabezado y lo dejan en el MISMO parrafo que el
    texto, asi que el filtro de parrafos cortos no lo tira: la frase que se
    ofrecia para leer en voz alta en *The Secret Adversary* era `PROLOGUE
    PROLOGUE It was 2 p.m. on the afternoon of May 7, 1915.`.

    Se quitan solo los tokens ENTERAMENTE en mayusculas de tres letras o mas,
    y solo mientras quede frase detras. Un `I` o un `A` sueltos no se tocan,
    y una frase que empiece por un acronimo de verdad pierde como mucho esa
    palabra, que es mejor que ensenar el titulillo.
    """
    tokens = parrafo.split()
    i = 0
    while (i < len(tokens) and i < 6 and len(tokens) - i > 6
           and len(tokens[i]) >= 3
           and tokens[i].strip(".,;:!?'\"()[]").isupper()):
        i += 1
    return " ".join(tokens[i:]) if i else parrafo


_ROMANO_RE = re.compile(r"^[IVXLCDM]+\.?$")


def _parece_indice(frase: str) -> bool:
    """True si la «frase» es un trozo de indice o un titulo, no texto corrido.

    Miguel pulso «Una frase de mi libro» y le salio «VIRGIL 67 V. INVOCATION
    TO THE LYRE 68 VI.»: un indice con numeros de pagina, que el filtro de
    longitud y el de mayuscula inicial dejaban pasar. Se descarta si:
    - casi todas las letras son mayusculas (titulos y versales);
    - lleva dos o mas numeros sueltos o numerales romanos (paginas, capitulos);
    - tiene menos de tres palabras en minuscula (no hay frase).
    Pura y sin dependencias: la usa tambien la API del front.
    """
    tokens = [t.strip(".,;:!?'\"()[]«»“”‘’—–-") for t in str(frase or "").split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return True
    letras = [c for c in "".join(tokens) if c.isalpha()]
    if letras and sum(c.isupper() for c in letras) / len(letras) > 0.6:
        return True
    # Palabras que EMPIEZAN en minuscula: las de una frase corrida. «Chapter»
    # no cuenta, y es lo que separa un indice en caja de titulo de un texto.
    minusculas = sum(1 for t in tokens if t[0].islower())
    if minusculas < 3:
        return True
    # Numeros sueltos o romanos (el «I» pronombre no, que es texto). Una fecha
    # con cifras («It was 2 p.m. on May 7, 1915») tambien tiene numeros: solo es
    # indice si ademas apenas hay palabras en minuscula.
    numericos = sum(1 for t in tokens
                    if t.isdigit() or (_ROMANO_RE.match(t) and (len(t) > 1 or t in ("V", "X"))))
    return numericos >= 2 and minusculas / len(tokens) < 0.5


def _empieza_entera(frase: str) -> bool:
    """True si la frase empieza donde empieza una frase.

    Una que arranca en minuscula o con una comilla de cierre es el final de
    otra: "” thought Alice to herself, ..." salia como frase para leer en voz
    alta.
    """
    f = frase.lstrip()
    if not f:
        return False
    if f[0] in "”’'" + chr(34) + "»)]-–—,;:.!?":
        return False
    # Y si la primera LETRA va en minuscula aunque delante haya un parentesis:
    # «(when she thought it over afterwards…» es la continuacion de «“Oh dear!
    # I shall be late!”» (f4, informe final, captura 18).
    primera = next((ch for ch in f if ch.isalpha()), "")
    return not primera.islower()


def _oracion_de(texto: str, palabra: str) -> str:
    """Primera oracion con cuerpo del capitulo que contiene la palabra.

    Se prefiere una oracion de verdad a un encabezado. Los titulos ("CHAPTER
    X.", "The Dead House") tambien casan con el patron, y devolver uno como
    contexto deja a la desambiguacion sin nada a lo que agarrarse: la palabra
    llegaria practicamente desnuda. Si no hay mas que el encabezado, se
    devuelve, que es mejor que nada.
    """
    if not texto or not palabra:
        return ""
    patron = re.compile(rf"\b{re.escape(palabra.strip())}\b", re.IGNORECASE)
    respaldo = ""
    # Por PARRAFOS antes que por oraciones, como ya hacia
    # `_frase_del_capitulo`. Los encabezados no llevan punto, asi que partir el
    # capitulo entero con SENT_RE se los traga y los pega a la primera frase:
    # el contexto que se citaba de *Metamorphosis* empezaba "I I One morning,
    # when Gregor Samsa woke...", con el numero de capitulo dentro. Lo que se
    # manda a desambiguar tiene que ser una frase, no una frase con un titulo
    # pegado delante.
    trozos = [" ".join(p.split()) for p in re.split(r"\n\s*\n", texto)]
    for frase in _oraciones(
            " ".join(p for p in trozos if len(p.split()) >= 6) or texto):
        if not patron.search(frase):
            continue
        limpia = " ".join(frase.split())
        if len(limpia.split()) >= 6:
            return limpia
        respaldo = respaldo or limpia
    return respaldo


# Rotulos de la ficha en las dos lenguas. Si el lector pide la explicacion en
# ingles, dejarle las etiquetas en espanol queda a medio hacer.
_ROTULOS = {
    "es": {
        "pron": "Pronunciación", "dicc": "Diccionario", "aqui": "Aquí significa",
        "gram": "Gramática", "nivel": "Para tu nivel", "ej": "Ejemplo",
        "elegido": "Elegido entre {n} acepciones{sim}.",
        "afinidad": ", afinidad {v:.2f}",
        "sin_entrada": "No hay entrada de diccionario para esta palabra.",
        "dudoso": ("Poca confianza en la acepción elegida (afinidad {v:.2f} "
                   "sobre 1.00). Fíjate más en «Aquí significa» que en la "
                   "definición de diccionario."),
        "dudoso_solo": ("Poca confianza en la acepción elegida (afinidad "
                        "{v:.2f} sobre 1.00) y esta vez no hay explicación de "
                        "contexto. Puede no ser el sentido que tiene en tu "
                        "frase: léela entera antes de fiarte."),
        "cache": "desde caché", "tts": "audio generado con tts-1",
        "rareza": ("muy común", "frecuente", "poco frecuente", "rara"),
        "trad": "Traducción",
        "def_ia": "Definición (generada por IA)",
        "ia_aviso": ("Esta palabra no está en el diccionario de la app, así que la "
                     "definición la ha escrito una inteligencia artificial (OpenAI). "
                     "Suele acertar, pero puede equivocarse."),
        "acepcion_ia": ("La IA eligió esta acepción del diccionario porque encaja "
                        "mejor con tu frase."),
        "puede_ser": "Puede ser",
        "puede_ser_nota": ("Tu frase no deja claro cuál de estas es, y esta vez no hay "
                           "explicación de contexto: quédate con la que encaje al leerla."),
        "parte": ("La entrada del diccionario es de «{parte}», una parte de «{todo}»: "
                  "el diccionario no trae el compuesto entero. La pronunciación es la de "
                  "«{todo}»."),
    },
    "en": {
        "pron": "Pronunciation", "dicc": "Dictionary", "aqui": "Here it means",
        "gram": "Grammar", "nivel": "For your level", "ej": "Example",
        "elegido": "Chosen from {n} senses{sim}.",
        "afinidad": ", affinity {v:.2f}",
        "sin_entrada": "No dictionary entry for this word.",
        "dudoso": ("Low confidence in the sense picked (affinity {v:.2f} of "
                   "1.00). Trust “Here it means” more than the dictionary "
                   "gloss."),
        "dudoso_solo": ("Low confidence in the sense picked (affinity {v:.2f} "
                        "of 1.00), and there is no contextual explanation this "
                        "time. It may not be the sense your sentence uses: "
                        "read the whole sentence before trusting it."),
        "cache": "from cache", "tts": "audio generated with tts-1",
        "rareza": ("very common", "common", "uncommon", "rare"),
        "trad": "Spanish",
        "def_ia": "Definition (AI-generated)",
        "ia_aviso": ("This word is not in the app's dictionary, so the definition was "
                     "written by an AI (OpenAI). It is usually right, but it can be wrong."),
        "acepcion_ia": ("The AI picked this dictionary sense because it fits your "
                        "sentence better."),
        "puede_ser": "It may be",
        "puede_ser_nota": ("Your sentence does not make clear which of these it is, and "
                           "there is no contextual explanation this time: keep the one "
                           "that fits when you read it."),
        "parte": ("The dictionary entry is for «{parte}», part of «{todo}»: the "
                  "dictionary does not have the whole compound. The pronunciation is "
                  "for «{todo}»."),
    },
}

# Por debajo de esto la eleccion de acepcion es practicamente un sorteo: se
# avisa en vez de presentarla como si fuera segura.
# Por debajo de esto, la acepcion elegida se marca como dudosa. Estaba en
# 0,35 y dejaba pasar sin aviso los casos que mas duelen: "torpedoes" en una
# frase sobre un barco torpedeado salia como "An electric ray of the genus
# Torpedo" con afinidad 0,38, y asi se guardaba en el cuaderno del lector.
# Medido sobre 15 palabras del prologo de *The Secret Adversary*: 6 acepciones
# equivocadas, y con 0,35 dos de ellas salian sin ningun aviso.
#
# Subirlo no mejora la desambiguacion: la hace HONESTA. Es mejor un lector
# que duda de una definicion correcta que uno que se cree una equivocada.
AFINIDAD_DUDOSA = 0.40


# Traduccion de los avisos tecnicos a algo que un lector pueda entender. Los
# avisos vienen de `lexicon.py` con el texto de la excepcion pegado, que es
# util en un log y horrible en pantalla: nadie quiere leer
# "RuntimeError: Error code: 429 - You exceeded your current quota"
# mientras lee una novela.
_AVISOS_HUMANOS = (
    (("429", "quota", "insufficient_quota", "billing"), {
        "es": "Se ha agotado el presupuesto mensual de explicaciones. El "
              "diccionario, la fonética y el audio siguen funcionando.",
        "en": "The monthly budget for explanations has run out. The "
              "dictionary, phonetics and audio still work."}),
    # La clave RECHAZADA va antes que la clave AUSENTE, y con su propio texto.
    # Las dos caian en "Sin clave de OpenAI", asi que un servidor con la clave
    # caducada le decia al lector que no habia clave -y de paso el uso del cupo
    # ya estaba gastado, que es lo que no se entiende si el mensaje miente-.
    (("authentication", "401", "invalid_api_key", "incorrect api key"), {
        "es": "OpenAI ha rechazado la clave de este servidor, así que no hay "
              "explicación de contexto. No es cosa tuya: avisa a quien lo "
              "administra. El resto de la ficha no la necesita.",
        "en": "OpenAI rejected this server's key, so there is no contextual "
              "explanation. Not your fault: tell whoever runs it. The rest of "
              "the card does not need it."}),
    (("sin OPENAI_API_KEY", "api key"), {
        "es": "Sin clave de OpenAI: no hay explicación de contexto. El resto "
              "de la ficha no la necesita.",
        "en": "No OpenAI key: no contextual explanation. The rest of the "
              "card does not need it."}),
    (("sin audio en el diccionario",), {
        "es": "El diccionario no trae audio de esta palabra, así que la "
              "pronunciación de arriba está generada.",
        "en": "The dictionary has no audio for this word, so the "
              "pronunciation above is generated."}),
    (("sin sentido elegido",), {
        "es": "No se pudo elegir una acepción para esta palabra.",
        "en": "No sense could be picked for this word."}),
    # Este salia EN CRUDO, sin acentos y con el margen en decimales, al lado de
    # avisos escritos con cuidado: "acepcion provisional: margen bajo (0.004)
    # frente a otra acepcion: An animal that preys on game...". Lo que el lector
    # necesita saber es que la eleccion es dudosa y cual era la otra.
    (("acepcion provisional", "margen bajo"), {
        "es": "La acepción elegida es dudosa: había otra muy parecida. Si no "
              "encaja con lo que lees, fíate del contexto de la frase.",
        "en": "The sense picked here is uncertain: another one was almost as "
              "close. If it does not fit what you are reading, trust the "
              "sentence."}),
    (("timeout", "timed out", "connection", "network", "getaddrinfo"), {
        "es": "No hay conexión con OpenAI ahora mismo. El diccionario y la "
              "fonética son locales y siguen aquí.",
        "en": "No connection to OpenAI right now. The dictionary and "
              "phonetics are local and still here."}),
)


def _humanizar(aviso: str, idioma: str) -> str:
    bajo = aviso.lower()
    for pistas, textos in _AVISOS_HUMANOS:
        if any(p.lower() in bajo for p in pistas):
            return textos.get(idioma, textos["es"])
    return aviso


_META_MARKDOWN = re.compile(r"([\\`*_{}\[\]()#+!|>~<])")


def _md(valor) -> str:
    """Texto literal dentro del Markdown de la ficha: sin HTML y sin sintaxis.

    Lo que escribe OpenAI -y lo que viene del volcado de Wiktionary- entraba
    tal cual en un gr.Markdown. `sanitize_html` quita el HTML peligroso, pero un
    `![x](https://...)` o un `[enlace](...)` devuelto por el modelo -o metido
    en la frase de un libro para que lo repita- se pintaba como imagen remota o
    como enlace (Codex, auditoria de 5033e69). Se escapa el HTML y cada
    metacaracter de Markdown. Los saltos de linea se aplanan: un campo no
    puede abrir secciones nuevas.
    """
    texto = " ".join(str(valor or "").split())
    return _META_MARKDOWN.sub(r"\\\1", _html.escape(texto, quote=False))


def _ficha(r, idioma: str = "es") -> str:
    """La consulta lexica en markdown, diciendo de donde sale cada cosa.

    Todo dato dinamico pasa por `_md`. Las secciones que escribe OpenAI llevan
    «· IA» en el rotulo (Codex): la traduccion y la explicacion de contexto
    tambien son de la IA, aunque la acepcion sea del diccionario.
    """
    t = _ROTULOS.get(idioma, _ROTULOS["es"])
    ia = " · IA"
    # Cinturon y tirantes: `_consultar` ya rechaza lo larguisimo, pero esta
    # funcion se llama tambien desde otros sitios y un encabezado es lo unico
    # de la ficha que puede llenar una pantalla de movil sin que nada lo pare.
    cab = f"## {_md(str(r.palabra_superficie)[:LIMITE_PALABRA])}"
    if r.lema_buscado and r.lema_buscado.lower() != r.palabra_superficie.lower():
        cab += f"  ·  _{_md(r.lema_buscado)}_"
    if r.categoria:
        cab += f"  ·  {_md(r.categoria)}"
    L = [cab]
    # Compuesto que el diccionario no trae entero: la entrada es de una parte, y
    # se dice antes que nada (Miguel, con «war-chant»).
    if getattr(r, "parte_del_diccionario", None) and getattr(r, "compuesto", None):
        rotulo = t.get("parte") or _ROTULOS["es"]["parte"]
        L.append("_" + rotulo.format(parte=_md(r.parte_del_diccionario), todo=_md(r.compuesto)) + "_")

    fon = []
    if r.ipa_uk:
        fon.append(f"UK {_md(r.ipa_uk)}")
    if r.ipa_us:
        fon.append(f"US {_md(r.ipa_us)}")
    if fon:
        marca_ia = " _(IPA generada por IA)_" if getattr(r, "ipa_generada_por_ia", False) else ""
        L.append(f"**{t['pron']}:** " + "  ·  ".join(fon) + marca_ia)
    # La traduccion, lo primero que busca quien lee (Miguel, con «mostly»).
    # `getattr`: las pruebas construyen fichas con objetos sin estos campos.
    if getattr(r, "traduccion", None):
        L.append(f"**{t['trad']}{ia}:** {_md(r.traduccion)}")

    # Eleccion dudosa y sin explicacion de OpenAI: las acepciones principales
    # en vez de una sola, que podia ser la hucha para «on the bank» (f4,
    # informe final, captura 21). Ver `lexicon.ResultadoLexico`.
    principales = [g for g in (getattr(r, "acepciones_principales", None) or []) if g]
    if r.sentido and principales and not r.definicion_contextual:
        L.append(f"**{t['dicc']}** (Wiktionary) · {t['puede_ser']}: "
                 + " · ".join(_md(g) for g in principales))
        L.append(f"_{t['puede_ser_nota']}_")
    elif r.sentido:
        L.append(f"**{t['dicc']}** (Wiktionary): {_md(r.sentido)}")
        if r.etiquetas_sentido:
            L.append(f"_{_md(', '.join(r.etiquetas_sentido))}_")
        if getattr(r, "acepcion_elegida_por_ia", False):
            L.append(f"_{t['acepcion_ia']}_")
        if r.n_sentidos_candidatos > 1:
            sim = (t["afinidad"].format(v=r.similitud)
                   if r.similitud is not None else "")
            L.append("_" + t["elegido"].format(n=r.n_sentidos_candidatos, sim=sim) + "_")
        # `lexicon` ya avisa por su cuenta cuando el margen entre acepciones es
        # estrecho. Si lo ha hecho, no se repite el mismo aviso con otras
        # palabras: dos advertencias seguidas diciendo lo mismo se ignoran.
        ya_avisado = any("margen bajo" in a or "provisional" in a for a in r.avisos)
        if (not ya_avisado and r.similitud is not None
                and r.n_sentidos_candidatos > 1 and r.similitud < AFINIDAD_DUDOSA):
            # Si OpenAI no contesto no hay "Aquí significa" a la que remitir:
            # mandar al lector a una seccion que no existe es peor que callar.
            clave = "dudoso" if r.definicion_contextual else "dudoso_solo"
            L.append("[!] " + t[clave].format(v=r.similitud))
    elif getattr(r, "generado_por_ia", False):
        if getattr(r, "definicion_ia", None):
            L.append(f"**{t['def_ia']}:** {_md(r.definicion_ia)}")
        L.append(f"[IA] _{t['ia_aviso']}_")
    else:
        L.append(f"_{t['sin_entrada']}_")

    if r.definicion_contextual:
        L.append(f"**{t['aqui']}{ia}:** {_md(r.definicion_contextual)}")
    if r.explicacion_gramatical:
        L.append(f"**{t['gram']}{ia}:** {_md(r.explicacion_gramatical)}")
    if r.explicacion_adaptada:
        L.append(f"**{t['nivel']} ({_md(r.banda_lector)}){ia}:** {_md(r.explicacion_adaptada)}")
    if r.ejemplo_simplificado:
        L.append(f"**{t['ej']}{ia}:** _{_md(r.ejemplo_simplificado)}_")

    pie = []
    if r.frecuencia_zipf is not None:
        muy, frec, poco, rara = t["rareza"]
        rareza = (muy if r.frecuencia_zipf >= 5 else
                  frec if r.frecuencia_zipf >= 4 else
                  poco if r.frecuencia_zipf >= 3 else rara)
        pie.append(f"{rareza} (zipf {r.frecuencia_zipf:.1f})")
    if r.desde_cache:
        pie.append(t["cache"])
    if r.audio_generado:
        pie.append(t["tts"])
    if pie:
        L.append("_" + " · ".join(pie) + "_")
    # El aviso del audio se decide AQUI, que es donde se sabe si lo hubo.
    # "sin audio en el diccionario" se traducia siempre por "la pronunciacion
    # de arriba esta generada", y sin clave no se genera ninguna: si ademas la
    # palabra no trae IPA -el diccionario solo la tiene para el 2,3 %- la ficha
    # hablaba de una pronunciacion que no estaba en ninguna parte.
    avisos = list(r.avisos)
    if getattr(r, "generado_por_ia", False):
        # Ya lo dice el aviso de IA, con mas contexto.
        avisos = [a for a in avisos if "no esta en el diccionario" not in a
                  and "no trae sentidos" not in a]
    if not r.audio_generado:
        sin_nada = not (r.ipa_uk or r.ipa_us or r.audio_uk or r.audio_us)
        avisos = [a for a in avisos if "sin audio en el diccionario" not in a]
        if sin_nada:
            avisos.append({"es": "De esta palabra no hay pronunciación: ni el "
                                 "diccionario la trae ni se pudo generar.",
                           "en": "There is no pronunciation for this word: the "
                                 "dictionary has none and none could be "
                                 "generated."}.get(idioma, "es"))
    # `dict.fromkeys` y no un `set`: quita repetidos conservando el orden.
    # Dos avisos distintos pueden humanizarse al MISMO texto -"no se pudo
    # generar audio: AuthenticationError" y "OpenAI no disponible:
    # AuthenticationError" son los dos "clave rechazada"-, y el lector veia la
    # misma linea dos veces seguidas.
    for a in dict.fromkeys(_humanizar(a, idioma) for a in avisos):
        L.append(f"[!] {a}")
    return "\n\n".join(L)


def _reproductores(r) -> str:
    """Audio remoto de Wiktionary. Los locales van al componente gr.Audio."""
    trozos = []
    for etiqueta, url in (("UK", r.audio_uk), ("US", r.audio_us)):
        if url and str(url).startswith("http"):
            # La URL viene del volcado de Wiktionary. Hoy las 7.484 son de
            # upload.wikimedia.org y ninguna lleva comillas, pero un dato que
            # no controlamos no entra sin escapar en un atributo HTML.
            seguro = _html.escape(str(url), quote=True)
            trozos.append(
                f'<p style="margin:.2rem 0"><b>{etiqueta}</b><br>'
                f'<audio controls preload="none" src="{seguro}"></audio></p>')
    # Sin ningun audio -ni de Wiktionary ni generado-, la voz del propio
    # navegador (Web Speech API): gratis, sin clave y sin entrar. Con «mostly»
    # el lector se quedaba sin nada que escuchar.
    if not (r.audio_uk or r.audio_us):
        palabra = str(getattr(r, "palabra_superficie", "") or "").strip()[:LIMITE_PALABRA]
        if palabra:
            texto = _html.escape(palabra, quote=True)
            botones = "".join(
                f'<button type="button" class="ll-voz-navegador" data-texto="{texto}" '
                f'data-lang="{lang}" style="min-height:44px;margin:.2rem .4rem .2rem 0;'
                f'padding:.3rem .8rem;border-radius:999px;cursor:pointer">'
                f'🔊 {nombre}</button>'
                for lang, nombre in (("en-US", "Voz del navegador (US)"),
                                     ("en-GB", "Voz del navegador (UK)")))
            trozos.append(
                f'<p style="margin:.3rem 0">{botones}<br><small>Voz sintética de tu '
                'navegador: sirve de orientación, pero no es un audio de diccionario.'
                '</small></p>')
    return "".join(trozos)


def _local(url):
    """Ruta reproducible por gr.Audio, o None si el audio es remoto."""
    if url and not str(url).startswith("http") and os.path.exists(str(url)):
        return str(url)
    return None


def _consultar(p, libro, idx, palabra, oracion_manual, idioma="es",
               peticion: gr.Request = None):
    """Consulta lexica en dos etapas, porque la espera es casi toda de red.

    Medido: todo el trabajo local -spaCy, el SQLite de 1,48 M entradas, la
    desambiguacion con MiniLM, la IPA- son **40 ms** con los modelos ya
    calientes. Los 30 segundos largos que se notan son la llamada a OpenAI.
    Antes la pantalla se quedaba en blanco todo ese rato y parecia colgada.

    Es una funcion generadora: el primer `yield` dice que se esta buscando, y
    el segundo trae el resultado. No cambia ni un numero, solo deja de mentir
    sobre lo que esta pasando.
    """
    palabra = (palabra or "").strip()
    if not palabra:
        yield "Escribe la palabra que quieres consultar.", "", gr.update(visible=False)
        return
    if len(palabra.split()) > 4:
        yield ("Consulta una palabra (o un phrasal verb corto), no una frase.",
               "", gr.update(visible=False))
        return
    if len(palabra) > LIMITE_PALABRA:
        yield ({"es": f"Eso son {len(palabra)} caracteres seguidos: ninguna "
                      f"palabra inglesa pasa de {LIMITE_PALABRA}. Selecciona "
                      f"una palabra del texto y vuelve a intentarlo.",
                "en": f"That is {len(palabra)} characters in a row: no English "
                      f"word goes past {LIMITE_PALABRA}. Pick a word from the "
                      f"text and try again."}[idioma if idioma == "en" else "es"],
               "", gr.update(visible=False))
        return

    esperando = ("es" if idioma != "en" else "en")
    yield ({"es": f"### {palabra}\n\nBuscando en el diccionario y preparando "
                  f"la explicación de contexto…",
            "en": f"### {palabra}\n\nLooking it up and preparing the "
                  f"contextual explanation…"}[esperando], "", None)

    # La oracion viaja entera al modelo y ademas entra en la clave de cache,
    # asi que un texto largo distinto en cada intento es una llamada de pago
    # nueva cada vez. El recorte va en el servidor: el limite del navegador es
    # una sugerencia, no una defensa.
    oracion = (oracion_manual or "").strip()[:LIMITE_ORACION]
    origen = "de la oración que escribiste"
    if not oracion and libro is not None and idx is not None:
        cap_actual = _cap(libro, idx)
        oracion = _oracion_de(cap_actual.texto, palabra) if cap_actual else ""
        origen = "localizada en el capítulo"
    if not oracion:
        oracion = palabra
        origen = "sin contexto: la desambiguación será peor"

    # El tope por hora es un freno de GASTO, no de uso. La cabecera de este
    # modulo lo dice: "las acciones que no cuestan dinero no se limitan". Y una
    # consulta sin perfil -o en una copia sin clave- es diccionario e IPA del
    # SQLite de aqui, y el audio de Wiktionary, que lo pide el navegador a
    # upload.wikimedia.org: ni uno ni otro nos cuesta un centimo, que es de lo
    # que habla este tope. -Local del todo no es: eso solo vale para el
    # diccionario y la fonetica-. Aplicarle el tope cortaba la
    # consulta 31 de un aula entera detras de la misma NAT sin que ninguna
    # pudiera costar un centimo, y encima el aviso les decia que "leer, buscar
    # y medir siguen funcionando: no cuestan nada", como si esta si costara.
    #
    # `permite` PREGUNTA sin consumir. Quien decide de forma atomica sigue
    # siendo `_puede_pagar` mas abajo, asi que esto no reabre la condicion de
    # carrera que se cerro alli. Y se exige tambien que HAYA clave: sin ella no
    # se llama a OpenAI por mucho perfil que tenga el visitante.
    va_a_costar = (not config.falta()
                   and cuentas.permite(BASE_DATOS_LECTOR,
                                       _codigo_de(peticion))[0])
    if va_a_costar and not _dentro_del_limite(peticion, "lexico",
                                              LIMITE_CONSULTAS_HORA):
        yield (_aviso(_mensaje_limite(
            idioma, _minutos_para_la_siguiente("lexico", peticion), "lexico")),
            "", gr.update(visible=False))
        return

    nivel = p.nivel if p is not None else NIVEL_POR_DEFECTO
    try:
        # `_puede_pagar` consume el uso si lo concede, en una sola operacion:
        # no hay que apuntarlo despues.
        if config.falta():
            # Sin clave no puede haber llamada, asi que no hay nada que cobrar.
            # `va_a_costar` ya lo sabia dos lineas mas arriba y no se usaba
            # para esto: con perfiles declarados y la clave caducada o borrada
            # del Space, CADA consulta descontaba un uso del cupo sin que
            # pudiera salir una sola peticion a la API. `lexicon` pone el aviso
            # de "sin OPENAI_API_KEY", que en este caso si es verdad.
            puede, motivo_pago = False, ""
        else:
            puede, motivo_pago = _puede_pagar(peticion)
        r = consultor().consultar(palabra, oracion, nivel, idioma=idioma,
                                  usar_openai=puede)
    except Exception as e:
        # Si el diccionario no esta, no hubo consulta ni llamada: se devuelve el
        # uso que `_puede_pagar` acaba de cobrar. Antes el lector perdia un uso
        # de su cupo por un fallo que no era suyo.
        #
        # Y `Exception` y no `(FileNotFoundError, OSError)`: `CacheLexico`
        # ejecuta un CREATE TABLE sobre `~/.literalevel/lexicon.db`, y un
        # archivo cortado a media escritura -el disco del Space es efimero-
        # lanza `sqlite3.DatabaseError`, que NO desciende de OSError. Se
        # escapaba hacia Gradio, con el uso ya cobrado y sin devolver.
        cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
        yield _aviso(e), "", gr.update(visible=False)
        return
    # Si la puerta de pago dijo que no, hay que decir POR QUE. Antes
    # `motivo_pago` se tiraba: `lexicon` seguia su camino de "sin clave" y el
    # visitante leia "Sin clave de OpenAI: no hay explicacion de contexto" en
    # un servidor que SI tiene clave. Lo que pasaba era que no habia entrado
    # con su perfil, o que habia agotado su cupo, y no se le decia ninguna de
    # las dos cosas. Los otros dos manejadores de pago si lo mostraban.
    if not puede and motivo_pago:
        r.avisos = ([a for a in r.avisos if "OPENAI_API_KEY" not in a]
                    + [motivo_pago])
    # Y el cupo: `_puede_pagar` cobra ANTES de saber si se va a llamar a
    # OpenAI. Si la respuesta sale de la cache de `lexicon.db` no se gasta un
    # centimo, pero el contador bajaba igual, asi que `tope` no era "llamadas
    # de pago permitidas" como declara `cuentas.py`, sino pulsaciones. Se
    # devuelve el uso. Cobrar primero y devolver despues, y no al reves, para
    # no reabrir la condicion de carrera que `consumir` cerro.
    #
    # Y se mira `llamadas_de_pago`, no `desde_cache`: `desde_cache` solo habla
    # de la EXPLICACION, y el audio se pide aparte y con otra clave. Con eso,
    # "Fetters" acertaba la explicacion en cache -uso devuelto- y pagaba un
    # tts-1 nuevo. Medido: 5 llamadas de pago, 1 uso cobrado.
    elif puede and getattr(r, "llamadas_de_pago", 0) == 0:
        cuentas.devolver(BASE_DATOS_LECTOR, _codigo_de(peticion))
    # Al cuaderno **solo si el diccionario encontro algo**. Sin este filtro
    # acababan dentro las pruebas y los errores de dedo, y la pestana "Mis
    # palabras" se llenaba de cadenas sin sentido. Una palabra que el
    # diccionario no reconoce no es vocabulario aprendido.
    if r.sentido:
        cuaderno.registrar(
            palabra=r.palabra_superficie, lema=r.lema_buscado or r.lema,
            oracion=oracion, categoria=r.categoria, sentido=r.sentido,
            libro=(libro.titulo if libro is not None else None),
            capitulo=(int(idx) + 1 if _cap(libro, idx) is not None else None),
            banda=r.banda_lector, zipf=r.frecuencia_zipf,
            ruta=_archivo_lector("cuaderno.db", peticion))

    if oracion == palabra:
        # Ni capitulo abierto ni oracion escrita. Antes el pie decia
        # "Contexto: sin contexto: la desambiguacion sera peor", que se
        # contradice solo, y encima citaba la palabra suelta como si fuera
        # una frase del libro. Mejor decir la verdad y no fingir contexto.
        cola = ("\n\n_No había ningún capítulo abierto ni escribiste una "
                "oración, así que busqué la palabra suelta: el sentido "
                "elegido puede no ser el que te interesa._"
                if idioma != "en" else
                "\n\n_No chapter was open and you did not type a sentence, so "
                "I looked the word up on its own: the sense picked may not be "
                "the one you need._")
    else:
        contexto = "Contexto" if idioma == "es" else "Context"
        cola = f"\n\n> {_fragmento_para_leer(oracion, palabra)}\n\n_{contexto}: {origen}._"
    ficha = _ficha(r, idioma) + cola
    local = _local(r.audio_us) or _local(r.audio_uk)
    yield ficha, _reproductores(r), gr.update(value=local, visible=bool(local))


# Por que capitulo va cada lector, para no repetir siempre la misma frase.
_RONDA_FRASE: dict[tuple, int] = {}


def _frase_del_capitulo(libro, idx):
    """Manda la primera oracion de largo razonable a la practica de voz.

    Devuelve `gr.update()` -es decir, no toca nada- cuando no hay frase que
    traer. Antes devolvia cadena vacia, asi que quien habia escrito su frase
    a mano y pulsaba el boton por curiosidad **se quedaba sin ella**, sin un
    solo mensaje que lo explicara.
    """
    if libro is None or idx is None:
        return gr.update()
    c = _cap(libro, idx)
    if c is None:
        return gr.update()
    # Por parrafos, no por el capitulo entero: los encabezados ("I", "The Dead
    # House") no llevan punto, asi que la primera "oracion" del texto crudo se
    # los traga enteros y sale una frase absurda para leer en voz alta.
    candidatas = []
    for parrafo in re.split(r"\n\s*\n", c.texto):
        limpio = " ".join(parrafo.split())
        if len(limpio.split()) < 30:      # titulillo o linea suelta
            continue
        for f in _oraciones(_sin_encabezado(limpio)):
            # Y que EMPIECE donde empieza una frase: la primera candidata de
            # *Alicia* era `” thought Alice to herself, ...`, que es el
            # final de otra.
            # Y que no sea un indice ni un titulo (ver `_parece_indice`).
            if 6 <= len(f.split()) <= 25 and _empieza_entera(f) and not _parece_indice(f):
                candidatas.append(f)
    if not candidatas:
        return gr.update()
    # Una distinta en cada pulsacion. Antes devolvia siempre la primera del
    # capitulo, asi que practicar dos veces seguidas era practicar lo mismo:
    # el boton parecia roto aunque estuviera haciendo su trabajo.
    clave = (getattr(libro, "titulo", ""), int(idx))
    n = _RONDA_FRASE.get(clave, -1) + 1
    _RONDA_FRASE[clave] = n
    return candidatas[n % len(candidatas)]


# --- Punto 5: pronunciacion ----------------------------------------------

_CSS_VOZ = """<style>
/* Este bloque llega DESPUES de `#ll-css` en el DOM y con la misma
   especificidad, asi que su `border` abreviado reescribia entero el
   `border-color:var(--ll-borde)` de alli, y el `color:inherit` tapaba
   `--ll-lector-texto`. Era, palabra por palabra, el mismo fallo que se
   corrigio en `#ll-lector` y que aqui se quedo sin corregir. */
#ll-voz{padding:1.1rem 1.3rem;border:1px solid var(--ll-borde);
  border-radius:10px;font-family:Georgia,"Times New Roman",serif;
  /* `!important` por lo mismo que en `#ll-lector`: esto vive dentro de un
     `div.prose` y la regla de la paleta le ganaba. */
  font-size:21px;line-height:2.1;color:var(--ll-lector-texto) !important}
#ll-voz .ll-w{padding:.12em .34em;border-radius:5px;margin:0 .06em;
  border-bottom:3px solid transparent}
/* Verde de acierto y rojo de fallo. Salen de la paleta y no del CSS porque
   NO hay un par de colores que valga para las cinco: medidos contra el fondo
   del lector, el verde clavado daba 2,21-2,30 en las tres paletas claras y el
   rojo 2,86-2,95 sobre su propio fondo, los dos por debajo del 3:1 que WCAG
   pide a un objeto grafico. Y oscurecerlos para las claras los hunde en las
   oscuras: el rojo a x0,8 sube a 4,04 en amanecer y cae a 2,45 en
   medianoche. El significado no cambia -verde es bien y rojo es mal en las
   cinco-, solo el tono. */
#ll-voz .ok{border-bottom-color:var(--ll-bien)}
#ll-voz .mal{background:var(--ll-mal-fondo);border-bottom-color:var(--ll-mal);
  font-weight:600}
#ll-voz .leyenda{display:block;margin-top:1rem;font-family:system-ui,sans-serif;
  font-size:13px;opacity:.78;line-height:1.5}
#ll-voz .oido{display:block;margin-top:.5rem;font-family:system-ui,sans-serif;
  font-size:14px;opacity:.85;font-style:italic}
</style>"""


def _palabras_html(ev, transcripcion_ok: bool) -> str:
    """La frase objetivo palabra a palabra: cual sono bien y cual no.

    Es lo que de verdad quiere ver quien practica. El numero global dice poco;
    saber que fallaste en 'fortress' y no en 'the' es lo accionable.
    """
    if not ev.palabras_objetivo:
        return ""
    if not transcripcion_ok:
        # Sin clave no se llega aqui (`_practicar_voz` avisa antes): lo normal es una
        # grabacion en silencio o lo que whisper inventa sin voz (reinicio 24, 0a759a5).
        return (_CSS_VOZ + '<div id="ll-voz"><span class="leyenda">'
                'No te oí. Acércate al micrófono y vuelve a grabar.</span></div>')
    fallo = set(ev.palabras_falladas)
    trozos = [
        f'<span class="ll-w {"mal" if w in fallo else "ok"}">{_html.escape(w)}</span>'
        for w in ev.palabras_objetivo
    ]
    bien = len(ev.palabras_objetivo) - len(fallo)
    oido = _html.escape(ev.transcripcion or "(no se entendió nada)")
    return (_CSS_VOZ + '<div id="ll-voz">' + " ".join(trozos)
            + f'<span class="oido">Se te entendió: “{oido}”</span>'
            + f'<span class="leyenda">Subrayado verde: bien pronunciada '
              f'({bien} de {len(ev.palabras_objetivo)}). Fondo rojo: no se '
              f'entendió como esa palabra ({len(fallo)}).</span></div>')


def _reproductor_fonema(ruta: str, fonema) -> str:
    """Un `<audio>` que apunta al mp3 pregrabado del fonema.

    Va como HTML dentro del Markdown del veredicto, y no como otro `gr.Audio`:
    una correccion trae tantos fonemas como palabras falladas, y un componente
    por fonema obligaria a cambiar las salidas de `b_practicar`. Gradio lo
    sirve por `gradio_api/file=` porque la carpeta esta en `RUTAS_PERMITIDAS`.
    La ruta es relativa (sin `/` delante) para que valga tambien si la app se
    monta bajo un prefijo.
    """
    from urllib.parse import quote
    src = "gradio_api/file=" + quote(Path(ruta).as_posix(), safe="/:")
    etiqueta = _html.escape(f"Escuchar el sonido /{fonema.simbolo}/", quote=True)
    return (f'<audio controls preload="none" aria-label="{etiqueta}" '
            f'title="{etiqueta}" src="{_html.escape(src, quote=True)}" '
            'style="height:2.2rem;max-width:100%;vertical-align:middle"></audio>')


def _detalle_de_voz(d, audio_palabra: str | None = None) -> str:
    """Una palabra de la correccion: su IPA, su fonema con audio y la explicacion.

    La IPA de la palabra sale de los diccionarios locales -Kaikki y, si no la
    trae, CMUdict- y SOLO de ahi (`fonemas.ipa_de_palabra`): si ninguno la
    tiene, se dice, y no se le pide al modelo, que la inventaria sin avisar.
    El fonema y el consejo ya no son del modelo: `voz.fijar_fonemas` los saca
    de comparar la IPA esperada con la entendida y de `articulacion.FICHAS`;
    si no hay fonema (`ninguno`), se pinta el texto sin reproductor.
    Nunca lanza: lee los campos con `getattr` para que un detalle a medias no
    tire la correccion entera, que ya se ha pagado.
    """
    cruda = str(getattr(d, "palabra", "") or "").strip()
    palabra = _html.escape(cruda, quote=False)
    ipa, variante = fonemas.ipa_de_palabra(cruda)
    if ipa:
        cabeza = f"- **{palabra}** {_html.escape(ipa, quote=False)} ({variante})"
        # Si Kaikki solo trae la britanica, en la misma linea convivirian dos
        # convenciones (/θɔːt/ arriba, /ɔ/ americano abajo). Se dice. Fable.
        if variante == "UK":
            cabeza += " · transcripción británica; el sonido de abajo es el americano"
    else:
        cabeza = f"- **{palabra}** (sin transcripción fonética en el diccionario)"
    trozos = [cabeza]
    # La palabra SOLA. Miguel: «me dices el error en la vocal, pero no como se
    # escucha la palabra sola; tengo que escuchar todo el texto».
    if audio_palabra:
        etiqueta = _html.escape(f"Escuchar «{cruda}» sola", quote=True)
        trozos.append(
            f'Escuchar la palabra: <audio controls preload="none" aria-label="{etiqueta}" '
            f'title="{etiqueta}" src="{_html.escape(_src_audio(Path(audio_palabra)), quote=True)}" '
            'style="height:2.2rem;max-width:100%;vertical-align:middle"></audio>')
    fonema = fonemas.buscar(getattr(d, "fonema", None))
    if fonema is not None:
        linea = (f"Sonido **/{fonema.simbolo}/**, como en "
                 f"*{', '.join(fonema.ejemplos)}*")
        audio = fonemas.audio_de(fonema.simbolo)
        if audio:
            linea += " " + _reproductor_fonema(audio, fonema)
        trozos.append(linea)
    # Como se mueve la boca: primero el sonido solo y luego la palabra entera
    # (Miguel: «primero por sonido y despues en una palabra»). La palabra sale
    # aunque no haya fonema que señalar: con «tragic» entendido como «Mahic» no
    # hay IPA de lo entendido, pero la de «tragic» si. Dentro de un <details>:
    # las imagenes no se descargan hasta abrirlo.
    anim_sonido = _svg_sonido_src(fonema.simbolo, "ga") if fonema is not None else None
    anim_palabra = _svg_palabra_src(ipa, "rp" if variante == "UK" else "ga")
    imagenes = "".join(
        f'<img loading="lazy" src="{_html.escape(src, quote=True)}" '
        f'alt="{_html.escape(alt, quote=True)}" '
        'style="display:block;max-width:100%;height:auto;margin:.3rem 0">'
        for src, alt in ((anim_sonido, f"Corte de la boca: el sonido /{fonema.simbolo if fonema else ''}/"),
                         (anim_palabra, f"Corte de la boca: la palabra «{cruda}»")) if src)
    if imagenes:
        trozos.append(f"<details><summary>Ver cómo se mueve la boca</summary>{imagenes}</details>")
    # El modelo suele cerrar la frase con su punto; poner otro detras dejaba
    # «..» en cada linea.
    # Escapado, como la palabra: es texto del modelo. En pantalla lo limpiaba
    # DOMPurify, pero por la API de Gradio salia crudo a cualquier cliente.
    # Lo encontro Fable (auditoria 18).
    sonido = _html.escape(str(getattr(d, "sonido_que_falla", "") or "").strip().rstrip("."),
                          quote=False)
    boca = _html.escape(str(getattr(d, "como_colocar_la_boca", "") or "").strip(), quote=False)
    explicacion = " ".join(t for t in (f"{sonido}." if sonido else "", boca) if t)
    if explicacion:
        trozos.append(explicacion)
    # `<br>` y no saltos de linea: el Markdown del veredicto no tiene
    # `line_breaks`, y un salto dentro de un elemento de lista se pinta como
    # un espacio.
    return "<br>".join(trozos)


def _practicar(ruta_audio, frase, peticion: gr.Request = None):
    # Cada practica genera un audio de referencia de pago y nunca acierta en
    # cache (el nombre lleva marca de tiempo), asi que el tope va aqui.
    frase = (frase or "").strip()[:LIMITE_FRASE_VOZ]
    if not frase:
        return "", "Escribe la frase que vas a leer en voz alta.", gr.update(visible=False)
    if not ruta_audio:
        return "", "Graba tu voz con el micrófono (o sube un audio).", gr.update(visible=False)
    # Mismo motivo que en la sinopsis y en la consulta lexica: el cubo por hora
    # solo se gasta si esta pulsacion puede costar dinero.
    va_a_costar = (not config.falta()
                   and cuentas.permite(BASE_DATOS_LECTOR,
                                       _codigo_de(peticion))[0])
    if va_a_costar and not _dentro_del_limite(peticion, "voz", LIMITE_VOZ_HORA):
        return ("", _aviso(_mensaje_limite(
            "es", _minutos_para_la_siguiente("voz", peticion), "voz")),
            gr.update(visible=False))
    # Esta es la funcion mas cara de la aplicacion: transcribe con whisper y
    # genera un audio de referencia, y ninguna de las dos cosas acierta en
    # cache. Por eso es la que se cierra detras del codigo.
    #
    # Y la misma guardia que `_consultar` y `_de_que_trata`, que aqui faltaba:
    # sin clave no puede haber llamada, asi que no hay nada que cobrar. Con
    # perfiles declarados y la clave caducada o borrada del Space, CADA intento
    # de pronunciacion descontaba un uso del cupo sin que saliera una sola
    # peticion a la API -y esta es ademas la unica de las tres que, a
    # proposito, no devuelve el uso cuando no hay transcripcion-.
    if config.falta():
        return ("", _aviso("Para corregir la pronunciación hace falta la clave "
                           "de OpenAI. Lo demás de la aplicación no la necesita "
                           "y sigue funcionando."),
                gr.update(visible=False))
    # El codigo que se cobra, leido ANTES de cobrar: la devolucion por silencio va a esa
    # cuenta aunque la sesion cambie durante whisper (reinicio 26, como `_corregir_voz`).
    codigo_cobrado = _codigo_de(peticion)
    puede, motivo_pago = _puede_pagar(peticion, codigo_cobrado)
    if not puede:
        return "", motivo_pago, gr.update(visible=False)
    try:
        # Los fallos se registran aparte, en la base de ESTE lector: las
        # palabras que a uno se le atragantan no son asunto de los demas.
        # `origen` solo va al registro de las grabaciones sin voz (4e, 06a7aac).
        s = voz.practicar(ruta_audio, frase, guardar_fallos=False, origen="gradio")
        # Whisper respondio y no oyo ninguna palabra: el uso se devuelve, con el tope diario
        # por cuenta de `cuentas` (Central, reinicio 26). Con la red caida `sin_voz` es False.
        devuelto = bool(getattr(s, "sin_voz", False)) and cuentas.devolver_por_silencio(BASE_DATOS_LECTOR, codigo_cobrado)
        if s.evaluacion.palabras_falladas and s.transcripcion_ok:
            voz.registrar_fallos(s.evaluacion.palabras_falladas,
                                 ruta=_archivo_lector("voz.db", peticion), frase=frase)
    except Exception as e:
        # Tampoco se devuelve aqui, y por lo mismo: `voz.practicar` puede haber
        # reventado DESPUES de llamar a gpt o a tts-1, y desde fuera no hay
        # forma de saberlo. Entre cobrar un uso que quiza no se gasto y abrir
        # un camino para gastar sin limite, se cobra. Si algun dia `SesionVoz`
        # dice cuantas llamadas hizo, esto se puede afinar.
        return "", _aviso(e), gr.update(visible=False)

    ev = s.evaluacion
    L = [f"## {ev.puntuacion:.0f} / 100"]
    if not s.transcripcion_ok:
        # Sin transcripcion, el uso se devuelve SOLO si whisper respondio sin ninguna
        # palabra (`sin_voz`), y dentro del tope diario de `cuentas.devolver_por_silencio`
        # (`devuelto`, arriba; reinicio 26). Con la red o la clave caidas no se sabe que se
        # gasto, y se cobra.
        #
        # Por que no se devuelve siempre: hubo unas horas en que se devolvia con cualquier
        # transcripcion fallida («sin transcripcion no hubo whisper, no se gasto nada»), y
        # era FALSO: `evaluar_pronunciacion` contra "" marcaba todas las palabras como
        # falladas, eso llamaba a `explicar_correccion` (gpt) y `generar_audio_correcto`
        # (tts-1) iba siempre. Un perfil de tope 3 podia gastar sin limite. Desde 0a759a5 y
        # 681544f, sin voz ya no hay gpt ni tts-1, y el tope diario cierra lo que queda.
        #
        # El aviso es el de la grabacion sin voz: sin `OPENAI_API_KEY` se sale arriba con
        # su propio aviso, asi que aqui la causa es silencio, ruido o un fallo de red.
        L = [L[0].replace(f"{ev.puntuacion:.0f} / 100", "— / 100")]
        L.append("[!] No te oí. Acércate al micrófono y vuelve a grabar."
                 + (" Este intento no cuenta." if devuelto else ""))
    elif not ev.palabras_falladas:
        L.append("Ni una palabra fallada. Sube el listón con una frase más larga.")

    if s.correccion:
        L.append(f"**Cómo corregirlo:** {_html.escape(str(s.correccion.resumen or ''), quote=False)}")
        # Cada detalle en su propia linea de la lista, con su IPA y el audio
        # del fonema: ver `_detalle_de_voz`.
        audios = getattr(s, "audios_palabras", None) or {}

        def _audio_de(d):
            normal = voz.normalizar_palabras(str(getattr(d, "palabra", "") or ""))
            if not normal:
                return None
            # La pieza de un compuesto («war» de «war-chant») usa su propio
            # audio y, si no lo hay, el del compuesto que la contiene.
            return audios.get(normal[0]) or next(
                (r for k, r in audios.items() if "-" in k and normal[0] in voz.piezas(k)), None)

        L.append("\n".join(_detalle_de_voz(d, _audio_de(d)) for d in s.correccion.detalles))
    # El reproductor nace oculto, asi que devolver la ruta pelada asignaria el
    # valor y lo dejaria invisible: se generaba el audio, se pagaba y no se
    # veia nunca. Hay que encenderlo explicitamente.
    return (_palabras_html(ev, s.transcripcion_ok), "\n\n".join(L),
            gr.update(value=s.audio_correcto, visible=bool(s.audio_correcto)))


def _mal_pronunciadas(peticion: gr.Request = None) -> str:
    """Las palabras que el lector pronuncio mal, con la frase donde fallo.

    Miguel (13 sep): que se queden en «Mis palabras», no solo las buscadas,
    para practicarlas. Lee la base de ESTE lector.
    """
    try:
        filas = voz.palabras_para_practicar(n=30, ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        return f"<p>{_html.escape(_aviso(e))}</p>"
    if not filas:
        return ("<p>Todavía no hay palabras mal pronunciadas. Cuando practiques en "
                "«Pronunciar», las que fallen aparecerán aquí con su frase.</p>")
    trozos = ['<div id="ll-malpron"><p><b>Para practicar en voz alta</b> · copia la '
              'frase en «Pronunciar» y vuelve a intentarlo.</p><ul>']
    for f in filas:
        frase = (f" — <i>{_html.escape(_fragmento_para_leer(str(f['frase']), str(f['palabra'])))}</i>"
                 if f.get("frase") else "")
        vez = "vez" if f["fallos"] == 1 else "veces"
        trozos.append(f"<li><b>{_html.escape(str(f['palabra']))}</b> · {int(f['fallos'])} {vez}{frase}</li>")
    trozos.append("</ul></div>")
    return "".join(trozos)


def _debiles(peticion: gr.Request = None):
    try:
        filas = voz.puntos_debiles(n=15, ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        return _aviso(e)
    if not filas:
        return "Aún no hay palabras registradas. Practica una frase primero."
    return ("Tus palabras más falladas:\n\n"
            + "\n".join(f"{i + 1}. **{w}** — {n} vez{'es' if n > 1 else ''}"
                        for i, (w, n) in enumerate(filas)))


# --- Cuaderno: lo unico que sobrevive a cerrar la app ---------------------

_CSS_CUADERNO = """<style>
#ll-cuaderno{display:flex;flex-direction:column;gap:.7rem}
/* El fondo sale de la paleta, no clavado. Estaba en rgba(8,16,28,.55),
   que es un azul casi negro: en las paletas claras dejaba el texto entre
   2,5 y 3,9:1 en los dos modos. */
#ll-cuaderno .ll-c{padding:.75rem .9rem;border:1px solid var(--ll-borde);
  border-radius:9px;background:var(--ll-panel);color:var(--ll-texto)}
/* Sin esto, una palabra larguisima o una URL desbordan la pantalla del movil
   y la pestana entera se convierte en un muro ilegible. */
#ll-cuaderno .ll-c *{overflow-wrap:anywhere;word-break:break-word}
#ll-cuaderno .ll-p{font-weight:700;font-size:1.05rem}
#ll-cuaderno .ll-d{opacity:.78;font-size:.82rem;font-weight:400}
#ll-cuaderno .ll-f{margin:.4rem 0 .3rem;padding-left:.7rem;
  /* Azul hielo clavado: 1,23:1 sobre las paletas claras. Mismo fallo que
     las tarjetas, en el borde que sobrevivio al arreglo. */
  border-left:3px solid var(--ll-acento);
  font-family:Georgia,serif;line-height:1.5}
#ll-cuaderno .ll-s{font-size:.9rem;opacity:.85}
</style>"""


def _recortar(t, n: int) -> str:
    """Texto de una linea y acotado: nada puede desbordar una pantalla."""
    t = " ".join(str(t or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def _fragmento_para_leer(oracion: str, palabra: str, tope: int = 30) -> str:
    """Lo que se ENSEÑA de una oracion larga: la clausula donde esta la palabra.

    La oracion entera sigue siendo el contexto de OpenAI y lo que guarda el
    cuaderno; esto solo decide que se cita en la ficha y en «Mis palabras». En
    Alicia, la de «waistcoat-pocket» es UNA frase de Carroll de 107 palabras
    -«(when she thought it over afterwards…» hasta «…under the hedge.»-, con
    un solo punto y coma: el partidor no puede cortarla y no debe (f4, informe
    final). Hasta `tope` palabras se devuelve tal cual. Si pasa, se toma la
    clausula que contiene la palabra (cortada en «;», «:» o «,») y se le suman
    las vecinas mientras quepan; si la clausula sola ya pasa, una ventana de
    `tope` palabras centrada en la palabra. «…» donde se corta.
    """
    texto = " ".join(str(oracion or "").split())
    palabras = texto.split()
    if len(palabras) <= tope:
        return texto

    def normal(w):
        return "".join(ch for ch in w.lower() if ch.isalnum() or ch in "'-")

    clave = normal(str(palabra or "").split()[0]) if str(palabra or "").strip() else ""

    def es_la_palabra(w):
        n = normal(w)
        return bool(clave) and (n == clave or clave in n.split("-"))

    clausulas, actual = [], []
    for w in palabras:
        actual.append(w)
        if w.endswith((";", ":", ",")):
            clausulas.append(actual)
            actual = []
    if actual:
        clausulas.append(actual)
    idx = next((i for i, cl in enumerate(clausulas) if any(es_la_palabra(w) for w in cl)), None)
    if idx is None:
        return " ".join(palabras[:tope]).rstrip(",;:") + " …"
    if len(clausulas[idx]) <= tope:
        ini = fin = idx
        total = len(clausulas[idx])
        while True:
            crecio = False
            if ini > 0 and total + len(clausulas[ini - 1]) <= tope:
                ini -= 1
                total += len(clausulas[ini])
                crecio = True
            if fin < len(clausulas) - 1 and total + len(clausulas[fin + 1]) <= tope:
                fin += 1
                total += len(clausulas[fin])
                crecio = True
            if not crecio:
                break
        trozo = [w for cl in clausulas[ini:fin + 1] for w in cl]
        antes, despues = ini > 0, fin < len(clausulas) - 1
    else:
        cl = clausulas[idx]
        pos = next(i for i, w in enumerate(cl) if es_la_palabra(w))
        a = max(0, min(pos - tope // 2, len(cl) - tope))
        trozo = cl[a:a + tope]
        antes = idx > 0 or a > 0
        despues = idx < len(clausulas) - 1 or a + tope < len(cl)
    frase = " ".join(trozo).strip().rstrip(",;:")
    return ("… " if antes else "") + frase + (" …" if despues else "")


def _mis_palabras(peticion: gr.Request = None):
    db = _archivo_lector("cuaderno.db", peticion)
    total, lemas, libros = cuaderno.contar(db)
    if not total:
        return ("<p>Todavía no has consultado ninguna palabra. Abre un libro "
                "en <b>Leer</b>, selecciona una que no conozcas —doble clic "
                "con el ratón, o mantenla pulsada en el móvil— y aparecerá "
                "aquí con la frase en la que la encontraste.</p>")
    tarjetas = []
    for a in cuaderno.ultimas(20, db):
        donde = f" · {_recortar(a.libro, 40)}" if a.libro else ""
        if a.libro and a.capitulo:
            donde += f", cap. {a.capitulo}"
        rareza = f" · {a.rareza}" if a.rareza else ""
        partes = [f'<div class="ll-p">{_html.escape(_recortar(a.palabra, 40))}'
                  f'<span class="ll-d">{_html.escape(rareza + donde)}</span></div>',
                  f'<div class="ll-f">{_html.escape(_fragmento_para_leer(a.oracion, a.palabra))}</div>']
        if a.sentido:
            partes.append(f'<div class="ll-s">'
                          f'{_html.escape(_recortar(a.sentido, 160))}</div>')
        tarjetas.append('<div class="ll-c">' + "".join(partes) + "</div>")
    cabecera = (f"<p><b>{lemas}</b> palabras distintas, en <b>{total}</b> "
                f"consultas sobre <b>{libros}</b> "
                f"libro{'s' if libros != 1 else ''}.</p>")
    return (_CSS_CUADERNO + cabecera
            + '<div id="ll-cuaderno">' + "".join(tarjetas) + "</div>")


def _repasar(peticion: gr.Request = None):
    """Cinco palabras para repasar: las mas raras que has mirado, mas las
    que fallaste al leerlas en voz alta. Sin nota y sin racha: es un
    recordatorio, no un examen."""
    anotaciones = cuaderno.para_repasar(5, _archivo_lector("cuaderno.db", peticion))
    aviso_voz = ""
    try:
        debiles = voz.puntos_debiles(n=5, ruta=_archivo_lector("voz.db", peticion))
    except Exception as e:
        # Un historial que no se puede leer ya no pasa por «nada que repasar»
        # (`voz.HistorialIlegible`): se dice, y el cuaderno se sigue enseñando.
        debiles = []
        aviso_voz = f"<p>{_html.escape(_aviso(e))}</p>"
    if not anotaciones and not debiles and not aviso_voz:
        return ("<p>No hay nada que repasar todavía. Consulta alguna palabra "
                "mientras lees, o practica una frase en voz alta.</p>")
    trozos = [_CSS_CUADERNO, aviso_voz]
    if anotaciones:
        trozos.append("<p><b>Del cuaderno</b> — ¿las recuerdas?</p>"
                      '<div id="ll-cuaderno">')
        for a in anotaciones:
            sentido = (f'<details><summary class="ll-s">Ver el sentido</summary>'
                       f'<div class="ll-s">'
                       f'{_html.escape(_recortar(a.sentido, 160))}</div></details>'
                       if a.sentido else "")
            trozos.append(
                f'<div class="ll-c"><div class="ll-p">'
                f'{_html.escape(_recortar(a.palabra, 40))}</div>'
                f'<div class="ll-f">{_html.escape(_fragmento_para_leer(a.oracion, a.palabra))}'
                f'</div>{sentido}</div>')
        trozos.append("</div>")
    if debiles:
        lista = ", ".join(f"<b>{_html.escape(_recortar(w, 30))}</b> ({n})"
                          for w, n in debiles)
        trozos.append(f"<p><b>De la práctica en voz alta</b><br>{lista}</p>")
    return "".join(trozos)


# --- Mis libros: lo que se esta leyendo y por donde se va ----------------

_CSS_BIBLIO = """<style>
#ll-biblio{display:flex;flex-direction:column;gap:.7rem}
#ll-biblio .ll-l{padding:.8rem .95rem;border:1px solid var(--ll-borde);
  border-radius:9px;background:var(--ll-panel);color:var(--ll-texto)}
#ll-biblio .ll-l *{overflow-wrap:anywhere}
#ll-biblio .ll-t{font-weight:700;font-size:1.05rem}
#ll-biblio .ll-a{opacity:.78;font-size:.85rem}
/* El canal y el relleno de la barra de avance iban clavados en azul hielo
   -rgba(143,211,232,.16) y #3aa9cf->#8fd3e8-, asi que la barra contra su
   propio canal daba 1,47-1,53:1 en las tres paletas claras. Es el mismo
   color clavado que las tarjetas de S3, en el sitio que no se reviso. */
#ll-biblio .ll-b{height:7px;border-radius:4px;margin:.5rem 0 .35rem;
  background:var(--ll-borde);overflow:hidden}
#ll-biblio .ll-b i{display:block;height:100%;
  background:linear-gradient(90deg,var(--ll-acento-hondo),var(--ll-acento))}
#ll-biblio .ll-n{font-size:.85rem;opacity:.8}
#ll-biblio .ll-x{font-size:.82rem;opacity:.78;font-style:italic}
</style>"""


def _mis_libros(peticion: gr.Request = None):
    """La estanteria: que se esta leyendo, por donde y cuanto se ha consultado."""
    todos = biblioteca.listar(_archivo_lector("biblioteca.json", peticion))
    # Los libros cuyo archivo ya no esta no se pintan. No se borran -si el
    # archivo vuelve, el marcapaginas sigue ahi-, pero ensucian: la estanteria
    # es para volver a leer, y a un archivo que no existe no se vuelve.
    libros = [e for e in todos if e.existe]
    ausentes = len(todos) - len(libros)
    if not libros:
        return ("<p>Todavía no has abierto ningún libro. Búscalo en "
                "<b>Buscar</b> o sube el tuyo en <b>Leer</b>, y "
                "aparecerá aquí con el punto donde lo dejaste.</p>",
                gr.update(choices=[], value=None))

    db = _archivo_lector("cuaderno.db", peticion)
    por_libro = {}
    for a in cuaderno.ultimas(500, db):
        if a.libro:
            por_libro[a.libro] = por_libro.get(a.libro, 0) + 1

    tarjetas, opciones = [], []
    for e in libros:
        pct = int(round(e.avance * 100))
        consultadas = por_libro.get(e.titulo, 0)
        nota = (f"Capítulo {e.capitulo + 1} de {e.capitulos} · {pct}% · "
                f"{ficha.miles(e.palabras)} palabras")
        if consultadas:
            nota += f" · {consultadas} palabra{'s' if consultadas != 1 else ''} consultada{'s' if consultadas != 1 else ''}"
        tarjetas.append(
            f'<div class="ll-l"><div class="ll-t">'
            f'{_html.escape(_recortar(e.titulo, 60))}</div>'
            f'<div class="ll-a">{_html.escape(_recortar(e.autor or "autor desconocido", 50))}</div>'
            f'<div class="ll-b"><i style="width:{pct}%"></i></div>'
            f'<div class="ll-n">{_html.escape(nota)}</div></div>')
        opciones.append((f"{e.titulo} — cap. {e.capitulo + 1} de {e.capitulos}",
                         e.ruta))
    pie = ("" if not ausentes else
           f'<p class="ll-x">{ausentes} libro{"s" if ausentes != 1 else ""} '
           f'que abriste ya no está{"n" if ausentes != 1 else ""} en el disco. '
           f'Si vuelves a abrirlo{"s" if ausentes != 1 else ""}, aparecerá'
           f'{"n" if ausentes != 1 else ""} otra vez por donde ibas.</p>')
    return (_CSS_BIBLIO + '<div id="ll-biblio">' + "".join(tarjetas) + "</div>" + pie,
            gr.update(choices=opciones, value=opciones[0][1] if opciones else None))


def _seguir_leyendo(ruta_libro, peticion: gr.Request = None):
    """Reabre un libro de la estanteria por el capitulo donde se quedo."""
    # El desplegable de capitulos NO se vacia mientras esto trabaja, por lo
    # mismo que en `_abrir_del_catalogo`: quitarle las opciones a un
    # componente que conserva su valor hace que Gradio pinte un Error rojo
    # encima del libro. Aqui se quedo sin arreglar la primera vez.
    vacio = gr.update(choices=[], value=None)
    sin_tocar = gr.update()
    if not ruta_libro:
        yield (None, sin_tocar, _html_lectura(""), gr.update(), gr.Tabs(),
               "Elige uno de tus libros.")
        return
    yield (None, sin_tocar, _html_lectura(""), gr.update(), gr.Tabs(),
           "Abriendo…")
    # El capitulo guardado se lee ANTES de abrir: `_abrir` vuelve a anotar el
    # libro en la biblioteca con su capitulo inicial, asi que leerlo despues
    # devolvia siempre el principio y "retomar" no retomaba nada.
    guardado = next((e for e in biblioteca.listar(
        _archivo_lector("biblioteca.json", peticion)) if e.ruta == str(ruta_libro)), None)
    libro, upd, html, resumen = _abrir(ruta_libro, peticion)
    if libro is None:
        yield None, vacio, _html_lectura(""), resumen, gr.Tabs(), resumen
        return
    idx = upd["value"]
    if guardado and 0 <= guardado.capitulo < len(libro.capitulos):
        idx = guardado.capitulo
        # Y se devuelve el marcapaginas al capitulo de verdad.
        _guardar_sesion(ruta_libro, libro.titulo, idx, peticion)
        biblioteca.anotar(ruta_libro=str(ruta_libro), titulo=libro.titulo,
                          autor=libro.autor, capitulos=len(libro.capitulos),
                          capitulo=idx, palabras=libro.palabras,
                          ruta=_archivo_lector("biblioteca.json", peticion))
    c = libro.capitulos[idx]
    yield (libro, gr.update(choices=upd["choices"], value=idx),
           _html_lectura(c.texto),
           f"**{libro.titulo}** — retomas en el capítulo {idx + 1} de "
           f"{len(libro.capitulos)}: _{c.titulo}_.",
           gr.Tabs(selected="leer"), "")


# --- Punto 6: diagnostico para la demo -----------------------------------

def _diagnostico():
    L = ["### Claves", "```", config.estado(), "```"]
    if config.falta():
        L.append("Sin `OPENAI_API_KEY` la app sigue funcionando: diccionario, "
                 "IPA, audio de Wiktionary, buscador y puntuación no usan red. "
                 "Lo que se apaga es la explicación contextual y la voz.")

    L.append("### Recursos")
    # Vale una carpeta local Y vale un repositorio del Hub, igual que en
    # `scoring.Puntuador`. Se corrigio alli y no aqui, asi que la pestana
    # Estado decia "FALTA" del mismo modelo que la app acababa de usar
    # para puntuar. Un diagnostico que miente es peor que no tenerlo.
    from scoring import _parece_repo_hf
    if os.path.isdir(RUTA_MODELO):
        donde = "carpeta local"
    elif _parece_repo_hf(str(RUTA_MODELO)):
        donde = "repositorio de Hugging Face"
    else:
        donde = None
    L.append(f"- Modelo v4: {donde or 'FALTA'} — `{RUTA_MODELO}`")
    from lexicon import RUTA_DICCIONARIO
    dic = Path(RUTA_DICCIONARIO)
    tam = f"{dic.stat().st_size / 1e6:.0f} MB" if dic.exists() else "FALTA"
    L.append(f"- Diccionario Kaikki: {tam}")
    # `LITERALEVEL_CUENTAS` se edita a ciegas en el panel del Space, y hasta
    # ahora una entrada mal escrita se descartaba sin que nadie lo supiera.
    # Aqui se ve el recuento; los motivos los da `cuentas.problemas()` y no
    # incluyen ninguna contrasena.
    validos, declarados = len(cuentas._tabla()), cuentas.declaradas()
    if declarados:
        L.append(f"- Perfiles: {validos} válidos de {declarados} declarados")
        for a in cuentas.problemas():
            L.append(f"  - ⚠️ {a}")
    else:
        L.append("- Perfiles: ninguno declarado, así que no hay puerta y todo "
                 "está abierto")
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
        gr.HTML(_CSS_GLOBAL, elem_id="ll-css")
        # La paleta va en su PROPIO <style>, aparte del estructural: cambiarla
        # solo reescribe una docena de variables y no vuelve a mandar toda la
        # hoja de estilo ni puede descolocar nada.
        paleta_css = gr.HTML(_css_paleta(paletas_mod.POR_DEFECTO),
                             elem_id="ll-paleta-css")
        # Cabecera con el boton de ajustes a la derecha. Laura (12 sep): «lo
        # que pones en los tres circulitos son configuraciones, no son
        # funcionalidades». Los colores y el estado del servicio eran dos
        # pestanas mas, al mismo nivel que leer o pronunciar, y en el movil
        # empujaban las funciones al menu «...». El profesor dijo lo mismo
        # con otras palabras: Colores tomaba demasiada presencia.
        with gr.Row(elem_id="ll-cabecera", equal_height=True):
            gr.Markdown(
                "# LiteraLevel\nLee en inglés al nivel que te toca.\n\n"
                "**1)** Fija tu nivel · **2)** busca algo que te apetezca leer · "
                "**3)** léelo aquí y consulta las palabras que se te atraganten. "
                "Las pestañas están en ese orden.")
            b_ajustes = gr.Button("⚙ Ajustes", size="sm", scale=0, min_width=110,
                                  elem_id="ll-b-ajustes")
        est_ajustes = gr.State(False)
        with gr.Column(visible=False, elem_id="ll-ajustes") as panel_ajustes:
            gr.Markdown(
                "## Ponlo como te guste\n"
                "Se cambia al momento y no se pierde nada de lo que "
                "estés leyendo.")
            paleta = gr.Radio(choices=paletas_mod.opciones(),
                              value=paletas_mod.POR_DEFECTO,
                              label="Paleta de colores")
            with gr.Accordion("Estado del servicio", open=False):
                diag = gr.Markdown()
                gr.Button("Comprobar").click(_diagnostico, None, diag)
                demo.load(_diagnostico, None, diag)
        b_ajustes.click(lambda v: (not v, gr.Column(visible=not v)),
                        est_ajustes, [est_ajustes, panel_ajustes])
        # Vacio a proposito: lo rellena _perfil_inicial en demo.load, que
        # si sabe de que lector se trata. Construir la interfaz ocurre una
        # vez por proceso, no una vez por visitante.
        # --- Entrar con tu perfil -------------------------------------
        # Arriba del todo y ABIERTO, no en un acordeon dentro de una pestana.
        # Tres de las funciones cuestan dinero porque llaman a un servicio
        # externo; el resto es libre. Solo aparece si esta copia tiene
        # perfiles configurados: en el ordenador de casa no hay a quien
        # limitar, y una caja pidiendo una llave que no existe solo confunde.
        # `None` cuando no hay perfiles: la caja no existe y `demo.load` no
        # puede encadenar `_estado_de_entrada` contra un componente que no se
        # ha creado. Lo encontro la prueba de `construir()`, no yo.
        estado_codigo = None
        if cuentas.hay_codigos():
            with gr.Accordion("Entrar con tu perfil", open=True):
                gr.Markdown(
                    "Con tu **usuario y contraseña** se activan las tres cosas "
                    "que llaman a un servicio externo: **explicar una palabra "
                    "en su frase**, **«¿de qué trata?»** y la **corrección de "
                    "pronunciación**.\n\n"
                    "Todo lo demás —medir un texto, buscar, leer el libro "
                    "entero, la curva por capítulos, el diccionario y la "
                    "fonética— **funciona sin entrar**.")
                with gr.Row():
                    caja_usuario = gr.Textbox(
                        label="Usuario", placeholder="tu usuario",
                        scale=2, autofocus=False)
                    caja_clave = gr.Textbox(
                        label="Contraseña", type="password",
                        placeholder="tu contraseña", scale=2)
                    b_entrar = gr.Button("Entrar", variant="primary", scale=1)
                    b_salir = gr.Button("Salir", scale=1)
                estado_codigo = gr.Markdown()
                b_entrar.click(_entrar, [caja_usuario, caja_clave], estado_codigo)
                caja_clave.submit(_entrar, [caja_usuario, caja_clave], estado_codigo)
                b_salir.click(_salir, None, estado_codigo)

        est_perfil = gr.State(None)
        est_libro = gr.State(None)
        # La paleta elegida. Va en un State porque el selector se construye
        # mucho mas abajo -en la pestana "Colores"- y la grafica, que la
        # necesita, se cablea antes: un State se declara aqui y se rellena
        # alli.
        est_paleta = gr.State(paletas_mod.POR_DEFECTO)

        with gr.Tabs() as pestanas:
            with gr.Tab("Mi nivel", id="nivel"):
                perfil_md = gr.Markdown(_describir(None))
                nombre = gr.Textbox(label="Tu nombre (opcional)")
                with gr.Accordion("Cuéntame cómo lees", open=True):
                    # `PREGUNTAS` trae un cuarto elemento que dice si admite
                    # varias respuestas. "Que sueles leer" es de esas: quien
                    # lee literatura clasica tambien lee menus, y marcar una
                    # sola le obliga a mentir.
                    radios = []
                    for _, pregunta, opciones, multiple in perfil_mod.PREGUNTAS:
                        elecciones = [(t, v) for t, v in opciones]
                        radios.append(
                            gr.CheckboxGroup(choices=elecciones, label=pregunta,
                                             info="Puedes marcar varias")
                            if multiple else
                            gr.Radio(choices=elecciones, label=pregunta))

                with gr.Accordion("Y ahora lee esto, con sinceridad", open=True):
                    gr.Markdown("Tres fragmentos de verdad, de menos a más "
                                "difícil. Pesan más que lo anterior: delante "
                                "de un texto real uno se juzga mejor que "
                                "describiéndose.")
                    for f in getattr(perfil_mod, "FRAGMENTOS", []):
                        # Con la tipografia del lector, para que se lea como
                        # un libro y no como un formulario.
                        gr.HTML(_html_lectura(f["texto"]))
                        gr.Markdown(f"_{f['obra']} — {f['autor']}_")
                        radios.append(gr.Radio(
                            choices=[(t, v) for t, v in f["opciones"]],
                            label=f["pregunta"]))

                b_cuest = gr.Button("Estimar mi nivel", variant="primary")
                # El resultado, tambien AQUI ABAJO. Arriba del todo se queda
                # fuera de pantalla en un movil y no te enteras de que ha
                # terminado; es la misma salida pintada dos veces.
                perfil_md_abajo = gr.Markdown()
                # Sale solo cuando ya hay nivel. Sin esto habia que subir toda
                # la pantalla a mano para llegar a las pestanas, justo despues
                # de un formulario largo: el peor momento para pedir scroll.
                b_ir_buscar = gr.Button("Ver libros para mi nivel  →",
                                        variant="primary", visible=False)
                with gr.Accordion("O mídelo con un libro que ya hayas leído",
                                  open=False):
                    gr.Markdown("Si ya leíste un libro en inglés y te resultó "
                                "cómodo, súbelo: se miden ocho partes "
                                "repartidas por toda la obra, no solo el "
                                "principio.")
                    libro_nivel = gr.File(label="Tu libro (.epub, .pdf, .txt)",
                                          file_types=[".epub", ".pdf", ".txt"],
                                          type="filepath")
                    b_libro = gr.Button("Medir con este libro", variant="primary")

                with gr.Accordion("O pega un fragmento a mano", open=False):
                    muestra = gr.Textbox(lines=8, label="Pega aquí unas 200 palabras "
                                                       "en inglés que leas sin esfuerzo")
                    b_muestra = gr.Button("Medir con este texto")
                    gr.Markdown("_La primera vez tarda: carga el modelo v4 (328 MB)._")

                salidas_nivel = [est_perfil, perfil_md, perfil_md_abajo]
                b_cuest.click(_desde_cuestionario, [est_perfil, nombre] + radios,
                              salidas_nivel)
                b_libro.click(_nivel_desde_libro, [est_perfil, nombre, libro_nivel],
                              salidas_nivel,
                              concurrency_id="modelo", concurrency_limit=1)
                b_muestra.click(_desde_muestra, [est_perfil, nombre, muestra],
                                salidas_nivel,
                                concurrency_id="modelo", concurrency_limit=1)
                est_perfil.change(lambda p: gr.update(visible=p is not None),
                                  est_perfil, b_ir_buscar)

            # Rotulos cortos a proposito: en un movil de 390 px, con «Buscar
            # lectura» y «Pronunciación», solo cabian dos pestanas y las demas
            # funciones acababan escondidas en el menu «...».
            with gr.Tab("Buscar", id="buscar"):
                with gr.Row():
                    consulta = gr.Textbox(label="¿De qué te apetece leer?", scale=4,
                                          placeholder="una novela de detectives victoriana")
                    n_res = gr.Number(value=10, label="¿Cuántos te propongo?",
                                      precision=0, minimum=1, maximum=50,
                                      scale=1,
                                      info="Cuántos libros quieres en la lista")
                # La etiqueta dice lo que la casilla HACE. Decia "Solo libros
                # que pueda leer / Deja fuera lo que te quede muy grande o muy
                # pequeno", y no deja fuera nada: `catalogo.buscar` suma la
                # afinidad de nivel con peso 0,3 al parecido, o sea que ACERCA
                # los resultados sin excluir ninguno. Medido: con nivel 0,2
                # seguian saliendo cuatro B1, y con 2,0 tres B1.
                ajustar = gr.Checkbox(value=True,
                                      label="Acercar los resultados a mi nivel",
                                      info="Pesa tu nivel además del parecido; "
                                           "no descarta libros")
                # El aviso va ENCIMA del boton que provoca la espera. Debajo
                # de los resultados, en un movil, queda fuera de pantalla y se
                # lee cuando ya no sirve.
                gr.Markdown("_La primera búsqueda tras despertar la "
                            "aplicación carga el buscador del catálogo: "
                            "puede tardar unos segundos. Las siguientes son "
                            "instantáneas._")
                with gr.Row():
                    b_buscar = gr.Button("Buscar", variant="primary")
                    b_recom = gr.Button("Sorpréndeme con algo de mi nivel")
                resultados = gr.Markdown()
                # Los mensajes de "Leerlo ahora" tienen que caer AQUI, en la
                # pestana donde esta el boton. Antes iban a `libro_md`, que
                # vive en la pestana de lectura: el usuario pulsaba y no veia
                # absolutamente nada, ni el error ni la espera.
                estado_abrir = gr.Markdown()
                # Lista visible, no desplegable: en un movil un dropdown
                # largo cuesta de manejar y es facil quedarse en el primero
                # sin darse cuenta de que se puede cambiar.
                elegido = gr.Radio(label="Elige cuál abrir", choices=[])
                b_abrir = gr.Button("Leerlo ahora", variant="primary")

                entradas_busq = [est_perfil, consulta, ajustar, n_res]
                b_buscar.click(_buscar, entradas_busq, [resultados, elegido])
                consulta.submit(_buscar, entradas_busq, [resultados, elegido])
                b_recom.click(_recomendar, [est_perfil, n_res], [resultados, elegido])
                # El boton vive en la pestana del cuestionario pero solo se
                # puede cablear aqui, que es donde ya existen sus salidas.
                # Salta de pestana Y trae la recomendacion hecha: llegar a un
                # buscador vacio despues de contestar seria empezar de cero.
                b_ir_buscar.click(lambda: gr.Tabs(selected="buscar"), None, pestanas
                                  ).then(_recomendar, [est_perfil, n_res],
                                         [resultados, elegido])

            with gr.Tab("Leer", id="leer"):
                # En el movil la cabecera del libro quedaba en una columna de
                # tres palabras por linea junto a la caja de subida. Poner
                # `min_width` a los dos componentes lo EMPEORO -la caja se
                # quedaba sus 300 px y la cabecera salia letra a letra-: una
                # fila de Gradio solo se parte entre COLUMNAS. Con dos columnas
                # de 300 px, a 390 se apilan y en escritorio siguen juntas.
                with gr.Row():
                    with gr.Column(scale=2, min_width=300):
                        archivo = gr.File(label="Tu libro (.epub, .pdf, .txt)",
                                          file_types=[".epub", ".pdf", ".txt"],
                                          type="filepath", height=150)
                    with gr.Column(scale=3, min_width=300):
                        libro_md = gr.Markdown()
                # Cuatro controles en una fila no caben en un movil: a 390 px
                # "Medir dificultad" se queda con unos 80 px. Se parte.
                with gr.Row():
                    b_prev = gr.Button("‹ Anterior", scale=1)
                    # 260 px: en el movil la fila se apila entera. Con el
                    # minimo por defecto se partia en dos y uno.
                    cap = gr.Dropdown(label="Capítulo", choices=[], scale=4, min_width=260)
                    b_next = gr.Button("Siguiente ›", scale=1)
                cap_md = gr.Markdown()
                # La ficha aparece sola al abrir: esta contada, es instantanea
                # y no cuesta nada. Lo de abajo son los dos botones que si
                # tardan -uno lee el libro entero con el modelo, el otro pide
                # el resumen a OpenAI- y por eso hay que pedirlos.
                with gr.Accordion("Ficha del libro", open=True):
                    ficha_md = gr.Markdown()
                    sugeridos = gr.Radio(label="Capítulos a tu nivel",
                                         choices=[], visible=False,
                                         elem_id="ll-sugeridos")
                    b_trata = gr.Button("¿De qué trata? (resumen)")
                    sinopsis_md = gr.Markdown()
                escala = gr.Radio(
                    choices=[("Escala LiteraLevel (0 – 2)", "cifra"),
                             ("Nivel orientativo (A1 – C2)", "cefr")],
                    value="cifra", label="Cómo quieres ver el nivel",
                    info="Salgan como salgan, se enseñan los dos: el número es "
                         "lo que mide el modelo y la letra es la etiqueta más "
                         "cercana.")
                with gr.Accordion("¿Qué significa cada nivel?", open=False):
                    gr.Markdown(_TABLA_CEFR)
                b_medir = gr.Button("¿Cómo de difícil es este capítulo?")
                # Dos botones y no uno con un desplegable: son dos decisiones
                # distintas -"echame un vistazo" y "leelo entero"- y cada una
                # dice en su etiqueta lo que cuesta.
                with gr.Row():
                    b_rapido = gr.Button("Vistazo rápido (unos segundos)")
                    b_analizar = gr.Button("Leer el libro entero (tarda más)",
                                           variant="primary")
                # El numero SALE de las constantes. Decia "unas 80" cuando
                # el producto real es 30 x 2 = 60, porque la cifra se escribio
                # a mano y luego se bajaron los capitulos de 40 a 30.
                gr.Markdown(f"_El vistazo toma unas "
                            f"{RAPIDO_CAPITULOS * RAPIDO_VENTANAS} ventanas "
                            "repartidas por "
                            "toda la obra y tarda segundos. El análisis "
                            "completo lee **todas** las ventanas del libro: en "
                            "uno largo son minutos, y queda guardado para "
                            "siempre. La curva se dibuja mientras avanza._")
                # Su propio hueco: antes la medicion pisaba la posicion del
                # capitulo y cambiar de capitulo borraba la medicion.
                medicion_md = gr.Markdown()
                analisis_md = gr.Markdown()
                # gr.Plot y no gr.BarPlot: con 366 capitulos las barras se
                # fundian en un bloque macizo. Plotly trae zoom y desplazamiento.
                grafica = gr.Plot(label="Dificultad capítulo a capítulo",
                                  show_label=True)
                # --- La palabra, ENCIMA del texto -----------------------
                # Estaba al final de la pestana, debajo del capitulo entero y
                # del indice: el lector hacia doble clic en una palabra y tenia
                # que bajar todo el capitulo para leer que significaba. En un
                # capitulo de Guerra y Paz eso son varias pantallas. Aqui la
                # caja y el resultado quedan a un palmo de donde se lee.
                with gr.Accordion("Consultar una palabra", open=True):
                    gr.Markdown(
                        "**Selecciona una palabra del texto de abajo** y se "
                        "copia aquí sola: doble clic con el ratón, o mantenla "
                        "pulsada si estás en el móvil. La oración de contexto "
                        "se busca en el capítulo abierto.")
                    with gr.Row():
                        palabra = gr.Textbox(label="Palabra", scale=3,
                                             elem_id="ll-palabra")
                        b_palabra = gr.Button("Consultar", variant="primary",
                                              scale=1)
                    ficha = gr.Markdown()
                    audio_web = gr.HTML()
                    audio_local = gr.Audio(label="Pronunciación generada",
                                           type="filepath",
                                           elem_id="ll-audio-palabra",
                                           visible=False)
                    with gr.Accordion("¿Y la oración? La busco yo sola",
                                      open=False):
                        gr.Markdown("No hace falta que copies nada: cuando "
                                    "seleccionas la palabra, busco la frase del "
                                    "capítulo donde aparece y la uso como "
                                    "contexto. Esta caja solo sirve para forzar "
                                    "otra distinta.")
                        oracion = gr.Textbox(label="Oración (opcional)")
                    idioma = gr.Radio(
                        choices=[("Explícamelo en español", "es"),
                                 ("Explain it in English", "en")],
                        value="es", label="Idioma de la explicación",
                        info="El diccionario, la IPA y el audio no cambian: "
                             "siempre vienen de Wiktionary. Esto solo afecta a "
                             "la explicación de contexto y gramática.")

                texto = gr.HTML(_html_lectura(""))

                # Los mandos, OTRA VEZ, debajo del texto. Cuando terminas un
                # capitulo estas al final de la pagina, y los de arriba quedan
                # a una pantalla entera de scroll hacia atras.
                with gr.Row():
                    b_prev2 = gr.Button("‹ Capítulo anterior")
                    b_next2 = gr.Button("Capítulo siguiente ›")
                with gr.Accordion("Índice del libro", open=False):
                    # Lista y no desplegable: en el movil se recorre con el
                    # dedo. Va dentro de un acordeon y con altura limitada
                    # porque hay libros de 366 capitulos.
                    indice = gr.Radio(label="Ir a un capítulo", choices=[],
                                      elem_id="ll-indice")

                archivo.change(_abrir, archivo, [est_libro, cap, texto, libro_md])
                archivo.change(_limpiar_consulta, None,
                               [ficha, palabra, oracion, audio_web, audio_local])
                cap.change(_capitulo, [est_libro, cap], [texto, cap_md])
                # Y vuelve arriba del texto. Laura (12 sep): «doy a siguiente
                # capitulo y me deja ahi mismo abajo, tengo que hacer todo el
                # scroll para irme arriba».
                b_prev.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap
                             ).then(None, None, None, js=JS_AL_TEXTO)
                b_next.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap
                             ).then(None, None, None, js=JS_AL_TEXTO)
                # `concurrency_id` compartido: los cuatro manejadores que
                # cargan el v4 hacen cola ENTRE ELLOS y con nadie mas. Son 2
                # vCPU: dos puntuaciones a la vez no van al doble de rapido,
                # van peor las dos.
                b_medir.click(_medir, [est_libro, cap, escala], medicion_md,
                              concurrency_id="modelo", concurrency_limit=1)
                b_analizar.click(_analizar_libro,
                                 [est_libro, gr.State("completo"), escala,
                                  est_paleta],
                                 [analisis_md, grafica],
                                 concurrency_id="modelo", concurrency_limit=1
                                 # Al acabar la curva ya se sabe que capitulos
                                 # estan a tu alcance: se ofrecen en el acto.
                                 ).then(_capitulos_sugeridos,
                                        [est_libro, est_perfil], sugeridos)
                b_rapido.click(_analizar_libro,
                               [est_libro, gr.State("rapido"), escala,
                                est_paleta],
                               [analisis_md, grafica],
                               concurrency_id="modelo", concurrency_limit=1)
                # Va colgado del State y no de `archivo`, para que la ficha
                # salga tambien cuando el libro llega del buscador y no de una
                # subida. Lo unico que los dos caminos comparten es este State.
                est_libro.change(_ficha_libro, [est_libro, est_perfil], ficha_md)
                # Las sugerencias leen SOLO estados del servidor -el libro y el
                # perfil-, nunca el desplegable: la leccion de la auditoria 17.
                # Y se eligen con `.select`, que solo dispara cuando lo toca
                # una persona, para que repintar las opciones no salte de
                # capitulo solo. El salto va por `_indice_de`, como el indice.
                est_libro.change(_capitulos_sugeridos, [est_libro, est_perfil],
                                 sugeridos)
                est_perfil.change(_capitulos_sugeridos, [est_libro, est_perfil],
                                  sugeridos)
                sugeridos.select(_indice_de, [est_libro, sugeridos], cap)
                est_libro.change(lambda: "", None, sinopsis_md)
                b_trata.click(_de_que_trata, est_libro, sinopsis_md)

                # Los mandos de abajo mueven el MISMO desplegable de arriba,
                # asi que no hay dos estados que puedan discrepar.
                # Y estos son los que pulso Laura: estan DEBAJO del texto, que
                # es donde se acaba el capitulo. Sin el salto la dejaban al
                # final del capitulo nuevo.
                b_prev2.click(lambda l, i: _mover(l, i, -1), [est_libro, cap], cap).then(
                    None, None, None, js=JS_AL_TEXTO)
                b_next2.click(lambda l, i: _mover(l, i, 1), [est_libro, cap], cap).then(
                    None, None, None, js=JS_AL_TEXTO)
                # **`cap` NO entra aqui, y esa es la linea del recuadro rojo.**
                #
                # Cuando cambia el libro, este manejador leia tambien el
                # desplegable de capitulos. Los manejadores que abren un libro
                # son GENERADORAS y cambian `est_libro` y `cap` a la vez, asi
                # que este evento se dispara con el valor VIEJO del desplegable
                # -medido en la traza de red: recibe el capitulo del libro
                # anterior-. Si ese numero no existe en el libro nuevo -leias
                # el 90 de *Karamazov* y abres uno de 24 capitulos- Gradio lo
                # rechaza en `Dropdown.preprocess`, o sea ANTES de llamar a
                # `_indice_de`, y pinta «Value: 89 is not in the list of
                # choices: [0...23]». Por eso validar dentro de `_indice_de` no
                # servia de nada: la funcion no llegaba a ejecutarse.
                #
                # `est_libro` es un `gr.State` y su valor vive en el servidor,
                # asi que ese si llega al dia. Con el libro solo, el indice se
                # repinta con las opciones nuevas y sin seleccion, y el
                # `cap.change` de abajo -donde `cap` es el que dispara, no una
                # entrada rancia- marca el capitulo.
                est_libro.change(_indice_de, est_libro, indice)
                # `.select` y no `.change`: solo dispara cuando lo toca una
                # persona. Con `.change` se hacia un bucle, porque justo abajo
                # se actualiza el indice cada vez que cambia el capitulo.
                #
                # Y manda opciones Y valor, no el valor pelado: con el value
                # suelto, meter un numero en un desplegable cuyas opciones
                # estan vacias un instante es otra forma del mismo Error.
                indice.select(_indice_de, [est_libro, indice], cap).then(
                    None, None, None, js=JS_AL_TEXTO)
                cap.change(_indice_de, [est_libro, cap], indice)
                entradas_lex = [est_perfil, est_libro, cap, palabra, oracion, idioma]
                b_palabra.click(_consultar, entradas_lex,
                                [ficha, audio_web, audio_local])
                palabra.submit(_consultar, entradas_lex,
                               [ficha, audio_web, audio_local])

            with gr.Tab("Pronunciar", id="voz"):
                # La entrada al perfil ya NO vive aqui: esta arriba del todo,
                # antes de las pestanas. Estaba en un acordeon cerrado dentro
                # de esta pestana y no la encontraba nadie.

                frase = gr.Textbox(label="Frase que vas a leer en voz alta",
                                   placeholder="It is a truth universally acknowledged...",
                                   elem_id="ll-frase")
                b_traer = gr.Button("Traer una frase del capítulo que estoy leyendo")
                mi_audio = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                    label="Léela en voz alta")
                with gr.Row():
                    b_practicar = gr.Button("Corrígeme", variant="primary")
                    b_debiles = gr.Button("Mis puntos débiles")
                palabras_html = gr.HTML()
                veredicto = gr.Markdown()
                audio_ref = gr.Audio(label="Cómo debería sonar", type="filepath",
                                 elem_id="ll-audio-ref", visible=False)
                # Laura (12 sep): para probar otra frase habia que volver a la
                # caja, borrarla tecla a tecla y quitar la grabacion. Debajo
                # de la correccion, que es donde se esta al terminar.
                b_otra = gr.Button("Otra frase ↺")
                # Su propia caja, y no la del veredicto. Los dos botones
                # escribian en `veredicto`: pulsar "Mis puntos debiles" borraba
                # la correccion que acababa de costar una llamada de pago, y no
                # habia forma de volver a verla sin pagar otra.
                debiles_md = gr.Markdown()

                b_traer.click(_frase_del_capitulo, [est_libro, cap], frase)
                ev_practicar = b_practicar.click(_practicar, [mi_audio, frase],
                                                 [palabras_html, veredicto, audio_ref])
                b_debiles.click(_debiles, None, debiles_md)
                # `cancels`: sin el, pulsar «Otra frase» mientras llegaba una
                # correccion vaciaba la pantalla y, al terminar, la correccion
                # vieja volvia a aparecer junto a la frase nueva. Lo encontro
                # Codex, reproducido con la voz simulada.
                b_otra.click(lambda: ("", None, "", "",
                                      gr.update(value=None, visible=False)),
                             None, [frase, mi_audio, palabras_html, veredicto, audio_ref],
                             cancels=[ev_practicar]
                             ).then(None, None, None, js=JS_A_LA_FRASE)

            with gr.Tab("Mis libros", id="biblioteca"):
                gr.Markdown("Los libros que has abierto, por dónde vas en cada "
                            "uno y cuántas palabras consultaste en ellos. Se "
                            "guardan solos mientras lees.")
                b_biblio = gr.Button("Ver mis libros", variant="primary")
                biblio_html = gr.HTML()
                seguir = gr.Radio(label="Seguir leyendo", choices=[])
                b_seguir = gr.Button("Retomar donde lo dejé")
                estado_seguir = gr.Markdown()

                b_biblio.click(_mis_libros, None, [biblio_html, seguir])

            with gr.Tab("Mis palabras", id="cuaderno"):
                gr.Markdown("Se llena solo mientras lees. Cada palabra con la "
                            "frase en la que la encontraste, que es lo que "
                            "de verdad la fija.")
                with gr.Row():
                    b_cuaderno = gr.Button("Ver mis palabras", variant="primary")
                    b_repasar = gr.Button("Repasa 5")
                # gr.HTML y no gr.Markdown: hace falta el CSS que parte las
                # palabras largas, o una sola desborda la pantalla del movil.
                cuaderno_md = gr.HTML()

                b_cuaderno.click(_mis_palabras, None, cuaderno_md)
                b_repasar.click(_repasar, None, cuaderno_md)
                # Y las que pronunciaste mal, con su frase (Miguel, 13 sep).
                b_malpron = gr.Button("Palabras que pronuncié mal")
                malpron_html = gr.HTML()
                b_malpron.click(_mal_pronunciadas, None, malpron_html)

            # «IPA» y no «AFI»: es la sigla que el lector ve en diccionarios y
            # apps (International Phonetic Alphabet). Miguel, 13 sep.
            with gr.Tab("Sonidos IPA", id="afi"):
                gr.Markdown(
                    "## Los sonidos del inglés\n"
                    "Los símbolos del **IPA** (International Phonetic Alphabet; en español, "
                    "Alfabeto Fonético Internacional o AFI). Toca uno "
                    "y lo oirás tres veces: **sostenido**, **rápido** y **en una palabra**. "
                    "En «Cómo se articula» tienes la posición de labios, lengua y boca. "
                    "Los audios están grabados de antemano: escucharlos no gasta nada y "
                    "no hace falta entrar.")
                gr.HTML(_tabla_afi_html(), elem_id="ll-afi-tabla")

        # El selector de paleta vive en el panel de ajustes, arriba, pero se
        # cablea aqui: la grafica se declara dentro de la pestana de lectura.
        paleta.change(_css_paleta, paleta, paleta_css)
        # Y la paleta tiene que llegar tambien a lo que NO es CSS: la
        # grafica es una imagen de Plotly con los colores dentro. Si ya
        # hay una curva pintada se repinta; si no, se deja como esta
        # -devolver None la borraria-.
        paleta.change(lambda c: c, paleta, est_paleta)
        paleta.change(_repintar_grafica, [est_libro, paleta], grafica)

        # Cierra el bucle buscar -> leer. Va aqui abajo y no en la pestana del
        # buscador porque necesita componentes de la pestana de lectura, que
        # se declaran despues.
        b_abrir.click(_abrir_del_catalogo, elegido,
                      [est_libro, cap, texto, libro_md, pestanas, estado_abrir])
        b_abrir.click(_limpiar_consulta, None,
                      [ficha, palabra, oracion, audio_web, audio_local])

        # Al abrir, y EN ESTE ORDEN, que no es un detalle: primero se averigua
        # QUIEN es el lector, y solo despues se leen sus datos. Encadenado con
        # `.then()` a proposito: tres `demo.load` sueltos corren a la vez y
        # `_perfil_inicial` podria leer la carpeta equivocada -o la de
        # "anonimo"- antes de que el registro haya llegado. Es el mismo tipo de
        # carrera que el cupo, y aqui se cierra ordenando.
        id_lector = gr.Textbox(visible=False)
        cadena = (demo.load(_registrar_lector, id_lector, None, js=JS_IDENTIDAD)
                  .then(_perfil_inicial, None, [est_perfil, perfil_md]))
        if estado_codigo is not None:
            cadena = cadena.then(_estado_de_entrada, None, estado_codigo)
        cadena.then(_reanudar, None,
                    [est_libro, cap, texto, libro_md, pestanas])

        b_seguir.click(_seguir_leyendo, seguir,
                       [est_libro, cap, texto, libro_md, pestanas, estado_seguir])
        b_seguir.click(_limpiar_consulta, None,
                       [ficha, palabra, oracion, audio_web, audio_local])

        # Engancha el doble clic del lector a la caja de consulta.
        demo.load(None, None, None, js=JS_SELECCION)
        # Y los clics de la tabla del AFI (sonar y cambiar de acento).
        demo.load(None, None, None, js=JS_AFI)
        # Y la voz del navegador para las palabras sin audio.
        demo.load(None, None, None, js=JS_VOZ_NAVEGADOR)

    # La cola: 8 a la vez, y el modelo de uno en uno.
    #
    # Sin esta llamada Gradio usa su valor por defecto, que su propia
    # documentacion fija en 1: UN evento a la vez para todos los visitantes.
    # Con eso, una consulta lexica esperando a OpenAI bloqueaba la aplicacion
    # entera; medido en el Space, otra sesion pulsando "Estimar mi nivel"
    # -aritmetica pura- se quedo 170 s sin respuesta.
    #
    # 8 porque casi todo lo que hace esta app es ESPERAR -a OpenAI, a
    # Gutenberg, a disco-, y esperar no gasta CPU. Lo que si la gasta es el
    # modelo, y ese se limita aparte.
    demo.queue(default_concurrency_limit=8)
    return demo


if __name__ == "__main__":
    construir().launch(theme=TEMA, inbrowser=True,
                       allowed_paths=RUTAS_PERMITIDAS,
                       max_file_size=TAMANO_MAXIMO_SUBIDA)
