# Ronda 4 · Arranque de los Spaces el día de la demo (f4)

16 sep 2026. Encargo de la Central. Solo lectura: no se reinició ningún Space ni se tocó `app/`. Las cifras salen de
la API de Hugging Face, de las filas de `DESPLIEGUE.md` y de llamadas sin credenciales al Space.

## 1. ¿Se duerme el Space de la API? Sí, a las 48 h

- **Consultado hoy a la API de Hugging Face** (`get_space_runtime`): `MikeMaki1763/literalevel` está en `RUNNING`,
  hardware `cpu-basic`, y declara **`sleep_time` / `gcTimeout` = 172.800 s, es decir 48 horas exactas** de inactividad.
  Sin almacenamiento persistente (`storage: None`).
- Coincide con lo que ya afirman los entregables (`documento.md:1473` y `notebook_proyecto.py:2488`): «se suspende tras
  48 h sin visitas y el primero en volver paga el arranque». Queda comprobado contra la API, no solo escrito.
- **Qué significa para la demo:** el Space **no se duerme por estar unas horas sin uso**. Solo se duerme si pasan dos
  días enteros sin una sola visita. Si alguien lo abre el día antes, el día de la demo está despierto.

## 2. ¿Qué tarda en volver?

Dos tiempos distintos, y conviene no mezclarlos:

| Momento | Qué es | Medido |
|---|---|---|
| **Despertar → `RUNNING`** | El contenedor arranca | **26-85 s** en los diez despliegues de `DESPLIEGUE.md`; los cuatro últimos, 46-72 s |
| **`RUNNING` → `buscador_listo`** | Catálogo, modelo del buscador y primera búsqueda | **12-14 s** desde el reinicio 30a (55 s antes de precargar el modelo) |
| **Petición normal, ya despierto** | `/api/salud` | **0,3 s** (medido hoy, dos llamadas) |

- **Cota para un arranque en frío completo: alrededor de un minuto, y hasta minuto y medio.** Sale de sumar el peor
  `RUNNING` reciente (72 s) con el peor `buscador_listo` (14 s). No se ha medido un despertar real desde la
  suspensión de 48 h, porque provocarlo exige dos días de inactividad y reiniciar el Space estaba descartado.
  **Es una cota construida con arranques por despliegue, no una medida del caso peor.** Un despertar de verdad puede
  tardar más, porque además hay que traer la imagen.
- Lo que sí quita incertidumbre: desde el **reinicio 30a** el modelo del buscador viaja dentro de la imagen y **ya no
  se descarga al arrancar** (0 descargas en el log, `buscador_listo` de 55 s a 12 s). Esa parte del arranque en frío,
  que era la más larga y dependía del Hub, ha desaparecido.

## 3. El Space del front

- `MikeMaki1763/literalevel-front` es **estático**: la API de Hugging Face no le devuelve hardware ni `sleep_time`.
  No tiene el ciclo de suspensión del otro.
- **Medido hoy: 0,64 s** para la página. No hay arranque en frío que esperar.
- El front **sí depende de la API** para todo lo que no sea pintar la página: si la API está dormida, la aplicación
  se abre pero las búsquedas y el resto esperan a que despierte.

## 4. Qué debe hacer Miguel, en minutos

1. **La víspera, o esa misma mañana: abrir la aplicación una vez.** Con eso el contador de 48 h se reinicia y el Space
   llega despierto a la demo.
2. **Diez minutos antes de empezar:** abrir <https://mikemaki1763-literalevel.hf.space/api/salud> y mirar que ponga
   `"buscador_listo":true`. Si lo pone, está listo y no hay nada más que hacer.
3. **Si no responde o tarda:** dejar esa pestaña cargando y esperar. Es el arranque; cuenta con **un minuto, hasta
   minuto y medio**. No recargar en bucle ni abrir más pestañas: no acelera nada.
4. **Si a los dos minutos sigue sin responder:** abrir <https://huggingface.co/spaces/MikeMaki1763/literalevel> para
   ver la fase del Space (Building, Running, Error). Con `Error`, avisar: es un fallo, no una siesta.
5. **Durante la demo, si algo va lento en la primera búsqueda:** es la primera petición tras el arranque. La segunda
   ya va a 0,3 s.

## 5. Pasos para pegar en el guion

- **La víspera:** abrir la aplicación una vez, para que el Space no llegue dormido (se suspende a las 48 h sin visitas).
- **10 minutos antes:** abrir `/api/salud` y comprobar `"buscador_listo":true`.
- **Si no está listo:** esperar con la pestaña abierta, de uno a minuto y medio; es el arranque en frío.
- **Si a los 2 minutos no responde:** mirar la página del Space; si dice `Error`, avisar.
- **La primera búsqueda tras el arranque va más lenta;** la siguiente, a 0,3 s.

## Comprobado y correcto

- La suspensión a las 48 h que afirman `documento.md` y el cuadernillo **coincide con lo que declara la API de Hugging
  Face hoy** (172.800 s).
- El front es estático y responde en menos de un segundo; no hay que calentarlo.
- La API despierta responde `/api/salud` en 0,3 s.

## Hueco declarado

**No se ha medido un despertar real desde la suspensión de 48 h.** Habría hecho falta dejar los dos Spaces sin visitas
dos días, o reiniciar el Space, que la Central descartó. Las cifras del apartado 2 son arranques por despliegue, que es
la mejor cota disponible; un despertar desde suspensión puede ser algo más lento.
