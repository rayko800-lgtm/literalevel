---
name: latex-en-esta-maquina
description: Compilar y editar LaTeX en el equipo de Miguel — dónde está tectonic, cómo editar un .tex sin corromperlo (el shell se come las barras invertidas), y qué comprobar antes de dar un PDF por bueno. Úsala antes de tocar cualquier .tex o .bib.
---

# LaTeX en esta máquina

## Compilar

```bash
export PATH="/d/tex/bin:$PATH"
export TECTONIC_CACHE_DIR="D:/tex/cache"
cd /c/Users/laura/literalevel/entrega
tectonic -X compile documento.tex
```

`tectonic` **no está en el PATH** por defecto: vive en `D:\tex\bin` y su caché
en `D:\tex\cache`. Sin la variable se rebaja a descargar los paquetes otra vez.

- Resuelve `biber` solo. No hace falta cadena de cuatro pasadas.
- `Fontconfig error: Cannot load default config file` sale siempre y **no es un
  error**: ignóralo.
- Añade `--keep-logs` solo si vas a mirar los desbordes; si no, el `.log` se
  queda en `entrega/` y ensucia el repo (está en `.gitignore`).

---

## La trampa cara: NO edites LaTeX desde el shell

Esto ha corrompido `documento.tex` **seis veces**, y siempre igual.

### Los heredocs se comen las barras invertidas

```bash
python -X utf8 - <<'PYEOF'      # incluso entrecomillado
t = t.replace('\\textbf{9,51}', ...)
PYEOF
```

Llega a Python como **tabulador + `extbf`**. `\t` se interpreta antes de que
Python vea nada. El resultado es un `.tex` que ya no compila, y el fallo
aparece a cien líneas de donde estabas mirando.

### El shell expande `$0` dentro de comillas dobles

```bash
python -X utf8 -c "t = t.replace('...', '\$0{,}72x')"
```

deja **`/usr/bin/bash{,}72x`** dentro del `.tex`, y el error que salta es
`LaTeX Error: Command \item invalid in math mode` — que no tiene nada que ver
y te hace buscar en el sitio equivocado.

### Lo que sí funciona

**Escribe el guion con la herramienta Write y ejecútalo.** No pasa por el
shell, así que no hay nada que expandir. Dentro del guion, dos costumbres:

```python
BS = chr(92)              # la barra invertida, sin escribirla nunca
TEXTBF = BS + 'textbf'

def tex(s):
    """@ es la barra invertida, para cadenas largas."""
    return s.replace('@', BS)

VIEJO = tex('@textbf{Evaluados} & @textbf{45}')
```

Y comprueba después de cada tanda:

```python
assert chr(9) + 'extbf' not in t      # tabulador + extbf
assert '/usr/bin/bash' not in t
```

Para un cambio de una línea, la herramienta **Edit** es más segura que
cualquier guion.

---

## Antes de dar un PDF por bueno

**1. Referencias rotas.** LaTeX no falla por una `\ref` sin `\label`: imprime
`??` y sigue.

```python
refs = set(re.findall(BS+BS+r'(?:ref|eqref)\{([^}]+)\}', t))
labs = set(re.findall(BS+BS+r'label\{([^}]+)\}', t))
print('rotas:', sorted(refs - labs))
```

**2. Desbordes.** `grep -c "^warning.*Overfull"`. Los de 2–6 pt son invisibles;
a partir de **20 pt** el texto se sale del margen y se ve. Casi siempre es una
palabra en `\cod{}` que no se puede partir: mételes `\allowbreak`.

```latex
\cod{MikeMaki1763/\allowbreak literalevel-v4}
```

**3. Cuadros sin número.** Una tabla dentro de `\begin{center}` **no es un
cuadro**: no lleva número, no sale en el índice de cuadros y no se puede
referenciar. Si el `.md` la cita como «Cuadro 10b», en el PDF no existe.
Conviértela en `table` con `\caption` y `\label`.

**4. Los `.dat` de las figuras.** `datos_figuras/*.dat` es lo que **dibuja** las
gráficas. Si corriges una cifra en las tablas y no ahí, el gráfico contradice a
la tabla de al lado y no se nota releyendo.

**5. El texto del PDF, extraído.** La comprobación definitiva:

```python
from pypdf import PdfReader
todo = ''.join((p.extract_text() or '') for p in PdfReader('presentacion.pdf').pages)
for s in ['0,855', '0,854']:      # la nueva y la vieja
    print(s, 'SI' if s in todo else 'no')
```

Buscar la cadena en los **bytes** del PDF no vale: el texto va comprimido y
siempre da `False`.

---

## La numeración del `.md` y la del `.tex` no coinciden, y está bien

El PDF numera además las tablas que en el `.md` van como listas dentro del
texto, así que «Cuadro 11» del `.md` es «Cuadro 16» del PDF. No intentes
alinearlas: **dilo en la cabecera del `.md`** y que cada archivo referencie su
propia numeración.

---

## Cuadernos

`tools/a_notebook.py` convierte un `.py` con marcas `# %%` en `.ipynb`. El
`.py` es la fuente —se compara entre versiones— y el `.ipynb` es lo que Colab
abre. **Regenéralo siempre después de tocar el `.py`**, o el entregable se
queda con la versión anterior:

```bash
python -X utf8 tools/a_notebook.py entrega/notebook_proyecto.py
```

`ast.parse` no vale para comprobar la sintaxis de un `.py` de Colab: las líneas
`!pip` y `%cd` son magias de IPython. Quítalas antes de parsear.
