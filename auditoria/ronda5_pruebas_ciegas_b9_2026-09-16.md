# Ronda 5: barrido de pruebas que se creen a sí mismas (b9, 16 sep 2026)

**Informe completo: no me quedé sin cupo.** Solo lectura; no toqué `app/`,
`front/`, `tools/` ni ninguna prueba.

Base de la lectura: `git show HEAD:<ruta>` con HEAD en `f171d85`. Los cambios
sin commitear de f4 en `pruebas_extremas.py` tocan las líneas 519-540, 560,
2223 y 7369 de HEAD; ninguno de los hallazgos de abajo cae en esos tramos, así
que ninguno está ya arreglado en el árbol.

Alcance: `pruebas_api.py` (60 funciones), `pruebas_corpus.py` (41),
`pruebas_extremas.py` (~350 llamadas a `prueba`), los 30 `*.spec.ts` de
`front/src` y `tools/probar_boca_integrada.mjs`. Todo leído entero, no a
`grep`.

Lo único que ejecuté: una copia literal del lanzador de `pruebas_extremas.py`
(líneas 95-107) en mi scratchpad, sin importar `app/` ni cargar nada, con las
siete lambdas ciegas reescritas sobre dobles «mutantes». Las siete imprimen
`ok`; la salida está al final. Ninguna suite ni `ng build` en marcha.

## Lo que ya estaba en la lista de la Central

No las cuento como nuevas: la cadena fabricada de `pruebas_extremas.py:5743`,
el espacio del CSS en `plurales.spec.ts`, la lambda que devuelve una tupla en
`pruebas_extremas.py:519-521`, la prueba de encuadre 3D sobre un build viejo y
el `assert.equal(px.borde, 0)` de `tools/probar_boca_integrada.mjs`. Sobre esta
última solo añado que en HEAD el `borde` va precedido de
`assert.ok(px.colores>40 && px.fraccion>0.015)` (líneas 206 y 239), así que un
canvas vacío ya no pasa; lo que sigue sin distinguir es un modelo recortado
por el contenedor CSS y no por el búfer, que es lo que la Central describe.

## Ciegas de verdad: no pueden fallar

Las siete son del mismo archivo y las siete tienen el mismo antídoto
(un `assert` de una línea). En cada una: dónde, la cita, por qué pasa
siempre, y qué cambio del código real dejaría la prueba en verde.

### C1. `pruebas_extremas.py:1141-1145` — «los limites de la tabla son los del codigo»

```python
prueba("los limites de la tabla son los del codigo",
       lambda: [(lim, ui._cefr(lim - 0.001), ui._cefr(lim)) for lim, esperado
                in ((0.20, "A2"), (0.60, "B1"), (1.00, "B2"), (1.40, "C1"),
                    (1.80, "C2"))
                if ui._cefr(lim) != esperado] or "los cinco limites cuadran")
```

Es el patrón `malas or "todo bien"` que la docstring del propio lanzador
(líneas 60-70) da por corregido «en cada una de esas cuatro». Esta quedó
fuera: si algún límite falla, la lista de fallos es no vacía, o sea verdadera,
y el `or` la devuelve tal cual. El lanzador solo falla con excepción o con
`False`, y una lista nunca es `False`: imprime `ok [(0.2, 'A1', 'A1'), ...]`.

Mutante en verde: en `app/ui.py:2164` cambiar `+ 0.5` por `+ 0.4` (o
cualquier deslizamiento de los cortes). La propiedad SÍ la protege
`_la_tabla_que_ve_el_lector_es_la_del_codigo` (5014-5041), con `assert`; esta
prueba es un duplicado ciego que además imprime la lista de fallos en verde.

### C2. `pruebas_extremas.py:333-336` — «opciones con un libro de Gutenberg»

```python
prueba("opciones con un libro de Gutenberg",
       lambda: (ui._opciones_libros([_LibroFalso()])["choices"] or None)
       and "lista una opcion")
```

