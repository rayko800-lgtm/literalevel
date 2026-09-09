# Cinco auditorías, tres modelos: qué encontró cada uno

LiteraLevel se sometió a **cinco auditorías externas**, encargadas a modelos de
**dos familias distintas** —Codex/Astra de OpenAI y Fable de Anthropic—, todas a
ciegas: a ninguno se le dijo qué habían encontrado los anteriores ni qué se
había corregido.

Este documento no es otra auditoría. Es la lectura de las cinco juntas, y
existe por una razón concreta: **cuando dos modelos que no se ven encuentran el
mismo defecto por separado, ese defecto era real.** Y cuando solo lo encuentra
uno, dice algo sobre en qué es bueno cada uno.

---

## 1. La progresión

| Ronda | Auditor | Críticos | Serios |
|---|---|---|---|
| 1 | Codex/Astra | **4** | 14 |
| 2 | Fable | **2** | 8 |
| 3 | Fable | **1** | 8 |
| 4 | Fable | **0** | 4 |
| 5 | Codex/Astra | **0** | 6 |

Siete críticos en total, todos verificados a mano contra el código antes de
tocar nada, y todos cerrados.

---

## 2. Dónde coincidieron, sin verse

Cuatro defectos los encontraron **las dos familias por separado**. Esa
coincidencia es la evidencia más fuerte de todo este proceso.

| Defecto | Codex/Astra | Fable |
|---|---|---|
| **Las «6,3 horas de A100» no salían de ningún cálculo** | H13 | serio, 2.ª ronda |
| **Pruebas que informaban éxito devolviendo la lista de violaciones** | H16 (cuatro casos) | serio (tres más) |
| **`validar_local.py` podía aprobar sin evaluar ni un texto** | H11 | serio, mismo archivo |
| **Confusión entre el corpus interno y el externo** | H05 («ciego», «nunca vio») | serio (0,908 atribuido a los externos) |

Las cuatro eran ciertas. La de las pruebas es la más incómoda de las cuatro:
**cuatro pruebas sustantivas no podían fallar**, lo cual es peor que no
tenerlas, porque dan confianza sin darla.

---

## 3. Dónde NO coincidieron, que es por qué se usaron dos

Ninguno de estos seis lo habría encontrado el otro.

**Solo Fable vio:**

- Que el Cuadro 8 evaluaba el modelo v2 **sobre sus propios datos de
  entrenamiento** —151 de los 189 artículos de OneStopEnglish—, comparándolo
  contra un v1 que no los había visto. Verificable en tres líneas del volcado.
- Que el «Transformer afinado» del Cuadro 7 es un `roberta-base` de 125 M, **no
  el modelo desplegado**, que es un `distilroberta` de 82 M entrenado sobre otro
  corpus. Un lector razonable atribuía sus cifras al v4.
- Que el filtro de prosa descrito en el documento no es el que aplica
  `scoring.continuous_prose`, y que eso explica la mitad de la diferencia entre
  los 38 textos de Colab y los 45 locales.

**Solo Astra vio:**

- Que se atribuía **causalidad** a una comparación que cambia cuatro cosas a la
  vez: representación, arquitectura, preentrenamiento y objetivo.
- Que **agrupar por libro no separa autores**: dos obras del mismo autor pueden
  caer a ambos lados de la partición, y eso no se comprobó.
- Que decir «esto no se arregla publicando nada» era **falso**: recalcular la
  aritmética de las métricas no necesita los textos, solo las 144 parejas de
  etiqueta y predicción, que se pueden publicar anonimizadas.

**El patrón es bastante claro:** Fable persigue mejor las tablas, las cifras y
la trazabilidad entre archivos. Astra persigue mejor la lógica del argumento y
lo que una afirmación da por supuesto.

---

## 4. La lección de método, que costó dinero aprender

**Un encargo de auditoría tiene que caber en la ventana de créditos del
auditor**, y eso resultó ser lo que más condiciona el resultado.

| Encargo | Tokens | Resultado |
|---|---|---|
| Auditoría completa, «lee y señala» | 180.448 | Informe de 24 hallazgos |
| Auditoría completa, «verifica ejecutando» | 151.193 | **Nada.** Murió leyendo |
| Coherencia de cifras entre archivos | 137.228 | **Nada.** Murió leyendo |
| **Un archivo, cuatro apartados** | ~90.000 | Informe de 11 hallazgos |

Pedir más rigor sobre el mismo alcance no cabe: verificar ejecutando multiplica
el gasto por cada comprobación. La pasada que sí entregó fue la más estrecha.

Y aun así, **las pasadas que murieron no fueron inútiles**: su fase de búsqueda
quedó en el registro, y ahí se vio que varias cifras corregidas en
`documento.md` seguían viejas en `documento.tex`, en el cuadernillo y en
`estrategia.md`.

---

## 5. Lo que ningún auditor encontró, y hay que decirlo

Las cinco auditorías miran el **texto y el código**. Ninguna abrió la aplicación
desplegada ni la usó como usuario. El defecto de producto más grave del proyecto
—que un lector de nivel A1 recibía un desplegable vacío, porque de los 1.197
libros del catálogo solo 148 se pueden abrir y **ninguno es A1**— lo encontró
una investigación aparte sobre retención, no una auditoría.

Conviene tenerlo presente antes de confiar demasiado en un informe limpio: **una
auditoría documental dice que lo escrito se sostiene, no que el producto sirva.**
