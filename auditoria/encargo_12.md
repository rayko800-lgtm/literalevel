# Encargo 12 — Codex, las cifras contra el código, el día de grabar

Escrito el **12 de septiembre de 2026** por la mañana. El cupo de Codex volvió
antes de lo que decía su propio aviso —el error del 11 anunciaba el martes 15 a
las 8:46 y hoy responde—, comprobado con una llamada de una palabra que costó
9.186 tokens.

## Por qué esta pasada y no otra

Hoy se graba. **El código está congelado** tras diecisiete auditorías, y lo que
no quiero es un hallazgo de código a las nueve de la mañana que me tiente a
tocar una aplicación desplegada y probada. Así que el alcance se elige por una
propiedad: **todo lo que encuentre se arregla editando texto**, no la app.

Eso deja una cosa, y es justo la que Codex tenía asignada desde el
[`encargo_9.md`](encargo_9.md) y nunca pudo hacer por falta de cupo: **las
cifras publicadas contra el código o el guion que las produce**.

Y hay un motivo extra para hacerla ahora: **es otra familia de modelos**. Fable
verificó estas cifras en las auditorías 15, 16 y 17. Que un modelo con otros
puntos ciegos confirme lo mismo vale más que un tercer aviso de Fable; y si
encuentra algo que Fable no vio, vale todavía más.

## Lo que NO va aquí

- Auditar el código, la interfaz o las pruebas. Congelado.
- Metodología del modelo. Ya lo hicieron las auditorías 11 a 14.
- Cualquier cosa que se arregle tocando `app/`.

## Dos avisos de dimensionado

El histórico de este proyecto con Codex es duro: un encargo de «verifica
ejecutando» murió a los 151.193 tokens **sin emitir un solo hallazgo**, y uno
estrecho murió a los 9.981 porque el cupo ya estaba agotado. Así que el encargo
lleva escritas las dos salvaguardas: **usa `grep` para ir al grano en vez de
leer archivos enteros**, y **si te quedas sin margen, escribe lo que lleves**.

Va en `--sandbox read-only`: no puede tocar el repositorio ni por accidente. Su
informe sale por la salida estándar y lo guardo yo.

---

## El encargo, literal

> Eres un auditor externo de LiteraLevel, un proyecto de fin de módulo de un
> máster de ciencia de datos. **No abras el directorio `auditoria/`.** Trabajas
> a ciegas y tu trabajo no es confirmar nada.
>
> **Alcance único: las cifras medidas de los entregables contra el código o el
> guion que las produce.** Nada de código, interfaz ni pruebas: está congelado.
>
> Los entregables son `entrega/documento.md`, `entrega/estrategia.md`,
> `entrega/notebook_proyecto.py`, `README.md` y `PENDIENTES.md`. El código vive
> en `app/` y los guiones de medición en la raíz y en `tools/`.
>
> Para **cada** cifra medida que encuentres —métricas del modelo, tamaños de
> corpus, tiempos, recuentos, porcentajes, costes— comprueba una de estas dos
> cosas, la que se pueda:
>
> 1. Que el código citado al lado la produce de verdad. Léelo; no hace falta
>    ejecutarlo salvo que sea barato y decisivo.
> 2. Que la misma cifra dice lo mismo **en todos los archivos donde aparece**.
>    Este proyecto ya ha publicado un `.md` corregido con su `.tex` sin
>    corregir más de una vez.
>
> Interesa **lo que no cuadra**, y da igual si el que está mal es el documento
> o el código. Si una cifra no se puede verificar desde el repositorio —porque
> el corpus no se distribuye, por ejemplo—, dilo: «no verificable desde aquí»
> es un resultado, y saber cuáles son esas es útil.
>
> **Mira con especial atención lo escrito en las últimas horas**, que es lo
> menos revisado: el apartado 8.2 del documento (el recorrido con *Crime and
> Punishment*), el párrafo de salidas estructuradas, el punto de *function
> calling* en Trabajo futuro, y el apartado 6.4 (cobertura de IPA y audio del
> diccionario).
>
> **Reglas.** Usa `grep` para localizar; no leas archivos enteros. No modifiques
> nada. Si te quedas sin margen, escribe el informe con lo que lleves: un
> informe a medias sirve, uno no escrito no vale nada.
>
> **Formato.** Para cada hallazgo: gravedad, `archivo:línea`, la cifra publicada,
> lo que dice el código, y cuál de los dos hay que cambiar. Al final, una lista
> de **lo que comprobaste y cuadraba**, y otra de **lo que no es verificable
> desde el repositorio**.