Con el desplegable vacío, `[] or None` es `None`, y `None and "..."` es
`None`. `None` no es `False`: `ok None`. Justo el caso que la prueba dice
vigilar (que se liste una opción) es el que no puede cazar.

Mutante en verde: `app/ui.py:1306-1307`, quitar `if _abrible(b.id)` por
`if False`, o devolver `gr.update(choices=[])`. La propiedad la protege
`_un_libro_de_gutenberg_se_puede_abrir_desde_la_tabla` (4185-4236), cuya
docstring dice literalmente «Las pruebas que los cubrian devolvian
`["choices"]` y no aseveraban nada»: esta es una de esas y sigue ahí.

### C3. `pruebas_extremas.py:853-858` — «repasar agrupa por lema»

```python
prueba("repasar agrupa por lema",
       lambda: (cuaderno.registrar(palabra="fetters", lema="fetter",
                                   oracion="in fetters again", zipf=2.3, ruta=_CDB)
                or len([a for a in cuaderno.para_repasar(9, _CDB)
                        if a.lema == "fetter"]) == 1)
       and "una sola entrada para fetter y fetters")
```

`cuaderno.registrar` devuelve `True` cuando guarda (`app/cuaderno.py:107`),
así que el `or` corta ahí y **la comparación `== 1` no se evalúa nunca** en el
camino normal. Solo se miraría el agrupado si el registro se rechazara, que
es cuando no tiene sentido mirarlo. La prueba devuelve la cadena y pasa.

Mutante en verde: en `app/cuaderno.py:138-144` quitar el `GROUP BY lema` de
`para_repasar`. No he encontrado otra prueba que asevere el agrupado por
lema: la propiedad queda **sin red**.

### C4. `pruebas_extremas.py:1043-1048` — «re-anotar no duplica»

```python
prueba("re-anotar no duplica",
       lambda: (biblioteca.anotar(ruta_libro="a", ..., capitulo=1, ...),
                biblioteca.anotar(ruta_libro="a", ..., capitulo=5, ...),
                [(e.ruta, e.capitulo) for e in biblioteca.listar(_BIB)])[2])
```

Devuelve la lista de (ruta, capítulo) y nadie la compara con nada. Con la
estantería duplicando, devuelve `[('a', 5), ('a', 1)]` y el lanzador imprime
`ok [('a', 5), ('a', 1)]`.

Mutante en verde: `app/biblioteca.py:80`, quitar el filtro
`if e.get("ruta") != str(ruta_libro)`. Sin red en ninguna otra suite que yo
haya visto (`pruebas_api.py` prueba la biblioteca por la API con ids
distintos, no la reanotación del mismo).

### C5. `pruebas_extremas.py:1061-1063` — «olvidar un libro»

```python
prueba("olvidar un libro",
       lambda: (biblioteca.olvidar("a", _BIB),
                [e.ruta for e in biblioteca.listar(_BIB)])[1])
```

Misma forma: devuelve la lista de rutas y no asevera que `"a"` haya
desaparecido. Con `olvidar` convertido en no-op, `ok ['a', ...]`.

Mutante en verde: `app/biblioteca.py:102`, devolver `_escribir(_leer(ruta), ruta)`
sin filtrar. En la API, `borrar_subido_libera_el_cupo` (`pruebas_api.py:808-832`)
sí asevera que el borrado saca el libro de la estantería, así que la
propiedad tiene red por el otro camino; esta prueba, no.

### C6. `pruebas_extremas.py:809-810` y `817-818` — el nombre de la carpeta del lector

```python
prueba("session_hash vacio cae en 'anonimo'",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("")).name))
prueba("session_hash raro no deja el nombre vacio",
       lambda: _con_nube(lambda: ui._dir_lector(_Peticion("///")).name))
```

