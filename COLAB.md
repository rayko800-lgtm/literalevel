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

## Ya está montado: lo hice yo

El **jueves 10 a las 19:00** quedó así, y lo puedes comprobar en pantalla:

- Cuaderno subido a tu Drive y abierto:
  <https://colab.research.google.com/drive/15P43BFhYBlmZCnbJcxIYj_H_Y6Ps9CkX>
- Cuenta: **rayko800@gmail.com** (la que tiene Colab Pro y `literalevel_bigdata`).
  Tu Chrome estaba dentro con `miguel.reyes.carrillo19@gmail.com`, que **no**
  tiene el Drive del proyecto: con esa cuenta el cuaderno no habría encontrado
  ni un texto.
- GPU: **Tesla T4, 14,6 GB**, CUDA activo, torch 2.11.0+cu128. Confirmado
  ejecutando la celda 1.
- La T4 va escrita en el propio `.ipynb` (`gpuType: "T4"`, sin `machine_shape`),
  así que cualquiera que lo abra la hereda. Antes decía A100 con memoria alta,
  que es de pago.

### Lo único que tienes que tocar

La celda 2 monta tu Drive y eso **exige tu permiso**: sale un diálogo
«¿Permitir que este cuaderno acceda a tus archivos de Google Drive?».

1. **Conectar con Google Drive**
2. En la ventana de Google, elige **rayko800@gmail.com**
3. **Permitir**

Es el único permiso de toda la sesión. Cuando lo des, avísame y sigo con el
resto de las celdas.

---

## Qué celdas van, con la numeración del cuaderno

| Celda | Qué hace | |
|---|---|---|
| **1** | Qué GPU tocó | ✅ hecha: Tesla T4 |
| **2** | Monta Drive | ⏳ **espera tu permiso** |
| **3** | Dependencias | un par de minutos |
| **4** | El código de LiteraLevel | |
| **5** | El catálogo oficial de Gutenberg | |
| ~~6, 6b, 6c~~ | Descargar textos | **se saltan**: medimos sobre lo ya descargado |
| **7** | Baja el modelo v4 y lo pone en la GPU | |
| ~~8~~ | Desviación de media precisión | se salta, no hace falta |
| **9** | **Mide la velocidad real** | **la importante** |
| **10** | Prepara la lista de pendientes | dirá cuántos quedan |
| **10b** | Lanza la tanda | la que tarda |
| ~~11, 11b~~ | El catálogo final y una sonda | al final, otro día |

*(Ojo: es la numeración que lleva el cuaderno en sus propios títulos, no la
posición en la lista. La celda «7» es la novena de arriba abajo.)*

### Los dos valores, ya puestos

En la celda **10b** ya está puesto:

```python
HORAS_TOPE_ANALISIS = 3.5     # sesion gratuita: se corta antes que una de Pro
```

Estaba en 8.0, que era para Colab Pro. Las sesiones gratuitas se cortan antes, y
**no pasa nada si se corta**: los resultados se guardan en Drive cada 500 libros
y la celda 13 es reanudable — al volver, se salta lo ya hecho. Si la dejas en
8.0 tampoco rompe nada, solo que el aviso ordenado de «guardo lo que llevo» no
llegará a tiempo.

Y en la celda **10**:

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

1. ~~Qué GPU~~ ya lo tengo: Tesla T4, 14,6 GB.
2. Lo que imprime la **celda 9**: `N ventanas/s` y las horas proyectadas.
3. Lo que imprime la **celda 10b** al terminar o al cortarse: cuántos libros
   lleva y en cuánto tiempo.

Con el número de la celda 9 se sabe **por fin** lo que cuesta el catálogo
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
