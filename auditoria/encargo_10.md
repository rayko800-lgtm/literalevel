# Encargo 10 — la auditoría 16, a dos días de grabar

Escrito el **viernes 11 de septiembre de 2026**, después de cerrar la auditoría
15 entera (7 serios, 6 menores, 2 notas) y sus 22 mutantes vivos.

**Para qué es esta pasada.** El sábado 12 Miguel graba el vídeo. Todo lo que
encuentre esta auditoría tiene que ser accionable en un día, o servirle para
saber qué **no** enseñar delante de la cámara. No es una auditoría académica:
es la última mirada antes de que esto se entregue.

---

## Por qué va a ciegas

No se le dice al auditor nada de lo que se corrigió hoy. Si se lo cuentas,
tiende a confirmarlo. **Lo que vuelva a salir es lo que sigue mal de verdad, y
lo que desaparezca es la prueba de que se arregló.**

Por eso el encargo le prohíbe abrir `auditoria/` salvo para escribir su informe:
si lee el informe 15, devuelve una versión de él.

---

## Lo que se le pide, y en qué orden

El orden importa: si se queda sin margen, lo que haya hecho ya vale.

1. **El recorrido de la demo, ejecutándolo.** Es lo único que el profesor va a
   ver. Cinco pasos del guion, con la app de verdad.
2. **Las cifras publicadas contra el código que las produce**, incluidas las
   que solo existen en el PDF.
3. **Mutantes.** Es lo que más ha rendido en catorce auditorías: romper una
   línea a propósito y exigir que falle la prueba que dice cubrirla.
4. **El dinero y los datos por lector**, que es donde un fallo no se ve y
   cuesta.

## Dos reglas de higiene que se aprendieron a golpes

- **Nombres de archivo propios en el bloc de notas.** Un subagente auditor
  escribió su arnés de mutación en `scratchpad/mutar.py`, que ya existía, y se
  llevó por delante una hora de trabajo. Todo lo suyo va con prefijo `f16_`.
- **No toca el repositorio.** Audita y escribe su informe. No arregla, no
  despliega, no hace commit, no toca el token de Hugging Face.

---

## El encargo, literal

> Eres un auditor externo de LiteraLevel, un proyecto de fin de módulo de un
> máster de ciencia de datos. Trabajas a ciegas: **no abras `auditoria/`** salvo
> para escribir tu informe al final. Tu trabajo no es confirmar nada, es
> encontrar lo que está mal.
>
> **Contexto que necesitas y nada más:** la aplicación mide la dificultad de
> textos en inglés para lectores hispanohablantes con un modelo propio (v4,
> distilroberta afinado en regresión, escala pública 0–2). Está desplegada en
> `https://mikemaki1763-literalevel.hf.space` y se arranca en local con
> `python -X utf8 app/ui.py`. Los entregables están en `entrega/`. Las pruebas
> son los `.py` de la raíz que empiezan por `pruebas_` o `tests_`.
>
> **Pasada 1 — el recorrido de la demo, ejecutándolo (lo más valioso).**
> El guion del vídeo está en `entrega/guion_video.md`. Haz sus cinco pasos con
> la aplicación de verdad, en local o en el Space, y compara lo que ves con lo
> que el guion y `entrega/documento.md` §8.2 prometen: cada cifra que se dice a
> cámara, cada pantalla que se enseña. Interesa **cualquier sitio donde la
> aplicación se contradiga a sí misma o contradiga al documento**, y cualquier
> paso que delante de una cámara pueda salir mal. Di también cuánto tarda cada
> paso: un paso correcto que tarda cuarenta segundos es un problema de vídeo.
>
> **Pasada 2 — las cifras.** Coge las cifras medidas de `entrega/documento.md`,
> `entrega/estrategia.md`, `README.md`, `PENDIENTES.md` y el cuadernillo
> `entrega/notebook_proyecto.py`, y comprueba que el código o el guion que se
> cita al lado las produce. **Extrae el texto de los tres PDF de `entrega/`**
> (`documento.pdf`, `guion_video.pdf`, `presentacion.pdf`) y comprueba que dicen
> lo mismo que sus fuentes: en este proyecto se ha publicado más de una vez un
> `.md` corregido con su `.tex` sin corregir. Usa `grep` para localizar; no leas
> archivos enteros.
>
> **Pasada 3 — mutantes.** Escoge entre diez y veinte líneas que alguna prueba
> dice cubrir, rómpelas **de una en una** sobre una copia del árbol, y comprueba
> si falla la prueba que debería cazarlas. Copia el árbol entero (`app/`, los
> `pruebas_*.py`, `tests_smoke.py`, `main.py`, `validar_local.py`,
> `catalogo_recomendaciones.csv` y los `catalogo_emb_*.npy`) a
> `scratchpad/f16_arbol/<mutante>/`; **verifica que el control sin mutar pasa
> antes de mutar nada**; y atribuye el fallo **por nombre de prueba**, no por
> «la suite falla». Un mutante que sobrevive es un agujero en la red, y es el
> hallazgo que más vale de esta auditoría. Apunta a lo que **no** sería obvio:
> el dinero, los datos de cada lector, las constantes del modelo, y las
> promesas que el documento hace y nadie asevera.
>
> **Pasada 4 — dinero y datos.** Tres caminos llaman a OpenAI y cuestan dinero.
> Recorre cada uno y responde: ¿se cobra el cupo cuando no se gasta? ¿se deja de
> cobrar cuando sí se gasta? ¿puede un visitante ver o gastar lo de otro? ¿hay
> algún camino a OpenAI que no pase por la puerta de pago?
>
> **Reglas.**
> - **No modifiques el repositorio.** No arregles nada, no despliegues, no hagas
>   commit, no toques credenciales. Auditas y escribes.
> - Todo lo que escribas en `scratchpad/` lleva el prefijo `f16_`. Es un
>   directorio compartido y ya se perdió trabajo ajeno por no hacerlo.
> - Si te quedas sin margen, **escribe el informe con lo que lleves**. Un
>   informe a medias sirve; uno no escrito no vale nada.
>
> **Formato del informe**, en `auditoria/informe_fable_16.md`:
> - Resumen de diez líneas al principio.
> - Cada hallazgo con **gravedad** (crítico / serio / menor / nota),
>   **ubicación** (`archivo:línea`), **cita literal**, **qué falla y por qué**,
>   **cómo se reproduce** y **cómo se arregla**.
> - La tabla de mutantes: cuál, qué rompe, qué prueba debería cazarlo, y si
>   vivió o murió.
> - Una sección final de **lo que comprobaste y estaba bien**. Sin ella no se
>   distingue lo revisado de lo no revisado.
> - Y una última pregunta, contestada con lo que hayas visto: **si mañana esto
>   se graba tal cual, ¿qué es lo que va a salir mal?**