Las dos devuelven `.name` y no lo comparan con nada. El título de la primera
promete `'anonimo'` y el de la segunda «no deja el nombre vacío», y ninguna
de las dos lo comprueba. Peor: si se quita el `or "anonimo"` de
`app/ui.py:378`, `BASE / "lectores" / ""` es la carpeta padre, `.name` vale
`"lectores"` (una cadena no vacía) y las dos siguen en `ok lectores`. Ese
mutante es exactamente «una carpeta para todos» que `_dos_lectores_no_se_ven_los_datos`
existe para impedir, pero aquella usa hashes normales y no llega a este borde.

La de en medio (`811-812`, «sin peticion tampoco revienta») está bien: solo
promete que no lanza. Y `813-816` («larguisimo se recorta») sí asevera.

### C7. `pruebas_extremas.py:896` — «idiomas admitidos»

```python
prueba("idiomas admitidos", lambda: ui.ConsultorLexico.consultar.__doc__ is not None)
```

Comprueba que `consultar` tiene docstring. No mira qué idiomas admite, ni que
`"klingon"` se rechace (eso lo hace la línea 894-895 por otro camino, de forma
laxa). Cualquier docstring, del contenido que sea, la deja en verde; borrar
el soporte de `en` no la toca.

Mutante en verde: en `app/lexicon.py:950-951` ignorar `idioma`. Es una prueba
de «existe» donde el título promete «vale lo que debe».

### Demostración ejecutada

Copia literal del lanzador (HEAD 95-107) con las siete formas sobre dobles
que hacen lo contrario de lo que el título promete:

```
  ok    los limites de la tabla son los del codigo     [(0.2, 'A1', 'A1'), (0.6, 'A1', 'A1'), ...
  ok    opciones con un libro de Gutenberg             None
  ok    repasar agrupa por lema                        una sola entrada para fetter y fetters
  ok    re-anotar no duplica                           [('a', 1), ('a', 5)]
  ok    olvidar un libro                               ['a', 'a']
  ok    session_hash raro no deja el nombre vacio      lectores
  ok    idiomas admitidos                              True

7 de 7 bien; FALLOS=[]
```

## Débiles pero útiles

No son ciegas: pueden fallar por excepción o miden algo, pero menos de lo
que su título sugiere. Van por orden de lo que yo arreglaría primero.

- **D1. `pruebas_extremas.py:4158-4182`, `_sorprendeme_filtra_de_verdad_por_nivel`.**
  `except Exception: return "sin catalogo en esta maquina..."`. Si `ui.catalogo()`
  lanza por lo que sea (no solo por faltar el CSV), la prueba se salta a sí
  misma e imprime `ok`. En la máquina de Miguel el catálogo está, así que hoy
  mide; pero en un runner sin él «filtra de verdad» sale en verde sin filtrar.
- **D2. Pruebas condicionadas a archivos que quizá no estén.** Imprimen `ok`
  con un texto que dice que no midieron: `pruebas_corpus.py:363-369`
  (`_libres_en_sorprendeme_del_catalogo_real`), `911-923`
  (`_busquedas_reales_en_espanol`), `456-458` (la segunda mitad de
  `_atribucion_fuera_al_medir`), `1257-1259` (la segunda mitad de
  `_pistas_de_busqueda_de_los_libres`) y `pruebas_extremas.py:5302-5318`
  (la segunda mitad de `_las_frases_no_llevan_comillas_sueltas_ni_cursiva`).
  Lo dicen en su resumen, que es honesto, pero la línea sigue empezando por
  `ok`, y quien cuente verdes no lo ve. Cuando se corran para la entrega,
  conviene mirar que esos cinco resúmenes NO empiecen por «sin».
- **D3. `pruebas_api.py:329-334`, `estado_sin_rutas`.** Solo aserciones
  negativas (`pista not in texto`). Con `/api/estado` devolviendo `{}` pasa.
  `precarga_y_peticion_comparten_el_catalogo` (1039-1040) sí asevera que
  `proceso` viene con sus dos claves, así que la ruta no está muerta; pero
  esta prueba, sola, no lo distingue.
