# Correr la tanda de Colab — guion para Miguel

Escrito el **jueves 10 de septiembre de 2026** por la noche. Diez minutos de tu
tiempo, y luego se queda trabajando solo.

> **Por qué lo tienes que hacer tú y no yo.** El conector de Colab está roto en
> esta máquina por un fallo diagnosticado: el servidor liga dos puertos
> distintos (IPv4 e IPv6) y anuncia solo el de IPv6, así que el navegador falla
> la conexión. Se probó cuatro veces el 8 de septiembre; dos de ellas colgaron
> treinta minutos y tumbaron el servidor. Y el Chrome que yo puedo controlar es
> **otro Chrome, aislado**, sin tu sesión de Google: hacerte teclear tu
> contraseña ahí sería peor que pedirte tres clics. Detalle en la skill
> `conectar-google`.

---

## Lo que cambia con la T4 gratis

**La T4 no gasta unidades.** El freno deja de ser el cupo y pasa a ser el
tiempo de sesión, y eso lo cambia todo: ya no hay que elegir entre 21 minutos de
A100 o nada.

Y hay un motivo para pensar que la T4 no va a ir tanto peor: en la A100 se midió
que **la tarjeta estaba parada el 80 % del tiempo** esperando a que Google Drive
entregase el siguiente `.txt`. Si el cuello de botella es el disco, una tarjeta
más lenta cuesta menos de lo que parece. **Pero eso hay que medirlo, no
suponerlo**, y la celda 11 lo mide.

---

## Los tres clics

1. **Abre Colab** (te lo dejo abierto en el navegador, si no:
   <https://colab.research.google.com>).
2. **Archivo → Subir cuaderno** y elige:
   ```
   C:\Users\laura\literalevel\colab_precalculo.ipynb
   ```
   *No se puede abrir desde GitHub porque el repositorio es privado.*
3. **Entorno de ejecución → Cambiar tipo de entorno → GPU → T4**, y guarda.

---

## Qué ejecutar, en este orden

| Celda | Qué hace | Ojo |
|---|---|---|
| **1** | Dice qué GPU tocó | Tiene que decir **Tesla T4** y ~15 GB |
| **2** | Monta Drive | **Te pide permiso en una ventana**: acepta con `rayko800@gmail.com` |
| **3** | Instala dependencias | Un par de minutos |
| **4** | Trae el código de LiteraLevel | |
| **5** | El catálogo oficial de Gutenberg | |
| **9** | Baja el modelo v4 del Hub y lo pone en la GPU | |
| **11** | **Mide la velocidad real** | **Pégame lo que imprima** |
| **12** | Prepara la lista de pendientes | Dirá cuántos libros quedan |
| **13** | Lanza la tanda | Es la que tarda |

**Sáltate la 6, la 7 y la 8** si solo vas a medir: son la descarga de textos.
**La 10** es la comprobación de media precisión y no hace falta.

### Antes de darle a la 13, dos valores

En la celda 13, arriba:

```python
HORAS_TOPE_ANALISIS = 3.5     # ponlo así para una sesión gratuita
```

Está en 8.0, que era para Colab Pro. Las sesiones gratuitas se cortan antes, y
**no pasa nada si se corta**: los resultados se guardan en Drive cada 500 libros
y la celda 13 es reanudable — al volver, se salta lo ya hecho. Si la dejas en
8.0 tampoco rompe nada, solo que el aviso ordenado de «guardo lo que llevo» no
llegará a tiempo.

En la celda 12 ya está puesto lo que quiero:

```python
MUESTRA_ALEATORIA = True      # no lo cambies
```

**Esto importa más de lo que parece.** Los ids de Gutenberg van por orden de
digitalización, que es cronológico: los primeros miles son sistemáticamente más
viejos —inglés del XIX, otra tipografía, otra longitud de frase—. Una tanda que
no llega a todo el catálogo y coge los primeros por id **no mide el catálogo,
mide el siglo XIX**. Con la muestra aleatoria, los mismos minutos dan algo que se
puede escribir en el documento con su margen.

---

## Qué me pegas cuando acabe

Tres cosas, y con eso hago las cuentas de verdad:

1. Lo que imprime la **celda 1** (qué GPU y cuánta memoria).
2. Lo que imprime la **celda 11**: `N ventanas/s` y las horas proyectadas.
3. Lo que imprime la **celda 13** al terminar o al cortarse: cuántos libros
   lleva y en cuánto tiempo.

Con el número de la celda 11 se sabe **por fin** lo que cuesta el catálogo
entero. Hasta ahora lo que hay escrito son 61 libros/min medidos con la tarjeta
esperando al disco, y una proyección de «unas 15 unidades» que **nadie ha
confirmado**. Esa proyección es la que decide si vale la pena comprar unidades o
si la T4 gratis llega sola.

---

## Si algo se pone feo

- **«No hay GPU disponible»**: la T4 gratis se reparte. Espera y reintenta, o
  prueba en un rato. No hay nada que arreglar del lado del cuaderno.
- **Se desconecta a media tanda**: normal en la capa gratuita. Vuelve a
  ejecutar la celda 13 y sigue donde iba.
- **La celda 2 no te pide permiso y falla**: cierra la sesión de Colab entera
  (Entorno de ejecución → Desconectar y eliminar) y vuelve a empezar. Montar
  Drive dos veces en la misma sesión da problemas.
- **Cualquier traza roja**: pégamela tal cual. No la interpretes ni la resumas.
