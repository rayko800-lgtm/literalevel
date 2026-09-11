# Encargo 11 — pasada estrecha de regresión, la noche antes de grabar

Escrito el **11 de septiembre de 2026**, de noche, después de cerrar los seis
serios, los cuatro menores y las tres notas de la auditoría 16.

## Por qué esta pasada existe

La auditoría 16 revisó el árbol en `b6a7c21`. **Todo lo que hice para
arreglarla es posterior y no lo ha mirado nadie**: `b6a7c21..HEAD`, que son
tres commits y 109 líneas de `app/ui.py`, justo en la pantalla de lectura, la
puerta de pago y el descargador del buscador.

Y hay una razón concreta para desconfiar de esos tres commits en particular:
**hoy, de mis propios arreglos, salieron tres problemas**. Una variable sin
definir que rompía el arranque cuando no hay perfiles configurados; un
reemplazo a ciegas de «295» por «296» que me cambió tres cifras que no eran de
pruebas; y dos diagnósticos falsos seguidos del recuadro rojo, que solo se
cayeron al volver a reproducir el fallo con el arreglo puesto.

Así que esto **no es otra auditoría del proyecto**. Es una pasada de
regresión sobre un diff pequeño, con una sola pregunta: *¿qué he roto hoy?*

## Por qué estrecha y no completa

Se graba mañana. Una auditoría completa son ~45 minutos suyos más el tiempo de
verificar, y cada hallazgo son arreglo, pruebas, despliegue y recompilar. Si
aparece algo tarde, el riesgo no es el hallazgo: es el arreglo con prisa —que
es exactamente como nació el fallo del arranque de esta tarde—.

Después de esta pasada, **el código se congela** salvo que salga un crítico.

## Lo que NO va aquí

- Auditar de nuevo las cifras, el documento o el cuadernillo. Lo hizo la 16 y
  cuadraban.
- El catálogo heredado (limitación conocida, remedición en curso).
- La corrección de pronunciación con micrófono real: no hay micrófono, y eso
  no lo desbloquea ningún auditor.

---

## El encargo, literal

> Eres un auditor externo de LiteraLevel (`C:\Users\laura\literalevel`), una
> aplicación que mide la dificultad de textos en inglés. Trabajas **a ciegas**:
> **no abras `auditoria/`** salvo para escribir tu informe al final.
>
> Esto **no es una auditoría del proyecto**: es una **pasada de regresión sobre
> un diff**. La pregunta única es *¿qué se ha roto con estos cambios?*
>
> **El diff es `git diff b6a7c21..HEAD`.** Empieza por ahí: léelo entero, que
> son ~1.250 líneas y la mitad son pruebas. Lo que de verdad importa son las
> **109 líneas de `app/ui.py`**, en cinco sitios:
>
> 1. `_abrir_del_catalogo`: ya no vacía el desplegable de capítulos mientras
>    descarga.
> 2. `_indice_de` y `_opciones_capitulos`: las opciones de capítulo se
>    construyen en un sitio y el valor se valida contra el libro.
> 3. El cableado del índice y del desplegable en `construir()`.
> 4. `_ficha_libro`: con perfil pero sin la curva medida, da un rango en vez de
>    un tiempo.
> 5. `_practicar`: se corta antes si no hay `OPENAI_API_KEY`.
>
> **Lo que quiero saber, en este orden:**
>
> **a) ¿Rompen algo que antes funcionaba?** Ejecuta los caminos que tocan, con
> la aplicación de verdad —en local con `python -X utf8 app/ui.py`, o contra
> `https://mikemaki1763-literalevel.hf.space`—: abrir un libro desde el
> buscador, abrir OTRO con uno ya abierto, moverse por capítulos con el
> desplegable y con el índice de abajo, volver atrás y adelante, subir un
> archivo desde disco, recargar la página con un libro abierto. Interesa
> cualquier estado en el que el desplegable y el índice **dejen de decir lo
> mismo**, o en el que el capítulo que se ve no sea el que marcan.
>
> **b) ¿Los arreglos hacen lo que dicen?** Rompe cada uno a propósito sobre una
> copia del árbol y comprueba que falla **la prueba que dice cubrirlo**, por
> nombre. Si alguna prueba nueva pasa igual con el arreglo deshecho, es
> decorativa y quiero saberlo. Copia el árbol a `scratchpad/f17_arbol/<id>/`
> con `app/`, los `pruebas_*.py`, `tests_smoke.py`, `main.py`,
> `validar_local.py`, `catalogo_recomendaciones.csv` y los
> `catalogo_emb_*.npy`; exporta
> `LITERALEVEL_MODELO=C:\Users\laura\literalevel\modelo_v4` y
> `LITERALEVEL_DICCIONARIO=C:\Users\laura\literalevel\kaikki_diccionario.db`;
> y **verifica que el control sin mutar pasa antes de mutar nada**.
>
> **c) ¿Hay algún camino que los arreglos no contemplen?** Piensa en los casos
> que no aparecen en el diff: un libro de un solo capítulo, uno de 366, un
> archivo subido a mano, dos pestañas abiertas del mismo navegador, la puerta
> de pago con clave y sin ella, un perfil recién creado.
>
> **Reglas.** **No modifiques el repositorio**: no arregles, no despliegues, no
> hagas commit, no toques credenciales. Todo lo que escribas en `scratchpad/`
> lleva el prefijo `f17_`. No ejecutes nada que gaste dinero: no hay
> `OPENAI_API_KEY` en local y así se queda. Si te quedas sin margen, **escribe
> el informe con lo que lleves**.
>
> **Informe en `auditoria/informe_fable_17.md`**, con: resumen de diez líneas;
> cada hallazgo con gravedad, `archivo:línea`, cita literal, qué falla, cómo se
> reproduce y cómo se arregla; la tabla de mutantes; y **lo que comprobaste y
> estaba bien**, que aquí importa tanto como lo que falla —si los cambios están
> sanos, quiero saber que lo están y por qué—.
>
> Última línea del informe, contestada con lo que hayas visto: **¿se puede
> grabar mañana con este código, sí o no?**
