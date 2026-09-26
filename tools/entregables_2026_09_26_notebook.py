# -*- coding: utf-8 -*-
"""Pone al día el TEXTO (solo celdas markdown) de notebook_proyecto.py y del
.ipynb a la vez, sin tocar el código ni las salidas guardadas de la ejecución
en Colab. Después comprueba que las celdas del .py regeneradas con
tools/a_notebook.py coinciden con las del .ipynb."""
import json, pathlib, sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PY = RAIZ / 'entrega' / 'notebook_proyecto.py'
NB = RAIZ / 'entrega' / 'notebook_proyecto.ipynb'
sys.path.insert(0, str(RAIZ / 'tools'))
from a_notebook import celdas  # noqa: E402

# (viejo, nuevo) sobre el .py; en el .ipynb se aplica lo mismo sin el «# ».
CAMBIOS = [
    ('# # LiteraLevel — cuadernillo del proyecto', '# # Pléyade (proyecto LiteraLevel) — cuadernillo del proyecto'),
    ('# **Entrega web al 15 de septiembre de 2026:** Angular es la interfaz principal\n'
     '# sobre una API FastAPI; Gradio conserva el motor y la interfaz de respaldo.\n'
     '# Enlace del lector: https://mikemaki1763-literalevel-front.static.hf.space/',
     '# **Entrega web al 26 de septiembre de 2026:** la aplicación se llama **Pléyade**;\n'
     '# Angular es la interfaz principal, publicada en Vercel, sobre una API FastAPI;\n'
     '# Gradio conserva el motor y la interfaz de respaldo.\n'
     '# Enlace del lector: https://pleyade-app.vercel.app (respaldo, la misma app:\n'
     '# https://mikemaki1763-literalevel-front.static.hf.space/)'),
    ('# **LiteraLevel** es una aplicación que mide esa dificultad',
     '# **Pléyade**, la aplicación del proyecto LiteraLevel, mide esa dificultad'),
    ('| Qué le da LiteraLevel |', '| Qué le da Pléyade |'),
    ('permanente está hecho —Angular en `MikeMaki1763/literalevel-front` y\n'
     '#    API/motor en `MikeMaki1763/literalevel`, en Hugging Face Spaces,\n'
     '#    público y en marcha, 7 USD/mes de cuenta Pro— y desde el 10 de septiembre\n'
     '#    de 2026 la estantería, el avance, el cuaderno y el perfil del lector viven\n'
     '#    en un bucket montado en `/data` y sobreviven a un reinicio.',
     'permanente está hecho —Angular en Vercel (`pleyade-app.vercel.app`, gratis),\n'
     '#    con respaldo en `MikeMaki1763/literalevel-front`, y API/motor en\n'
     '#    `MikeMaki1763/literalevel`, en Hugging Face Spaces, 7 USD/mes de cuenta\n'
     '#    Pro— y desde el 10 de septiembre de 2026 la estantería, el avance, el\n'
     '#    cuaderno y el perfil del lector viven en un bucket montado en `/data` y\n'
     '#    sobreviven a un reinicio; desde el 26, con cuenta, son de la cuenta y se\n'
     '#    ven igual en cualquier aparato.'),
    ('Las portadas FLUX no se generaron;\n'
     '#    la demo 3D local no se cuenta como publicada sin verificar su integración.',
     'Las portadas FLUX no se generaron.\n'
     '#    La boca 3D didáctica está publicada desde el 24 de septiembre y se mueve\n'
     '#    con un segundo modelo, aprendido de caras reales (documento, §7.8), que\n'
     '#    este cuaderno no reproduce.'),
]


def sin_comentario(s):
    return '\n'.join(l[2:] if l.startswith('# ') else l.lstrip('#') for l in s.split('\n'))


def main():
    crlf = bytes([13, 10]) in PY.read_bytes()
    py = PY.read_text(encoding='utf-8')
    nb = json.loads(NB.read_text(encoding='utf-8'))
    for v, n in CAMBIOS:
        assert py.count(v) == 1, ('py', v[:60])
        py = py.replace(v, n)
        vv, nn = sin_comentario(v), sin_comentario(n)
        hechos = 0
        for c in nb['cells']:
            if c['cell_type'] != 'markdown':
                continue
            src = ''.join(c['source'])
            if vv in src:
                src = src.replace(vv, nn); hechos += 1
                lin = src.split('\n')
                c['source'] = [l + '\n' for l in lin[:-1]] + [lin[-1]]
        assert hechos == 1, ('ipynb', vv[:60], hechos)
    # Coherencia: las celdas del .py nuevo, contra las del .ipynb nuevo.
    esperadas = celdas(py)
    assert len(esperadas) == len(nb['cells']), (len(esperadas), len(nb['cells']))
    for i, (a, b) in enumerate(zip(esperadas, nb['cells'])):
        assert a['cell_type'] == b['cell_type'] and ''.join(a['source']) == ''.join(b['source']), ('celda', i)
    PY.write_text(py, encoding='utf-8', newline=chr(13) + chr(10) if crlf else chr(10))
    crlf_nb = bytes([13, 10]) in NB.read_bytes()
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + '\n', encoding='utf-8',
                  newline=chr(13) + chr(10) if crlf_nb else chr(10))
    print('ok', len(CAMBIOS), 'cambios; celdas coherentes:', len(esperadas))


main()
