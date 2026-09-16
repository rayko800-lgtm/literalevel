# Cola de después de la entrega

Escrito por la Central el 16 de septiembre de 2026. **Esta es la copia que vale**:
antes vivía en el scratchpad de `entrega-f4`, que desaparece con la sesión.

Nada de esta lista se toca antes del 21 de septiembre. **Buscador
(`app/catalogo.py`) y cobro (`app/cuentas.py`) están congelados** hasta después
de la grabación y la demo del 19-20; solo los levanta un SERIO que afecte a la
demo o a los usuarios. Ver la memoria `congelacion-hasta-la-entrega`.

---

## 1. Buscador y cobro (congelados)

| Qué | Dónde | Nota |
|---|---|---|
| Los tres menores de 4e, en `parche_menores_28.py`: registro de devoluciones con disco roto, índice apellido→filas, obras contadas sin fechas | `app/cuentas.py`, `app/catalogo.py`, `pruebas_api.py`, `pruebas_corpus.py`, `tools/banco_mutantes.py` | El de las obras **mueve la exención de 5 obras**, así que toca el buscador: exige medida completa (100 palabras, 27 chips, 20 de control, sin perfil / A2 / B1 / 1,20) contra un **volcado del propio Space**, no contra lo local |
| El comentario del reinicio 30b en `catalogo.py` | `app/catalogo.py`, del commit 1643c4b | Dice que el ruido entre máquinas «no reordena empates», y el límite declarado dice lo contrario. Cambiarlo obliga a subir otra vez o a dejar el Space distinto de HEAD |
| Adelantar el 403 de `/api/voz` antes de leer el formulario | `app/api.py:1881-1935` | Hoy solo se pierde la subida del audio, **no cuota**: `consumir` rechaza sin sumar y el temporal se borra en el `finally`. No adelantar por delante el 503 de la clave de OpenAI |

## 2. Concordancias de singular y plural

La primera tanda fue 0e270f9 y cb799bc (14 y 15 sep). Esto es lo que se le
escapó. **El modelo a seguir ya está en el código**: `app/ui.py:2573`, con
`{'capítulo' if c.capitulos == 1 else 'capítulos'}`.

| Qué sale con n = 1 | Dónde | Alcance |
|---|---|---|
| «Se descartaron 1 resultados por parecido bajo.» | `app/catalogo.py:962`, servido en el campo «aviso» por `app/api.py:998` | **Se ve en el paso 3 de la demo.** Pendiente de la medida de f4: si aparece con 1 en alguna consulta del guion, entra antes de la entrega; si no, aquí se queda. Quedaría «Se descartó un resultado por parecido bajo.» |
| «Este libro tiene 1 capítulos; el 2 no existe.» | `app/api.py:563` | Es de la **misma familia** que el fallo de la ficha de un solo capítulo que vio Miguel en su teléfono. Se miran juntos |
| «cupo de 1 usos» | `app/cuentas.py:403` y `:423` | **Condicionado** a que exista alguna cuenta con tope 1. No se comprueba abriendo `literalevel_codigos.txt` |
| «Te quedan 1 usos», «1 de 20 se abren aquí mismo», «1 bloques», «Medidos 1 capitulos» (y le falta la tilde), «de 1 capítulos» | `app/ui.py` 693, 1233, 2140, 2432 y 2883 | Solo Gradio, que es motor y respaldo, no la pantalla de la entrega |

**Mirados y descartados, para que nadie los revise otra vez:** `app/api.py` 366,
1095 y 1525 y `app/scoring.py:392` (la cifra es una constante mayor que uno);
`app/api.py:1311` (no alcanzable con la configuración que se entrega);
`app/ui.py:3304` (ya guardado con `> 1`); `app/ficha.py:114` (contenido por
`ui._reloj_llano`, y el front va por `app/api.py:731`); `app/voz.py`, nada.

## 3. Mensajes que una persona no entendería

| Texto de hoy | Dónde | Propuesta |
|---|---|---|
| «Falta la cabecera X-Lector con el identificador de este navegador (al menos 16 caracteres).» | `app/api.py:187` | «No he podido identificar este navegador. Recarga la página y vuelve a intentarlo; si sigue igual, abre la aplicación en una pestaña normal, sin modo incógnito ni bloqueadores.» Hoy no lo ve nadie: el front siempre manda la cabecera |
| «Para guardar el nivel hace falta la cabecera X-Lector.» | `app/api.py:891` | «No he podido guardar tu nivel porque no reconozco este navegador. Recarga la página y responde otra vez el cuestionario.» |
| «Ahora mismo se están midiendo 4 libros. Vuelve a pedir la curva en unos minutos.» | `app/api.py:1311` | No dice de quién son esos libros, y quien lo lee entiende que son suyos. «El servidor está midiendo otros libros ahora mismo» |
| «· 3 bloques · confianza 0.8» | `app/ui.py:2140` | Jerga: ni «bloques» ni esa confianza significan nada para un lector. Solo Gradio |

## 4. Limpieza del Space del front

Dejar en `MikeMaki1763/literalevel-front` solo lo alcanzable desde `index.html`,
con la lista de los 14 archivos de e6 como referencia, y **comprobar la
aplicación después de borrar**.

- **Por qué no se hizo antes:** de los 402 `.js` del Space solo 14 se sirven;
  nadie carga el resto. Borrar archivos de un Space publicado tres días antes de
  grabar no compensa, y equivocarse sobre lo alcanzable rompe la entrega.
- **Riesgo declarado, de auditoría y no de usuarios:** quedan 76 chunks huérfanos
  que todavía dicen «seis preguntas». Quien haga `grep` sobre el Space los
  encontrará. La respuesta es que los 14 alcanzables están limpios y el resto es
  basura de despliegues anteriores.

## 5. Casa por dentro

- **Mover la caché local de Hugging Face (3,7 GB) a D:** y reiniciar las sesiones
  para que `TEMP` caiga en D:. Necesita que no haya sesiones trabajando y que
  Miguel las reinicie.
- **Dos carpetas temporales vacías del 7 de septiembre** que dan «Acceso
  denegado» al borrarlas. Ocupan 0 bytes; se dejaron estar.

## 6. Preguntas abiertas de producto, para después

- **Decidir «autor» por la consulta.** Con perfil, un autor buscado con una sola
  palabra («dostoyevski», «tolstoy», «cervantes») trae cuentos sin relación;
  ninguna de las cuatro variantes medidas lo arregla sin quitar cuentos del nivel
  del lector. Límite declarado en el documento (limitación 15).
- **Ideas que quedaron apuntadas:** preferir historias que no sean para «peques»
  cuando el lector tiene nivel alto.