- **D4. `pruebas_api.py:337-341`, `curva_de_libro_sin_medir`.** `"filas" in d
  and "trabajo" in d`: existencia de claves, no valores. Cubierta en parte
  por `topes_de_medir_y_de_la_curva` y `curva_de_un_solo_capitulo_sin_forma`.
- **D5. `pruebas_extremas.py:1020`, «estanteria vacia»** (`biblioteca.listar(_BIB)`
  sin comparar con `[]`) y **`826`, «base vacia»** (`(contar, ultimas)` sin
  comparar con `(0, 0, 0)` y `[]`). Nombre de estado, sin aserción del estado.
  Con la base sucia de una corrida anterior seguirían en verde.
- **D6. `pruebas_extremas.py:2003-2005`, «codigo vacio, None y espacios».**
  Devuelve `[validar(x) for x in ("", None, "   ")]` sin exigir que sean
  `None`. El título no promete el rechazo, así que no la llamo ciega; pero es
  la única que pasa por `validar` con esas tres entradas.
- **D7. `pruebas_extremas.py:590-591`, «desplegada, una carpeta por sesion».**
  Devuelve `.name` sin asertar; la de al lado (592-594) sí comprueba que dos
  sesiones no comparten. Sobra o se le pone un `==`.
- **D8. Aserciones sobre el código fuente en vez de sobre el comportamiento.**
  `pruebas_extremas.py:5403-5407` (que `_fragmento_para_leer` se llame en
  cuatro sitios), `6862-6869` (`"js=JS_AFI" in fuente` y `"audio.play()" in ui.JS_AFI`),
  `1002-1006` y `5054-5056` (`main.py`). Miden que la línea existe, no que
  haga algo; para JS dentro de Python no hay mucho más, pero conviene saber
  que una `JS_AFI` con `audio.play()` dentro de un comentario pasa.
- **D9. Front, negativas vacías.** `entrar-perfil.spec.ts:45-50`
  (`expect(document.activeElement).not.toBe(usuario)`: si `usuario` es `null`
  porque el campo no se pinta, pasa); `pronunciar.microfono.spec.ts:79`
  (`querySelector('.pagina > .aviso.error')).toBeNull()`: con la clase
  renombrada, pasa). Las dos van dentro de pruebas que además aseveran algo
  positivo, así que no están solas.
- **D10. `escuchar-y-ver.spec.ts:35-39`.** La URL de una pasada
  (`?dur=3&una=1`) la construye la propia `corte().animada` del test; lo que
  se prueba es que `EscucharYVer` llame a `animada(dur)` con el `dur` bueno y
  pida lo que devuelva. La construcción real de esa URL (la de `pronunciar.ts`)
  no está cubierta aquí. Es una decisión de unidad, no un fallo, pero que
  nadie crea que este spec protege el formato del `?dur=`.
- **D11. `tools/probar_boca_integrada.mjs:250-257`, `movimiento-reducido`.**
  `assert.equal(antes.equals(despues), true, 'reduced-motion sigue animando')`:
  una aserción de «nada cambia» pasa igual si el botón «reproducir» no hace
  nada. El propio comentario admite «se permite saltar a la pose quieta», así
  que un botón muerto y un salto correcto son indistinguibles.
- **D12. Código muerto dentro de pruebas buenas** (no cambia el veredicto,
  confunde al que lee): `pruebas_extremas.py:4266` y `4275` (`llamadas = []`
  que nadie llena y `assert not llamadas`, trivial: lo que caza el mutante es
  el `"Va de esto" in salida`), `3707` (`assert base`, sobre un dict que
  siempre es truthy) y `5836` (walrus `_indice :=` sin uso).

Las secciones 1 a 9 de `pruebas_extremas.py` (líneas 133-1134) son casi todas
humo declarado: devuelven `[:70]`, `repr(...)` o `len(...)` y solo prometen
«no revienta». Eso está bien como humo. Lo que no está bien es cuando el
título promete un resultado (C2-C7 y D5-D7): ahí el nombre engaña.

## Lo que miré y está bien

