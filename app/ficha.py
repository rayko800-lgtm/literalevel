"""La ficha de un libro: de que trata y como es de leer.

Miguel pidio que al abrir un libro haya "un preview, un overview, un resumen,
me dice de que trata, caracteristicas". La grafica de dificultad ya existe en
`ui.py`; esto es la otra mitad, y son dos cosas distintas a proposito:

- `caracteristicas()` se calcula **aqui, contando**. Cuanto se tarda en leerlo,
  cuanto es dialogo, como de largas son las frases, cuanta palabra distinta
  hay. No necesita red ni clave, no puede inventarse nada, y por eso es lo que
  siempre se ve.
- `sinopsis()` es lo unico que le pide a un modelo de lenguaje: de que va el
  libro, en dos frases, en espanol. Eso no se puede contar, hay que leerlo. Si
  no hay clave de OpenAI, no hay sinopsis y no pasa nada: la ficha se queda con
  lo que se pudo medir, que es la mayor parte.

Esa separacion importa para la defensa del proyecto: ninguna de las cifras de
la ficha viene de un modelo generativo, y la sinopsis viene marcada como lo que
es. Nunca se mezclan en la misma frase.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import scoring

# Un lector adulto en su lengua materna va a 240 palabras por minuto; en una
# lengua extranjera, la horquilla de la investigacion esta bastante por debajo.
# Se usan dos velocidades segun el nivel del texto para no dar una sola cifra
# que seria falsa para casi todo el mundo.
PPM_COMODO = 180        # texto por debajo del nivel del lector
PPM_EXIGENTE = 110      # texto por encima

# El dialogo se mide POR ORACION y no por parrafo. Es una correccion, no un
# capricho: `reader._limpiar_html` colapsa todos los espacios, asi que en un
# epub no queda ni un salto de parrafo. Contando por parrafos reconstruidos, en
# Alice, Pride and Prejudice y Crime and Punishment salia 100% de dialogo en
# los tres, que es una cifra sin ninguna informacion. Por oracion sale la
# diferencia real entre una novela conversada y una narrada.
_DIALOGO_RE = re.compile(r'["“”«»]|(?:^|\s)[—–]\s')

# Nada de esto es el libro: es la licencia y la portadilla de Project
# Gutenberg. Si se cuela, 'gutenberg' y 'project' salen entre las palabras mas
# repetidas de Alicia en el Pais de las Maravillas -salian- y ademas ensucia la
# longitud de frase y la variedad de vocabulario con texto legal.
_BOILERPLATE_RE = re.compile(
    r"project gutenberg|gutenberg-tm|gutenberg™|"
    r"start of (?:the|this) project|end of (?:the|this) project|"
    r"produced by|transcriber'?s note|full project gutenberg",
    re.IGNORECASE)

# Palabras que estan en todos los libros y no dicen de que va ninguno. No es
# una lista de "stopwords" academica: es corta y solo sirve para que las
# palabras distintivas no sean 'the', 'said' y 'would'.
#
# Faltaban dos familias enteras, y se veian en la pantalla del libro: las
# CONTRACCIONES -"Lo que mas se repite: tommy, tuppence, julius, don't, james,
# think, down, young, jane, got"- y los VERBOS CORRIENTES de narracion. Cuatro
# de diez puestos gastados en palabras que estan en todas las novelas.
_VACIAS = frozenset("""
the be to of and a in that have i it for not on with he as you do at this but
his by from they we say her she or an will my one all would there their what
so up out if about who get which go me when make can like time no just him
know take people into year your good some could them see other than then now
look only come its over also back after use two how our work first well way
even new want because any these give day most us is was are were been has had
said upon shall must very much such may own more many might should did does
made men man old great little upon thou thee thy ye sir mr mrs am pm chapter
think thought though thing things something nothing anything everything
got went came going gone asked answered replied cried told tell knew known
seemed seem looked looking felt feel began begin turned turn left put down
never always ever every before without again away while here where why yes
still quite rather perhaps indeed however almost enough perhaps another
don't didn't couldn't wouldn't shouldn't can't won't isn't aren't wasn't
weren't hasn't haven't hadn't doesn't ain't i'm i'll i've i'd it's that's
there's he's she's we're you're they're let's
too himself herself myself itself themselves once last being soon right
suddenly together whole same both each few long part place side end course
moment thus therefore towards toward off took saw let gave done
""".split())

# Cualquier LETRA, no solo la ASCII: con `[A-Za-z]`, "Svidrigaïlov" se partia
# en "svidriga" y "lov", y las dos mitades subian a "lo que mas se repite" de
# *Crimen y castigo* como si fueran palabras. Igual "Natasha" y "Rostov" en
# *Guerra y paz*. Se piden tres letras o mas, como antes.
_PALABRA_RE = re.compile(r"[^\W\d_](?:[^\W\d_]|['’-])*", re.UNICODE)


@dataclass
class Caracteristicas:
    palabras: int
    capitulos: int
    frase_media: float          # palabras por oracion
    dialogo: float              # fraccion de parrafos con marca de dialogo, 0..1
    riqueza: float              # palabras distintas / palabras, sobre una muestra
    distintivas: list[str] = field(default_factory=list)

    def minutos(self, exigente: bool) -> int:
        return max(1, round(self.palabras / (PPM_EXIGENTE if exigente else PPM_COMODO)))

    @property
    def forma_del_dialogo(self) -> str:
        if self.dialogo >= 0.35:
            return "muy conversado: se avanza rápido porque casi todo son voces"
        if self.dialogo >= 0.15:
            return "alterna narración y diálogo"
        return "sobre todo narración seguida, con poco diálogo"


def reloj(minutos: int) -> str:
    """'40 minutos', '2 h 45 min'. Nunca '4 y 2 h', que es lo que salia antes
    de redondear las horas hacia abajo por separado y perder los minutos."""
    if minutos < 90:
        return f"{minutos} minutos"
    h, m = divmod(int(minutos), 60)
    return f"{h} h" if m == 0 else f"{h} h {m:02d} min"


def miles(n) -> str:
    """1.197, no 1,197: en espanol el separador de miles es el punto.

    El `f"{n:,}"` de Python usa la coma, que en espanol es el separador
    DECIMAL. La app llego a decir "Catalogo: 1,197 libros" y "130,104
    palabras" en la misma pantalla en la que el documento escribe 1.197 y
    130.104. Aqui y no en `ui` porque `catalogo` tambien lo necesita.
    """
    return format(int(n), ",").replace(",", ".")


# Gutenberg envuelve cada libro entre dos lineas fijas. Son la unica forma
# fiable de saber donde acaba la obra y empieza la licencia, y hacen falta
# porque el epub de Alicia trae la licencia ENTERA pegada al final del capitulo
# XII: 2.900 de sus 5.042 palabras son texto legal. Excluir el capitulo entero
# tiraria el final del libro; hay que cortar dentro.
_INICIO_PG = re.compile(
    r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", re.I | re.S)
_FIN_PG = re.compile(
    r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.I)
# Cuando el epub se ha comido los asteriscos, la licencia sigue empezando por
# una de estas dos formulas, y siempre en la ultima parte del texto.
_FIN_PG_SUAVE = re.compile(
    r"End of (?:the )?Project Gutenberg(?:'s|’s)? |"
    r"START: FULL LICENSE|THE FULL PROJECT GUTENBERG LICENSE", re.I)


def sin_licencia(texto: str) -> str:
    """El texto de la obra, sin la envoltura legal de Project Gutenberg.

    Devuelve el texto tal cual si no encuentra marcas: mas vale contar de mas
    que devolver vacio un libro que no venia de Gutenberg.
    """
    if not texto:
        return ""
    m = _INICIO_PG.search(texto)
    if m:
        texto = texto[m.end():]
    m = _FIN_PG.search(texto)
    if m:
        return texto[:m.start()].strip()
    m = _FIN_PG_SUAVE.search(texto)
    # Solo se acepta el corte suave si cae en el ultimo tercio: en el primero
    # seria una mencion cualquiera y nos quedariamos sin libro.
    if m and m.start() > len(texto) * 0.33:
        return texto[:m.start()].strip()
    return texto.strip()


def _palabras_reales(capitulo) -> int:
    if not _BOILERPLATE_RE.search(capitulo.texto):
        return capitulo.palabras
    return len(sin_licencia(capitulo.texto).split())


_CABECERA_CORRIDA = re.compile(
    r"(?i)^\s*(?:the\s+)?project gutenberg (?:e-?book|e?text)\b")


def _sin_cabecera_corrida(texto: str) -> str:
    """El texto sin la cabecera corrida de Gutenberg, si la trae de primera linea.

    Los epub de la generacion vieja (`pg28xxx`) repiten "The Project Gutenberg
    eBook of X, by Y." al principio de CADA archivo del libro. Como el filtro
    mira las primeras 400 palabras buscando la formula, esa linea sola bastaba
    para clasificar como licencia todo capitulo de menos de 3.000 palabras:
    *Los hermanos Karamazov* perdia 38 de sus 98 capitulos y la *Alicia*
    ilustrada 12 de 13, con la curva del "libro entero" calculada sobre lo que
    quedaba. Se quita la LINEA, no la mencion: si el capitulo repite la formula
    mas abajo -que es lo que hace la licencia de verdad- sigue cazandose.
    """
    primera, _, resto = texto.partition("\n")
    if _CABECERA_CORRIDA.match(primera.strip()) and resto.strip():
        return resto
    return texto


def _es_boilerplate(capitulo) -> bool:
    """True si el capitulo es licencia o portadilla de Gutenberg y no el libro.

    Se mira el titulo y las primeras 400 palabras: la licencia larga del final
    empieza diciendo lo que es, y la portadilla es corta entera.

    OJO CON LA CABECERA. Se mira el texto SIN la envoltura legal, y eso no es
    un refinamiento: era un fallo que tiraba libros enteros. Un .txt de
    Gutenberg sin encabezados de capitulo -poesia, ensayo, teatro, relatos, o
    simplemente otra convencion de titulos- cae al respaldo de
    `reader._leer_txt`, que devuelve UN capitulo llamado "Texto completo" con
    el archivo entero dentro. Sus primeras 400 palabras son la cabecera legal
    de Gutenberg, que repite la formula varias veces, asi que el capitulo se
    clasificaba como licencia y el libro se descartaba SIN puntuar. Medido con
    un texto de prueba de 10.434 palabras de prosa: cero capitulos
    sobrevivian. Quitando la envoltura antes de mirar, sobrevive.
    """
    if _BOILERPLATE_RE.search(capitulo.titulo or ""):
        return True
    limpio = sin_licencia(capitulo.texto)
    # Si al quitar la envoltura no queda casi nada, el capitulo ERA la
    # envoltura. Es el caso que el filtro tiene que seguir cazando.
    if len(limpio.split()) < 150:
        return True
    # La PORTADILLA. El archivo que trae la marca de licencia lleva debajo
    # portada, creditos e indice, y eso no es el libro. Antes caia de rebote,
    # porque `reader` le ponia de titulo la cabecera corrida ("The Project
    # Gutenberg eBook of...") y la primera linea de esta funcion lo cazaba por
    # el titulo; ahora el titulo es limpio y hay que decirlo aqui.
    #
    # El criterio NO es la longitud -probe con "menos de 1.200 palabras" y se
    # llevaba por delante un capitulo de verdad de mil palabras con la
    # envoltura legal pegada, que es justo el caso que el parrafo de arriba
    # explica que no hay que romper-. Es que lo que queda DESPUES de quitar la
    # licencia no sea prosa corrida: un indice de capitulos no lo es. Y
    # `continuous_prose` se aplica solo aqui, al archivo de la licencia, no a
    # los capitulos, que es lo que lo hacia inservible como filtro general.
    #
    # Medido sobre los nueve epub cacheados del catalogo: caza la portadilla de
    # *Alicia* (83 palabras), *Grimms* (248) y *Guerra y paz* (799 palabras de
    # "Contents / BOOK ONE / CHAPTER I..."), y NO caza el primer archivo de
    # *Orgullo y prejuicio*, que trae dentro los cinco primeros capitulos de la
    # novela y hasta ahora se perdia entero.
    if _INICIO_PG.search(capitulo.texto) and not scoring.continuous_prose(limpio)[0]:
        return True
    cabeza = " ".join(_sin_cabecera_corrida(limpio).split()[:400])
    if not _BOILERPLATE_RE.search(cabeza):
        return False
    # Una novela puede mencionar Gutenberg de pasada en una nota al pie. Se
    # exige que la mencion pese: o el capitulo es corto, o repite la formula.
    return capitulo.palabras < 3000 or len(_BOILERPLATE_RE.findall(cabeza)) >= 2


def _muestra(libro, tope_palabras: int = 60000) -> str:
    """Texto del libro hasta un tope, repartido por todos los capitulos.

    Se reparte en vez de coger el principio porque el principio de un libro no
    se parece al resto: prologos, dedicatorias y arranques cuidados.
    """
    cuerpo = [c for c in libro.capitulos
              if c.palabras >= 150 and not _es_boilerplate(c)]
    if not cuerpo:
        cuerpo = [c for c in libro.capitulos if c.palabras >= 150]
    if not cuerpo:
        cuerpo = list(libro.capitulos)
    if not cuerpo:
        return ""
    por_capitulo = max(300, tope_palabras // len(cuerpo))
    trozos = []
    for c in cuerpo:
        toks = sin_licencia(c.texto).split()
        trozos.append(" ".join(toks[:por_capitulo]))
    return "\n\n".join(trozos)


def caracteristicas(libro) -> Caracteristicas:
    """Mide el libro contando. No llama a nada ni puede fallar por red."""
    texto = _muestra(libro)
    # El total tambien excluye la licencia: si no, un libro de 29.000 palabras
    # anuncia 33.000 y el tiempo de lectura sale inflado por texto legal.
    palabras_total = (sum(_palabras_reales(c) for c in libro.capitulos
                          if not _es_boilerplate(c))
                      # Un archivo que es SOLO portadilla y licencia -los hay
                      # en Gutenberg- deja la suma en cero. Antes de anunciar
                      # "0 palabras" se cuenta lo que haya, ya recortado.
                      or sum(_palabras_reales(c) for c in libro.capitulos)
                      or libro.palabras)

    frases = [f for f in scoring.SENT_RE.findall(" ".join(texto.split()))
              if len(scoring.words(f)) >= 3]
    frase_media = (sum(len(scoring.words(f)) for f in frases) / len(frases)
                   if frases else 0.0)

    con_voz = sum(bool(_DIALOGO_RE.search(f)) for f in frases)
    dialogo = con_voz / len(frases) if frases else 0.0

    # El apostrofo tipografico se normaliza al recto: Gutenberg escribe
    # "don’t" con el curvo, y sin esto `_VACIAS` -que lleva el recto- no lo
    # reconocia, asi que la contraccion seguia subiendo a las distintivas por
    # mucho que se anadiera a la lista. De paso, "don’t" y "don't" dejan de
    # contar como dos palabras distintas en la riqueza lexica.
    toks = [t.lower().replace("’", "'") for t in _PALABRA_RE.findall(texto)
            if len(t) >= 3]
    muestra = toks[:20000]
    riqueza = len(set(muestra)) / len(muestra) if muestra else 0.0

    cuenta: dict[str, int] = {}
    for t in toks:
        if t not in _VACIAS:
            cuenta[t] = cuenta.get(t, 0) + 1
    # Se piden repetidas de verdad (>= 8) para no sacar un nombre que sale una
    # vez; y se ordenan por frecuencia, que en una novela saca a los personajes
    # y los lugares, que es justo lo que uno quiere ver de un vistazo.
    distintivas = [p for p, n in sorted(cuenta.items(), key=lambda kv: -kv[1])
                   if n >= 8][:12]

    return Caracteristicas(
        palabras=palabras_total, capitulos=len(libro.capitulos),
        frase_media=round(frase_media, 1), dialogo=round(dialogo, 3),
        riqueza=round(riqueza, 4), distintivas=distintivas)


# --- La sinopsis: lo unico de aqui que sale a la red -----------------------

MODELO_POR_DEFECTO = "gpt-5"
ESFUERZO = "low"
_TOPE_EXTRACTO = 900        # palabras por pasaje enviado
_PASAJES = 4


def _modelo_sinopsis():
    from pydantic import BaseModel

    class Sinopsis(BaseModel):
        de_que_trata: str
        temas: list[str]
        para_quien: str
        aviso: str

    return Sinopsis


def _pasajes(libro) -> list[str]:
    """Principio, dos puntos del medio y el final, recortados."""
    cuerpo = [c for c in libro.capitulos
              if c.palabras >= 150 and not _es_boilerplate(c)]
    cuerpo = cuerpo or [c for c in libro.capitulos if c.palabras >= 150]
    if not cuerpo:
        return []
    n = len(cuerpo)
    idx = sorted({0, n // 3, (2 * n) // 3, n - 1})[:_PASAJES]
    return [" ".join(sin_licencia(cuerpo[i].texto).split()[:_TOPE_EXTRACTO])
            for i in idx]


def sinopsis(libro, cliente, *, modelo: str = MODELO_POR_DEFECTO
             ) -> tuple[dict | None, str]:
    """De que trata el libro, en espanol. Devuelve `(datos, causa)`.

    `causa` es "" si fue bien, "sin_cliente", "sin_pasajes" o "sin_red" si no
    salio NADA a la API, y "fallo" si la peticion llego a salir y fallo.
    La diferencia no es cosmetica: quien llama cobra un uso del cupo ANTES
    de saber si se va a gastar, y devolverlo cuando la llamada si salio
    seria regalar lo que ya se pago.

    Se le dan pasajes del principio, del medio y del final, y se le prohibe
    apoyarse en lo que "sepa" del titulo: si el archivo no es el libro que dice
    su portada, la ficha tiene que describir el archivo, no la portada.
    """
    if cliente is None:
        return None, "sin_cliente"
    trozos = _pasajes(libro)
    if not trozos:
        return None, "sin_pasajes"
    Sinopsis = _modelo_sinopsis()
    instrucciones = (
        "Eres el bibliotecario de LiteraLevel, una app de lectura en ingles "
        "para hispanohablantes. Recibes pasajes de un libro (principio, medio "
        "y final) y describes el libro para alguien que esta decidiendo si "
        "leerlo.\n\n"
        "REGLAS:\n"
        "- Responde en espanol, claro y sin jerga literaria.\n"
        "- Describe SOLO lo que se ve en los pasajes. No te apoyes en lo que "
        "recuerdes del titulo o del autor: si el archivo no coincide con su "
        "portada, describe el archivo.\n"
        "- Nada de destripar el final. Puedes decir de que trata y como "
        "empieza; no como acaba.\n"
        "- Si los pasajes no dan para saberlo, dilo en vez de rellenar.\n\n"
        "Campos:\n"
        "- de_que_trata: dos o tres frases. Que pasa y a quien le pasa.\n"
        "- temas: entre dos y cinco etiquetas cortas en espanol.\n"
        "- para_quien: una frase sobre a que lector le va a gustar esto.\n"
        "- aviso: una frase si el libro tiene algo que conviene saber antes "
        "(violencia, ingles muy antiguo, dialecto cerrado, mucha digresion). "
        "Cadena vacia si no hay nada que avisar."
    )
    entrada = (f"Titulo declarado: {libro.titulo or 'desconocido'}\n"
               f"Autor declarado: {libro.autor or 'desconocido'}\n\n"
               + "\n\n---\n\n".join(f"PASAJE {i}:\n{t}"
                                    for i, t in enumerate(trozos, 1)))
    try:
        r = cliente.responses.parse(
            model=modelo, instructions=instrucciones, input=entrada,
            text_format=Sinopsis, reasoning={"effort": ESFUERZO})
        return r.output_parsed.model_dump(), ""
    except Exception as e:
        # La sinopsis es un extra. Si OpenAI falla, cambia de formato o no hay
        # red, la ficha se queda con lo medido y el lector no ve un error.
        #
        # Pero SE DICE si la peticion llego a salir. Las de conexion y plazo
        # no gastaron nada, y quien llama tiene que poder devolver el uso del
        # cupo; las demas si pueden haber costado tokens.
        nombre = type(e).__name__
        sin_red = ("Connection" in nombre or "Timeout" in nombre
                   or isinstance(e, (ConnectionError, TimeoutError, OSError)))
        return None, ("sin_red" if sin_red else "fallo")


# --- Que partes de un libro son el libro ---------------------------------
RELLENO_RE = re.compile(
    r"^\s*(also translated|a note about|about the (author|translator)|"
    r"appendix|foreword|preface|introduction|contents|index|notes?\s*$|"
    r"acknowledg|copyright|dedication|title page|borzoi|colophon|"
    r"further reading|bibliograph|glossar|"
    # La etiqueta que `reader` pone a todo lo anterior al capitulo 1 de un
    # .txt. En los de Gutenberg eso es portada, indice y pies de ilustracion:
    # en Orgullo y Prejuicio son 4.957 palabras que no son la novela y que se
    # estaban puntuando como si lo fueran. No basta con `_es_boilerplate`,
    # que las deja pasar por ser un capitulo largo con una sola mencion a
    # Gutenberg; ni sirve `continuous_prose`, que ademas tiraria capitulos
    # de verdad -probado: se lleva por delante dos de Alicia-.
    r"antes del primer cap)", re.IGNORECASE)


def capitulos_de_cuerpo(libro):
    """Los capitulos que SON el libro: ni portadilla, ni indice, ni licencia.

    Vive aqui y no en `ui.py` porque el precalculo masivo en Colab tiene que
    usar exactamente este filtro. Si alla se escribiera otro parecido, el
    catalogo entero acabaria medido sobre un conjunto de capitulos distinto
    del que mide la app, y los numeros dejarian de ser comparables sin que
    nadie se diera cuenta.

    Devuelve pares (indice_original, capitulo).
    """
    return [(i, c) for i, c in enumerate(libro.capitulos)
            if c.palabras >= 150 and not RELLENO_RE.search(c.titulo)
            and not _es_boilerplate(c)]


def dificultad_global(filas) -> float:
    """La dificultad de un libro entero, a partir de sus filas por capitulo.

    Es la media sobre TODAS las ventanas del libro, que es la definicion que
    publica el documento. Se calcula ponderando la media de cada capitulo por
    su numero de ventanas, que da exactamente lo mismo:

        sum(media_i * n_i) / sum(n_i)  ==  sum(todas las ventanas) / total

    Vive aqui, y no suelta en `ui.py`, porque antes habia dos formulas. La app
    hacia la media de las medias de capitulo y el precalculo masivo la media de
    todas las ventanas, y **no son el mismo numero**: con un capitulo de una
    ventana a 0 y otro de nueve ventanas a 2, la primera da 1,0 y la segunda
    1,8. Un mismo libro salia con dos dificultades segun se hubiera medido en
    vivo o en el catalogo. Lo encontro una auditoria externa.

    Se elige la media por ventanas porque es la que esta documentada y la que
    trata igual a todo el texto: un capitulo de tres paginas no debe pesar lo
    mismo que uno de treinta.

    Un analisis guardado en disco por una version anterior podria no traer
    `ventanas`. En ese caso esa fila cuenta como una, en vez de reventar: la
    ficha de un lector no puede caerse porque su archivo sea viejo.
    """
    n = sum(f.get("ventanas", 1) for f in filas)
    if not n:
        return 0.0
    return sum(f["dificultad"] * f.get("ventanas", 1) for f in filas) / n


def capitulos_a_tu_nivel(filas, nivel, margen, minimo_palabras=1500, tope=5):
    """Los capitulos de un libro que SI estan al alcance de este lector.

    Un libro entero puede quedar por encima de tu nivel y tener, aun asi,
    capitulos que puedes leer. La curva por capitulo ya lo sabe; esto lo dice.

    Criterio: `dificultad <= nivel + margen`, con el MISMO margen con el que la
    ficha decide que un libro "va por encima de tu nivel" (`perfil.RETO`). Si
    fueran dos numeros distintos, la misma pantalla podria decir que un
    capitulo te queda grande y a la vez recomendartelo.

    Se ordenan por CERCANIA a tu nivel, no por facilidad: el objetivo es que
    sea legible, no que sea trivial. Se descartan los capitulos cortos -uno de
    200 palabras no es una lectura que recomendar- y se corta en `tope`.

    Vive aqui y no en `ui.py` por lo mismo que `dificultad_global`: el lector y
    el buscador del catalogo tienen que usar la misma seleccion, y si hubiera
    dos acabarian recomendando capitulos distintos del mismo libro.

    Nunca revienta: una fila sin `indice` o sin `dificultad` -un analisis viejo,
    un shard antiguo- se salta, y un nivel que no es un numero da lista vacia.
    """
    try:
        nivel = float(nivel)
        margen = float(margen)
    except (TypeError, ValueError):
        return []
    buenas = []
    for f in filas or []:
        try:
            dif = float(f["dificultad"])
            int(f["indice"])
        except (KeyError, TypeError, ValueError):
            continue
        if (f.get("palabras") or 0) < minimo_palabras:
            continue
        if dif <= nivel + margen:
            buenas.append(f)
    buenas.sort(key=lambda f: (abs(float(f["dificultad"]) - nivel), int(f["indice"])))
    return buenas[:max(int(tope), 0)]


def _titulo_normalizado(t) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()[:40]


def alinear_con_catalogo(libro, filas) -> dict:
    """{capitulo del catalogo -> indice en ESTE libro}, o {} si no cuadran.

    La curva por capitulo del catalogo se midio en Colab sobre el `.txt` de cada
    libro. Si la app abre otro formato, sus capitulos pueden NO ser los mismos.
    Medido el 12 de septiembre de 2026 sobre tres libros: el EPUB de *Pride and
    Prejudice* trae 15 secciones donde el `.txt` trae 61 capitulos; el `.txt`
    de *Frankenstein* coincide en titulos con el indice desplazado uno. Saltar
    con el indice del catalogo llevaria al lector a otro capitulo.

    Asi que solo se alinea cuando TODO cuadra: el mismo numero de capitulos de
    cuerpo y el mismo titulo en cada posicion. Se empareja por POSICION entre
    los capitulos de cuerpo -que es lo que el catalogo llama `capitulo`- y se
    devuelve el indice real de este libro, no el del catalogo. Si algo no
    cuadra, diccionario vacio: mejor no sugerir que sugerir mal.
    """
    try:
        cuerpo = capitulos_de_cuerpo(libro)
        filas = sorted(filas or [], key=lambda f: int(f["capitulo"]))
    except (KeyError, TypeError, ValueError, AttributeError):
        return {}
    if not cuerpo or len(cuerpo) != len(filas):
        return {}
    mapa = {}
    for (i, c), f in zip(cuerpo, filas):
        if _titulo_normalizado(c.titulo) != _titulo_normalizado(f.get("titulo", "")):
            return {}
        mapa[int(f["capitulo"])] = i
    return mapa
