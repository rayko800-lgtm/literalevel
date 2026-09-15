# Ronda 1 de revisión y auditoría — informe consolidado

Para Miguel. Noche del 14 al 15 de septiembre de 2026. Escrito por la central
con los cuatro informes de auditoría cruzada, el diagnóstico del caso Esmeralda
y la prueba como persona del front publicado. Cada hallazgo lleva su dueño.

## En una frase

La app funciona y lo que ve un usuario está bien, pero la auditoría encontró
**10 fallos serios**: 6 en el código y 4 en los documentos. Ninguno rompe la app.
Los del código afectan a la búsqueda de cuentos, a la velocidad cuando hay
varios usuarios a la vez y a la lectura natural. Los de los documentos afectan a
la credibilidad ante el profesor, porque algunas afirmaciones dicen más de lo que
se midió. Todos están asignados, y los dos de búsqueda del caso Esmeralda ya
están arreglados y en producción.

## Cómo se hizo

1. **Poner todo al día.** Cada sesión actualizó lo suyo: despliegue, pendientes,
   contratos entre módulos, README, skills y los cinco entregables.
2. **Auditoría cruzada a ciegas.** Nadie auditó su propio trabajo, y nadie leyó
   los otros informes antes de escribir el suyo.

| Área | Dueño | Auditó | Informe | Serios | Menores | Dudas |
|---|---|---|---|---|---|---|
| API y front | e6 | 4e | `cruzada_2026-09-14_api_front.md` | 2 | 8 | 1 |
| Voz, léxico, animación | 4e | e6 | `cruzada_2026-09-14_voz_lexico.md` | 2 | 6 | 1 |
| Catálogo y despliegue | f4 | e6 | `cruzada_2026-09-14_catalogo_despliegue.md` | 2 | 4 | 1 |
| Documentos | b9 y f4 | 4e | `cruzada_2026-09-14_documentos.md` | 4 | 11 | 2 |
| **Total** | | | | **10** | **29** | **5** |

Además: `diagnostico_encontrar_amor_b1_2026-09-14.md` (e6) y la prueba como
persona del front `45d9999` (f4).

## Los 10 serios, en palabras

### Código

1. **La corrección de voz y la subida de libros congelan el servidor** mientras
   trabajan. Con dos usuarios a la vez, uno espera al otro (medido: 3,4 s de
   espera en una petición que debería ser instantánea). Arregla **f4**.
2. **La vista previa gratuita del diccionario espera a la explicación de pago de
   otro usuario**, por un candado que abarca la llamada a OpenAI. Arregla **f4**.
3. **La lectura natural puede inventar «gonna»** cuando «going to» va seguido de
   un nombre: «I am going to school» se convertía en «I am gonna school» y así
   se leía en «Escúchalo natural». Arregla **4e**.
4. **Si una palabra se repite y se falla de dos maneras**, el segundo fallo pisa
   al primero y el sonido señalado es el equivocado. Arregla **4e**.
5. **Los 15.357 cuentos libres solo se buscan por título y autor.** Su gancho y
   su texto están vacíos en el índice de búsqueda. Es la causa de fondo de lo que
   vio Esmeralda: «amor» devolvía «MY FUTURE». Arregla **f4** recalculando ese
   índice en la CPU de esta máquina, sin gasto.
6. **La medición descarta 16 cuentos** (el final de cada grupo de bloques) y los
   cuenta como rechazados por el filtro. Arregla **f4**.

### Documentos

7. **El 0,908 se presenta como «validación ciega»** en la portada, el resumen y
   el guion de la demo, pero el propio documento (§7.4) reconoce que ese
   conjunto no es virgen. Es lo más delicado ante el profesor. Arregla **4e**.
8. **El coste de cómputo del catálogo está mal**: dice unas 3 horas de A100 dentro
   de 10 USD, cuando lo medido son 17 horas, y la medición real se hizo gratis.
   Arregla **4e**.
9. **El inventario de fuentes está incompleto**: faltan el corpus que entrenó el
   v4 (ELG CEFR), las cuatro fuentes de cuentos libres, common-pile y CMUdict, y
   una fila dice «sin descarga de texto» cuando se descargaron 16.000. La rúbrica
   exige describir fuente, calidad y relevancia. Arregla **4e**.
