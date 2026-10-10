# Medir el catálogo en Colab — guion para Miguel

Reescrito el **sábado 12 de septiembre de 2026**. Sustituye al del 10 de
septiembre, que dependía de Google Drive.

## Lo que cambió, en una frase

**Drive ya no está en el circuito.** Pedía un permiso en cada sesión nueva, y
Colab gratuito corta la sesión cada pocas horas: cada corte dejaba la tanda
parada hasta que alguien diera un clic. Ahora los resultados van a un
repositorio privado de Hugging Face (`MikeMaki1763/literalevel-catalogo`) con un
token guardado en los Secretos de Colab, y la tanda se reanuda sin pedir nada.

## Lo que ya está hecho y no hay que repetir

- **El token `HF_TOKEN` está en los Secretos de Colab** de `xxxxxx@xxxxxx.com`.
  Los Secretos van por cuenta: vale para cualquier cuaderno de esa cuenta.
- **El rescate de Drive**: la celda 2c subió a Hugging Face los libros que ya
  estaban medidos. Se decide sola: si el repositorio ya tiene shards, no toca
  Drive. Ese fue el último permiso de Drive del proyecto.

## Dónde mirar cómo va, sin abrir Colab

```
python -X utf8 tools/ver_progreso.py
```

Dice cuántos libros van medidos, a qué velocidad, cuánto falta y hace cuánto
se guardó el último shard. **Si dice que lleva más de 30 minutos sin shard
nuevo, Colab cortó la sesión**: sigue abajo.

## Si Colab corta la sesión (va a pasar, y no se pierde nada)

1. Abre el cuaderno `colab_precalculo.ipynb` en Colab **con la cuenta
   xxxxxx@xxxxxx.com** (arriba a la derecha tiene que salir esa cuenta).
2. Pulsa **Conectar** (arriba a la derecha). Sale una T4, que es gratis.
3. Panel izquierdo → icono de la llave (**Secretos**) → comprueba que el
   interruptor de **HF_TOKEN** está **encendido** para este cuaderno. El
   secreto es de la cuenta, pero el permiso de usarlo es de cada cuaderno.
4. Ejecuta las celdas **una a una y en este orden**, esperando a que acabe cada
   una (el título de cada celda empieza por su número):

   **1 → 3 → 2 → 2b → 2c → 4 → 5 → 6c → 7 → 10 → 10b**

   Sí, la 3 antes que la 2: en la copia de Colab las dependencias están en la 3,
   y la 2b importa una librería que la 3 actualiza. En la versión nueva del
   repositorio ya están en la 1, y este orden funciona igual en las dos.

5. **No ejecutes nunca la 6, la 6b, la 8 ni la 9.** Son registros de lo que se
   probó y no sirvió. La 6 descarga libro a libro de un espejo de Gutenberg, que
   es lento y va contra su política.
6. La **10b** es la que tarda horas. Guarda cada 500 libros y sube el shard, así
   que puedes cerrar el navegador.

Lo ya medido no se repite: la celda 2b se baja los shards del repositorio y la
10 se salta esos libros.

## Cuando termine todo

Celdas **11** (construye el catálogo final y lo sube) y **11b** (comprueba que
no hay libros repetidos ni shards perdidos). Luego me avisas y meto el catálogo
en la aplicación.

## Si algo se pone feo

- **«Falta el token»** en la celda 2 → el interruptor de HF_TOKEN está apagado
  para este cuaderno (paso 3).
- **«No hay GPU disponible»** → la T4 gratis se reparte. Espera un rato y
  reintenta.
- **Cualquier traza roja** → pégamela tal cual, sin interpretarla. **Nunca pegues
  el token** en el chat: si una salida lo mostrara, tápalo antes.

## Al final del proyecto

El token de Hugging Face hay que **revocarlo** en huggingface.co → Settings →
Access Tokens, y borrar el secreto de Colab. Hasta entonces, no se comparte.
