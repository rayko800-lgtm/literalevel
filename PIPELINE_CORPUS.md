# Pipeline de corpus externos — de la descarga al catálogo

Decidido por Miguel el 12 de septiembre de 2026. Cada fuente pasa por los mismos
pasos y **no avanza al siguiente sin superar su punto de control**. El modelo v4
**no se reentrena**: todo lo de aquí es medir, validar y catalogar.

## La regla, en una tabla

| ¿Licencia libre? | ¿Nivel del editor? | Qué se hace | ¿Al catálogo? |
|---|---|---|---|
| No (NC, ND, adaptado de AP/Reuters/AFP, desconocida) | Sí o no | Se mide y **valida internamente** | **No, nunca** |
| Sí (dominio público, CC BY) | Sí | **Primero se valida** el orden contra el nivel del editor; después entra | Sí, con la dificultad del v4 y el nivel del editor al lado |
| Sí | No | **Lo gradúa el v4** y ese es nuestro veredicto | Sí, con la dificultad del v4 |

El nivel de un editor infantil **no es MCER**: se valida el orden, no la letra.

## Los pasos

| # | Paso | Guion | Punto de control (no se sigue sin él) |
|---|---|---|---|
| 1 | **Descargar** con pausa entre peticiones, reanudable, respetando `robots.txt` y condiciones | `tools/bajar_*.py` | Cada texto trae fuente, id, URL, licencia, nivel del editor (o vacío) y `al_catalogo` |
| 2 | **Limpiar**: páginas en párrafos, fuera avisos de reproductor, glosarios y créditos | en el descargador y en `validar_graduados.py` | Muestra leída a mano: sin basura al principio ni al final |
| 3 | **Fuga** contra ELG CEFR English (8-gramas, umbral 50 %) | `validar_graduados.py` | Textos contaminados excluidos y contados |
| 4 | **Unidades**: ≥250 palabras solos; cortos en bloques ≥250 **sin mezclar fuente ni nivel** | `validar_graduados.py` | Cola corta declarada, no estirada |
| 5 | **Puntuar** con el v4 (mismo `scoring.Puntuador` que la app) | `validar_graduados.py` | Rechazos del filtro de prosa contados por motivo |
| 6a | **Validar** (con nivel): medias por nivel, Spearman, contar palabras, parcial sin longitud | `validar_graduados.py` | Resultado escrito en `auditoria/validacion_graduados_*.md`, salga bien o mal |
| 6b | **Describir** (sin nivel): reparto, cuartiles y comparación con las fuentes graduadas | `validar_graduados.py` | Idem |
| 7 | **Catalogar** solo `al_catalogo`: fila en el catálogo con fuente, licencia, atribución y dificultad del v4 | `tools/catalogar_corpus.py` | `pruebas_extremas.py` en verde; ningún texto con derechos en el CSV |
| 8 | **Abrir en la app**: el texto libre se sirve con su atribución | `app/catalogo.py`, `app/ui.py` | Probado en el navegador: buscar → abrir → leer |
| 9 | **Documentar** y propagar cifras a documento, estrategia, cuaderno y pendientes | — | PDF recompilados y comprobados |

## Estado por fuente

| Fuente | Nivel | Licencia | Paso alcanzado |
|---|---|---|---|
| African Storybook | 1–5 (300 de 367) | 316 CC BY al catálogo · 52 internos | 6a hecho |
| StoryWeaver | 1–4 | CC BY 4.0 (toda la plataforma) | 1 en curso (orden aleatorio) |
| VOA Learning English | sin nivel por artículo | dominio público; lo adaptado de agencias, interno | 1 casi terminado |
| Let's Read | sí | CC | 0: buscando modo de descarga |