Para que nadie lo repita. «Bien» aquí significa: cada aserción puede fallar
por un cambio del código real, y el texto comparado sale del código o de un
doble, no de la prueba.

**`pruebas_api.py`, las 60 funciones.** Todas devuelven cadenas y todas
aseveran con `_ok`/`assert`. Destaco las que podrían parecer sospechosas y
no lo son: `corte_de_una_pasada_con_la_duracion_del_audio` compara la
respuesta de la API con `aa.svg_articulacion(...)` del propio módulo (el
oráculo es el mismo código), pero lo que mide es que `dur` y `una` LLEGUEN,
y lo remata con un `!=` contra otro `dur`; `plurales_de_los_minutos` y
`topes_de_medir_y_de_la_curva` comparan mensajes literales escritos en la
prueba, que es lo correcto (la cadena nace en `ui.py`, no en el test);
`lo_de_pago_sin_clave_no_cobra_ni_gasta_ficha` mira el cubo antes y después
por claves reales; `voz_subida_y_palabra_no_bloquean_a_los_demas` mide tiempo
relativo con la lenta viva; `validacion_sin_eco_de_la_entrada` comprueba el
manejador por identidad.

**`pruebas_corpus.py`, las 41.** Todas aseveran con listas de ids esperadas
o cifras. El lanzador de este archivo NO trata `False` como fallo (solo la
excepción, líneas 44-53), pero no hay ninguna prueba que devuelva un booleano
sin asertar: lo comprobé a `grep` y a mano. Las cinco condicionadas a archivos
están en D2. `_medicion_reanudable_y_mismo_reparto:1107` acepta dos
resultados (`""` o `"bloque"`) para SWV2; es laxo a propósito y está
documentado en el comentario de encima.

**`pruebas_extremas.py`, las funciones con nombre (no las lambdas de humo).**
Todas las que revisé aseveran contra el código real, y muchas llevan además
un «guardia del caso» que comprueba que el fixture discrimina (3020-3021,
3418, 4143-4144, 4432-4433, 4919, 5240, 5391). En particular están bien y no
hay que volver a mirarlas: `_por_encima_del_tope_no_llega_al_consultor` (522;
el `try/except AssertionError` del primer uso no tapa nada porque `_consultar`
convierte la excepción en texto y la segunda consulta tendría que traer el
aviso), `_el_session_hash_no_escapa` (595), `_contraste_suficiente` (1220),
`_el_css_no_clava_los_colores_que_ya_fallaron` (1543),
`_ningun_color_literal_en_el_css` (1606), `_el_modelo_vale_como_repositorio`
(1824, con el centinela que llega a `from_pretrained`),
`_el_cupo_cuadra_con_las_llamadas_de_pago` (2406), `_sin_clave_no_se_culpa_al_cupo`
(3192), `_el_marcapaginas_y_el_cuaderno_son_de_cada_lector` (4044),
`_cada_respuesta_del_cuestionario_va_a_su_pregunta` (4117),
`_un_libro_de_gutenberg_se_puede_abrir_desde_la_tabla` (4185),
`_la_sinopsis_guardada_no_se_vuelve_a_pagar` (4239, cuyo mutante lo caza el
`"Va de esto" in salida`), `_la_puerta_de_entrada_tiene_freno` (5064),
`_recargar_no_borra_el_has_entrado_como` (5415, con el cableado por
`demo.fns`), `_abrir_un_libro_no_pinta_un_error_rojo` (5807),
`_la_practica_de_voz_no_cobra_sin_clave` (5981),
`_las_sugerencias_de_capitulos_salen_cuando_tocan` (6096),
`_el_catalogo_medido_recomienda_capitulos_sin_saltar_mal` (6193),
`_el_buscador_encuentra_un_nombre_mal_escrito` (6352),
`_practica_sin_voz_devuelve_el_uso` (6725), `_dos_lectores_a_la_vez_pagan_una_y_se_marca_ia`
(7232), `_la_ipa_y_el_audio_son_de_la_forma_escrita` (7479) y
`_las_animaciones_de_la_boca_se_sirven_como_archivo` (7608). Las lambdas con
`and "texto"` (363, 392, 402, 427, 434, 496-518, 836-841, 1028-1035,
1054-1056, 1114-1121, 1135-1137, 1204-1207, 2586-2597) están bien: el
booleano va delante del `and`, y si es `False` el `and` devuelve `False`.

