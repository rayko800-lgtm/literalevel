# Encargo 7 — undécima auditoría, a ciegas

Escrito el 9 de septiembre de 2026 por la noche, sobre el árbol `b32b520`.

Dos auditores en paralelo y con alcances distintos a propósito, porque tienen
puntos ciegos distintos y coincidir vale más que dos avisos sueltos:

- **Fable**, alcance amplio y al máximo de profundidad: la aplicación y el
  código.
- **Astra / Codex**, alcance estrecho y mecánico: coherencia de cifras entre
  archivos. Estrecho porque el cupo es limitado y porque un encargo de «audítalo
  todo a fondo» con Astra ya murió una vez sin emitir un solo hallazgo.

**Los dos van a ciegas.** Ninguno debe abrir `auditoria/` salvo para escribir su
propio informe. No se les dice qué se acaba de corregir: lo que vuelva a salir
es lo que sigue mal de verdad, y lo que no salga es la prueba de que se arregló.

---

## Fable — la aplicación y el código

Informe a `auditoria/informe_fable_11.md`.

Alcance: `app/*.py`, `pruebas_*.py`, `tests_smoke.py`, `main.py`,
`validar_local.py`, y la aplicación en marcha. Formato exigido: gravedad,
`archivo:línea`, cita literal, por qué falla, cómo se arregla. Y una lista de lo
comprobado que estaba bien, porque sin eso no se distingue lo revisado de lo no
revisado.

Preguntas que se le piden expresamente:

1. **¿Hay alguna prueba que pase también con el código roto?** Es el hallazgo
   más grave de la ronda anterior y se pide buscarlo por el mismo método:
   mutar la línea que la prueba dice cubrir y comprobar que la prueba falla.
2. **¿Queda algún color clavado en el CSS** que gane a la variable de la paleta
   por ir después, o alguna variable declarada que no pinte nada?
3. **¿Rompió algo la corrección?** Firmas cambiadas, funciones nuevas que nadie
   llama, mensajes al usuario sin sujeto, dos archivos que ya no dicen lo mismo.
4. **¿Algún manejador puede levantar una excepción hacia Gradio?** El módulo
   declara que ninguno lo hace.
5. **¿Qué avergonzaría al autor** si un profesor universitario abriera la
   aplicación delante de él?

## Astra / Codex — coherencia de cifras

> **NO SE HIZO.** Lanzada el 9 de septiembre a las 21:5x con `gpt-6-astra`,
> esfuerzo intermedio y este mismo alcance. Murió tras **9.981 tokens**, sin
> emitir un solo hallazgo y sin escribir informe: *«You've hit your usage limit
> … try again at Sep 15th, 2026 8:46 AM»*. El cupo ya estaba agotado antes de
> empezar y no vuelve hasta el **15 de septiembre a las 8:46**. Lo único que
> alcanzó a decir fue su plan de trabajo.
>
> El alcance de abajo queda escrito y listo para relanzarlo ese día. Mientras
> tanto, lo mecánico —que una cifra coincida consigo misma en todos los
> archivos— se barre con un `grep` desde aquí, que es lo que se hizo con el
> «205 pruebas» que estaba publicado en ocho sitios.

Informe a `auditoria/informe_codex_7.md`.

Una sola tarea: **que cada cifra publicada coincida con lo que devuelve el
guion que la mide, y que coincida consigo misma en todos los archivos donde
vive.** Con `grep` para ir al grano, sin leer archivos enteros. Si se queda sin
margen, que escriba el informe con lo que lleve.

Los sitios donde una cifra vive en este proyecto: `entrega/documento.tex` (el
entregable), `entrega/documento.md`, `entrega/estrategia.md`,
`entrega/presentacion.tex`, `entrega/guion_video.{md,tex}`,
`entrega/notebook_proyecto.py` **y el `.ipynb` regenerado**,
`entrega/datos_figuras/*.dat` —que es lo que dibuja las figuras y el que
siempre se olvida—, `README.md`, `PENDIENTES.md`, `DESPLIEGUE.md`,
`modelo_v4/README.md`, y los comentarios del código.

Se le pide mirar cada cifra en **todas sus formas**: el valor exacto, sus
redondeos plausibles, el número suelto con contexto flojo, y las dos formas del
separador decimal —los `.dat` y el código usan punto, la prosa usa coma—.

Y los números escritos a mano dentro de `tikzpicture`: coordenadas, rótulos de
bandas, etiquetas `n = …` puestas junto a las barras y los pies de figura que
afirman lo que la figura enseña. Un `grep` no los encuentra, porque ahí un
umbral va como `0.8` sin coma y sin contexto.
