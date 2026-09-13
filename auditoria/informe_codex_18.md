La revisión de `2932e50` y `8e8f0b6` deja **cuatro hallazgos: dos serios y dos menores**. No he modificado archivos ni abierto `auditoria/` o informes anteriores.

Las líneas corresponden a **`8e8f0b6`**. El repositorio recibió cambios durante la revisión; esos cambios posteriores quedan fuera del informe.

**1. Serio — El desplazamiento puede repetirse seis segundos después, interrumpiendo la lectura**

**Ubicación:** [app/ui.py:1387](C:/Users/laura/literalevel/app/ui.py:1387), líneas 1387–1396; cableado en 3758–3765.

**Cita literal:**

```javascript
const antes = inicio();
ir();
let vueltas = 0;
const reloj = setInterval(() => {
  if (inicio() !== antes || ++vueltas > 40) {
    clearInterval(reloj);
    ir();
    setTimeout(ir, 250);
  }
}, 150);
```

**Por qué falla:** el vencimiento del temporizador también ejecuta el desplazamiento, aunque no haya cambiado el texto. Ocurre al pulsar «Siguiente» en el último capítulo, «Anterior» en el primero, o cuando el capítulo nuevo ya se ha renderizado antes de tomar `antes`.

La simulación del JavaScript original produjo desplazamientos en **0, 6.150 y 6.400 ms**. Si el lector empieza a bajar después del primero, los posteriores le devuelven al principio. Dos pulsaciones crean temporizadores independientes y más saltos.

Además, el `.then()` depende del botón que actualiza `cap`, no de la finalización de `_capitulo`. Gradio encadena el evento inmediatamente precedente; no espera automáticamente otros eventos disparados por sus salidas. [Código oficial de Gradio 6.26](https://raw.githubusercontent.com/gradio-app/gradio/gradio@6.26.0/gradio/events.py).

**Cómo se arregla:** asociar el desplazamiento a la actualización efectiva del capítulo y su renderizado, identificando la navegación vigente. Cancelar temporizadores anteriores; al vencer el plazo, terminar sin desplazar. No iniciar una navegación cuando el índice no cambia.

**2. Serio — «Otra frase» permite que una corrección pendiente reponga el resultado anterior**

**Ubicación:** [app/ui.py:3877](C:/Users/laura/literalevel/app/ui.py:3877), líneas 3877–3883.

**Cita literal:**

```python
b_practicar.click(_practicar, [mi_audio, frase],
                  [palabras_html, veredicto, audio_ref])
```

```python
b_otra.click(lambda: ("", None, "", "",
                      gr.update(value=None, visible=False)),
             None, [frase, mi_audio, palabras_html, veredicto, audio_ref]
             ).then(None, None, None, js=JS_A_LA_FRASE)
```

**Por qué falla:** el nuevo botón limpia las salidas, pero no invalida la corrección que está ejecutándose.

Escenario: enviar la frase A, pulsar «Otra frase» mientras llega la respuesta y escribir B. Cuando termina A, `_practicar` vuelve a llenar el veredicto y muestra su audio junto a B.

Lo reproduje con las funciones originales aisladas y el servicio de voz simulado: después de limpiar y establecer B, la respuesta pendiente repuso **«100 / 100»**, el resultado de A y su reproductor visible. Esta prueba no realizó llamadas de pago.

**Cómo se arregla:** desactivar «Otra frase» mientras se procesa la corrección, o asignar una generación por intento y descartar respuestas de generaciones anteriores. La limpieza debe invalidar también los resultados pendientes.

**3. Menor — El relleno destinado a Markdown también estrecha el lector HTML**

**Ubicación:** [app/ui.py:551](C:/Users/laura/literalevel/app/ui.py:551).

**Cita literal:**

```css
.block.hide-container:has(.prose *){{padding:.6rem .95rem !important}}
```

**Por qué falla:** `.prose` no identifica exclusivamente Markdown. El componente `gr.HTML` de Gradio 6.26 utiliza esa clase por defecto y se construye sin contenedor. Por ello, la regla también alcanza al HTML del lector y de pronunciación, cuyos elementos interiores ya tienen relleno propio. [Constructor de HTML](https://raw.githubusercontent.com/gradio-app/gradio/gradio@6.26.0/gradio/components/html.py), [renderizador HTML](https://raw.githubusercontent.com/gradio-app/gradio/gradio@6.26.0/js/html/shared/HTML.svelte).

Al abrir un capítulo, se añade una capa exterior de **1,9 rem horizontales** —30,4 px si la raíz mide 16 px—, reduciendo nuevamente el ancho de lectura móvil. Es una conclusión del código y la estructura del componente; no una medición visual en el navegador.

**Cómo se arregla:** asignar una clase explícita a los Markdown que necesitan ese relleno y limitar la regla a esa clase.

**4. Menor — `_autor_corto` elimina partes significativas del nombre**

**Ubicación:** [app/ui.py:944](C:/Users/laura/literalevel/app/ui.py:944). Introducido en `2932e50`.

**Cita literal:**

```python
p = ",".join(p.split(",")[:2])
```

**Por qué falla:** interpreta cualquier segunda coma como el comienzo de un título nobiliario. Comprobé estos casos reales en el catálogo y comparé la función anterior y posterior al commit:

| Entrada | Resultado incorrecto |
|---|---|
| `Alger, Horatio, Jr., 1832-1899` — PG18581 | `Alger, Horatio` |
| `Appleton, Victor, II` — PG17985 | `Appleton, Victor` |
| `Allen, George (Vicar of St. Thomas's, Islington), 1827-1878` — PG64876 | `Allen, George (Vicar of St. Thomas's` |

Desaparecen sufijos identificativos y, en el último caso, queda un paréntesis abierto. Los tres se conservaban antes del cambio.

**Cómo se arregla:** retirar únicamente tratamientos reconocidos, como `graf` o `Sir`; conservar `Jr.`, numerales y comas dentro de paréntesis.

**Comprobaciones satisfactorias**

- Las cinco variantes de apóstrofo añadidas producen **100/100 y ninguna palabra fallada** al comparar con la contracción ASCII. También se conservan `well-known`, `rock'n'roll` y la eliminación de comillas exteriores.
- La prueba de contraste del commit pasa: **cinco paletas × 17 parejas = 85 comprobaciones**, incluidas las parejas afectadas por paneles y bordes.
- Los intervalos tienen limpieza y un límite de iteraciones; no encontré un intervalo infinito. El problema son los desplazamientos tardíos.
- «Otra frase» devuelve cinco valores para cinco salidas y limpia explícitamente el valor y la visibilidad del audio.
- Por inspección estática, se conservan los tres enlaces de la paleta —CSS, estado y gráfica— y las referencias necesarias están declaradas antes del cableado.
- Las menciones restantes a «Buscar lectura» y a la antigua pestaña «Colores» son comentarios, sin referencias funcionales rotas encontradas.

**Límites de verificación:** no pude comprobar visualmente el recorte de desplegables, el comportamiento de `sticky`, el posible solapamiento de «Ajustes» o la distribución a distintos anchos. Tampoco ejecuté la aplicación completa: los dos intérpretes Python localizados no tenían Gradio instalado. Las pruebas descritas fueron aisladas y sobre el código del commit.

La revisión automática de permisos rechazó el acceso del navegador a `http://127.0.0.1:7861/`, indicando que el permiso había sido denegado. No intenté acceder por otra vía.