**Front, los 30 spec.** Todos comparan contra el DOM o contra el valor
devuelto, con `toEqual`/`toBe` exactos; los `not.toContain` van siempre
detrás de un `toContain` positivo del mismo nodo, y `expect(undefined).not.toContain`
en vitest lanza en vez de pasar. Bien y sin nada que añadir:
`bloques-busqueda` (bordes en milésimas por los dos lados), `boca3d`
(relaciones numéricas entre poses, no valores absolutos), `carga`, `destruir`
y `sonador` (espías con `toHaveBeenCalledOnce`), `bienvenida` (foco y
`localStorage` leídos, no fabricados), `plurales` (cifra y sustantivo
emparejados por el DOM: es el arreglo del caso 2 y está bien hecho),
`pronunciar.frase` (el `scrollIntoView` se comprueba sobre el elemento que lo
recibió y el comentario de 44-47 explica por qué NO asevera el recorte en
jsdom), `pronunciar.sin-perfil` (`expectNone` de POST por método y ruta),
`pronunciar.barra`, `pronunciar.microfono`, `pronunciar.propuesta-a`,
`pronunciar.ritmo`, `pronunciar.silencio`, `pronunciar.ayuda`,
`pronunciar.boca3d`, `nivel`, `lector.ayuda`, `libro.curva`, `entrar-perfil`
(salvo D9), `portada`, `portada.ia`, `tarjeta-libro`, `tinte`, `ritmo`,
`formato`, `version`, `escuchar-y-ver` (salvo D10) y `app`.

**`tools/probar_boca_integrada.mjs`, aparte de `borde`.** Las capturas
antes/después (204, 247, 269) se comparan por bytes y pueden fallar; el
`pixeles()` inyecta `preserveDrawingBuffer:true` (132-143) y exige color y
fracción antes del borde; el gesto táctil va por CDP y no por un evento
sintético; `comprobarLayout` mide rectángulos reales; `inesperadas` y
`errores` se aseveran vacíos al final de cada caso. Solo D11.

## Dos observaciones sobre los lanzadores

1. `pruebas_extremas.py` y `pruebas_api.py` fallan con excepción o con
   `False` exacto. `None`, una tupla, una lista o `0` pasan. C1-C7 existen
   porque ese hueco sigue abierto. Endurecer el lanzador («solo pasa una
   cadena no vacía o `True`») rompería el humo de las secciones 1-9, que
   devuelve de todo; no lo propongo para antes del 20.
2. `pruebas_corpus.py` no trata ni `False` como fallo (líneas 44-53). Hoy no
   importa porque nadie devuelve booleanos ahí, pero la próxima lambda que lo
   haga será ciega desde el primer día.

## Qué haría yo antes del 20 (no he arreglado nada)

Las siete ciegas se cierran con un `assert` de una línea cada una, o
borrando la prueba cuando otra ya protege la propiedad (C1 y C2). Las que
dejan una propiedad **sin red** en ninguna otra suite son **C3** (agrupado
por lema en el repaso) y **C4** (reanotar no duplica en la estantería):
esas dos las arreglaría antes de la entrega. C6 protege un borde de «una
carpeta para todos», que es serio, pero el mutante concreto (`or "anonimo"`)
es de una línea que nadie va a tocar en tres días. El resto puede ir a
`auditoria/cola_tras_la_entrega_2026-09-16.md`.

De las débiles, la única que cambiaría antes del 20 es D2: al correr las
suites para la entrega, mirar que los cinco resúmenes condicionados no
empiecen por «sin», o esas cinco valen cero.
