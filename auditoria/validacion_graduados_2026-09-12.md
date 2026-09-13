# Validación del v4 con lectura graduada por sus editores — 12 de septiembre de 2026

**Estado: en curso.** Hecho African Storybook. StoryWeaver y VOA se están
descargando; esta nota se completa cuando terminen. **No se ha reentrenado nada:**
todo es evaluación con los pesos finales del v4.

Reproducible con:

```
python -X utf8 tools/niveles_african_storybook.py <booklistjs.php guardado>
python -X utf8 tools/bajar_storyweaver.py
python -X utf8 tools/bajar_voa.py --tope 60
python -X utf8 validar_graduados.py
```

Las puntuaciones, sin texto, quedan en `auditoria/validacion_graduados_puntuaciones.csv`.

## Qué se valida y qué no

Los niveles de estas fuentes los pone **cada editor, con su propio criterio y para
lectores infantiles**. No son niveles del MCER. Lo único que se puede comprobar es
el **orden**: si el nivel 1 del editor puntúa por debajo del 2, el 2 del 3, etc.

| Fuente | Nivel del editor | Textos en inglés | Licencia | ¿Al catálogo? |
|---|---|---|---|---|
| African Storybook | 1–5 (300 cruzados; 67 sin cruzar) | 367 | 316 CC BY · 48 CC BY-NC · 3 CC BY-NC-SA · 1 desconocida | Solo los CC BY |
| StoryWeaver | 1–4 | ~16.800 (descargando) | CC BY 4.0, toda la plataforma | Sí |
| VOA Learning English | **Sin nivel por artículo** | muestra de 60 por sección (descargando) | Dominio público; lo adaptado de AP, Reuters o AFP tiene derechos | Solo lo escrito por VOA |
| Let's Read | Sí | — | CC | **No descargado**: su lector no expone una API localizable |

## Decisiones de método

- **Cuentos cortos (decisión de Miguel):** los de 250 palabras o más se miden solos;
  los más cortos se juntan en bloques de al menos 250 palabras, **siempre dentro de
  la misma fuente y el mismo nivel**. La cola que no llega se declara y se deja fuera.
  Las métricas se dan también por separado para «solos» y «bloques».
- **Páginas en párrafos.** Un libro ilustrado trae una o dos frases por página en
  renglones sueltos. Tal cual, el filtro de prosa del v4 rechazó **70 de 219**
  unidades de African Storybook por «parece una lista, un menú o una tabla». Unir
  cada página en un párrafo —que es lo fiel al libro— dejó los rechazos en **9**.
- **Fuga:** se descarta cualquier texto que comparta la mitad o más de sus 8-gramas
  con ELG CEFR English, el corpus de entrenamiento. En African Storybook: **0 textos,
  máximo compartido 0,000**.
- **VOA:** se quita el aviso del reproductor («No media source currently available»)
  y el glosario final («Words in This Story»); se marca como interno todo artículo
  cuyo crédito diga que se adaptó de Associated Press, Reuters o AFP.

## African Storybook

210 de 219 unidades puntuadas; 9 rechazadas (7 del nivel 1, casi todas por forma de
lista incluso tras unir páginas, y 1 cola corta).

| Nivel del editor | Unidades | Media del v4 (0–2) | Desv. | Palabras medias |
|---|---|---|---|---|
| 1 | 8 | 0,315 | 0,198 | 301 |
| 2 | 37 | 0,323 | 0,195 | 325 |
| 3 | 32 | 0,405 | 0,134 | 371 |
| 4 | 61 | 0,493 | 0,248 | 492 |
| 5 | 36 | 0,598 | 0,225 | 739 |

| Métrica | Valor |
|---|---|
| Spearman v4 contra nivel | **0,416** |
| Spearman contar palabras contra nivel | **0,706** |
| v4 descontando la longitud (parcial) | 0,237 |
| Medias por nivel | **estrictamente crecientes** |

Por separado: los textos de 250 palabras o más (123 unidades) dan Spearman 0,307 y
medias **no** crecientes (el nivel 1 tiene solo 3 textos); los bloques de cuentos
cortos (51) dan 0,205 con medias crecientes en los cuatro niveles que llegan.

Los 67 cuentos que no se pudieron cruzar con un nivel (36 unidades) dan media
**0,475**, cuartiles 0,27 / 0,44 / 0,60: la misma franja que los niveles 2–4.

### Hallazgos

1. **El orden sale bien, pero lo explica sobre todo la longitud.** En estos cuentos,
   subir de nivel es sobre todo escribir más: contar palabras (0,706) ordena mejor
   que el modelo (0,416), y descontada la longitud al v4 le queda poco (0,237). Es
   distinto de OneStopEnglish, donde el modelo sí superaba a la longitud (0,800
   contra 0,692).
2. **Todo cae en 0,3–0,6**, que en la escala del v4 es la franja A1–A2. Para cuentos
   ilustrados infantiles es lo esperable: el modelo no confunde este material con
   lectura avanzada.
3. **El nivel 1 casi no se puede medir**: sus cuentos tienen tan pocas palabras que
   65 cuentos dan 8 unidades. Con esa *n*, su media es poco fiable.
4. **El formato engaña al filtro de prosa**: un libro ilustrado leído renglón a
   renglón parece una lista. Cualquier uso de la app con este material necesita la
   misma unión de páginas.

## Pendiente

- StoryWeaver: validar sobre la muestra aleatoria e intercalada por niveles que va
  bajando, y sobre el total al terminar.
- VOA: describir por sección y comparar lo escrito por VOA con lo adaptado de agencias.
- Let's Read: localizar un modo de descarga que respete sus condiciones.