10. **Hay fuentes citadas sin referencia APA** (Imperial 2025, Grossman y Chen,
    Lexile, ELG…). La rúbrica exige referencias en APA. Arregla **4e**.

## Lo que ya está arreglado y en producción

- **Buscador del caso Esmeralda** (reinicio 16, Space `484b83b`): el nivel ya no
  pesa más que el tema, un título acertado sale siempre primero, y 163 textos
  que no son lectura en inglés quedan fuera.
- **Frase de la demo**: «Don't you want to come with us?» no produce el enlace
  «with us»; se quitó la promesa del guion y la presentación.
- **Cifras de libros de amor**: mi primera medida estaba mal; queda por fijar la
  regla exacta (4e y f4 difieren en uno y tres títulos según cómo se cuente).

## Lo que está en marcha

| Quién | Qué |
|---|---|
| f4 | Serios 1, 2, 5 y 6; menores de API y catálogo; reinicios 17 y 18 |
| 4e | Serios 3, 4, 7, 8, 9 y 10; menores de voz y de documentos |
| e6 | Pantalla nueva de Encontrar (aprobada) y cuatro detalles del front: la barra del 3D tapa la lengua, sombras suaves inactivas, dos «1 minutos», leyenda de enlaces sin enlaces |
| b9 | Parada sin cupo de Fable; su trabajo está repartido |

## Lo que se comprobó y está bien

- Aislamiento entre lectores, cobro atómico y rutas de archivo sin recorridos.
- Degradación sin clave de OpenAI en voz y léxico.
- Fonema determinista, pronunciación por forma con su marca de IA, animación con
  duración.
- Recuento del catálogo (16.251 cargados, 15.357 dentro, 894 fuera), licencias
  por fuente y guardas de los desplegadores.
- Las 25 entradas de la bibliografía están citadas; las cifras de los CSV, el
  diccionario y los modelos 3D cuadran.
- Las 18 suites de pruebas pasan.

## Estado de cierre (15 sep, 01:00)

| Serio | Qué | Commit | En producción |
|---|---|---|---|
| 1 | Voz y subidas congelaban el servidor | 31325a4 (f4) | Sí, Space f237e61 |
| 2 | Vista previa del diccionario esperaba a otro lector | 31325a4 (f4) | Sí, Space f237e61 |
| 3 | «gonna» inventado en la lectura natural | 2661452 (4e) | Pendiente de reinicio |
| 4 | Palabra repetida pisaba el fonema | 2661452 (4e) | Pendiente de reinicio |
| 5 | Cuentos libres buscables solo por título y autor | 6945046 (f4) | Reinicio 18 en curso |
| 6 | 16 colas de grupo descartadas sin medir | 6945046 (f4) | Reinicio 18 en curso |
| 7 | 0,908 presentado como «validación ciega» | 72c9ee6 (4e) | Documentos |
| 8 | Coste de cómputo mal contado | 72c9ee6 (4e) | Documentos |
| 9 | Inventario de fuentes incompleto | 72c9ee6 (4e) | Documentos |
| 10 | Citas sin referencia APA | 72c9ee6 (4e) | Documentos |

Menores cerrados: los 6 de voz y la duda de «set off» (d58b0be, 4e), los 4 del front de la prueba como persona y el rango de tiempo (e6), y los tiempos «1 minuto» en motor y front (cb799bc, f712d73). En curso: 11 menores de documentos (4e) y menores de API y catálogo (f4).

Nuevo, destapado al arreglar el 5: «amor» coincidía con un autor («Fenn, Amor») y títulos parecidos, y el modelo multilingüe apenas relaciona «amor» con «love». Decisión de la central: el nombre solo impulsa con coincidencia completa y no fija la ventana de relevancia si el tema no se parece; las búsquedas de una palabra en español se traducen con el diccionario local; fuera las filas con título «nan». Va al reinicio 19 (f4).

## Qué sigue

Cuando las tres sesiones cierren sus correcciones: reinicio y publicación,
prueba como persona sobre lo corregido, y **ronda 2** de auditoría cruzada solo
sobre lo que cambió, con los auditores rotados.
