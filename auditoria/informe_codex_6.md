# Auditoría 6: corpus externo de British Council

**Recuento provisional: CRÍTICO 0 · SERIO 0 · MENOR 1.**

Informe en curso, iniciado en cuanto hubo evidencia sólida. Fecha: 9 de septiembre de 2026. Revisión inicial del repositorio: `425750f`. Alcance exclusivo: `auditoria/encargo_6.md`. No se han abierto otros informes de auditoría ni modificado otros archivos del proyecto.

## A. Integridad del corpus y manifiesto

En comprobación: inventario independiente en Downloads, contraste de nombres, contenido y fechas, y comparación exacta con el manifiesto.

## B. Aritmética de las exclusiones

Pendiente de ejecución: 59 − 2 − 10 = 47; identificación y motivo individual de las exclusiones; recuento estricto de 31. El comando `python` no está disponible en el PATH de esta sesión. El ejecutable de `D:/ll_bench/venv_cuda/Scripts/python.exe` devuelve «No Python at» para su intérprete base de Microsoft Store. Se está buscando otro intérprete instalado; esto es una limitación del entorno de auditoría, no un defecto atribuido al proyecto.

## C. Propagación de las cifras

### M1. MENOR hist?rico, CORREGIDO: dos explicaciones del cuadernillo conservaban la media antigua de A2

**Evidencia:** `entrega/notebook_proyecto.py:1751` y `entrega/notebook_proyecto.py:1984` comparan A1 y A2 como «0,504 frente a 0,548». El propio cuadernillo declara A2 = 0,5561 y n = 8 en `entrega/notebook_proyecto.py:1701` y `entrega/notebook_proyecto.py:1702`, y 47 textos en `entrega/notebook_proyecto.py:1704`. La búsqueda con `grep -n` verifica la contradicción sin depender de inferencia sobre el modelo.

**Consecuencia:** la actualización no llegó a las dos interpretaciones narrativas. A tres decimales, 0,5561 se escribe 0,556, no 0,548. La conclusión cualitativa sobre la cercanía de A1 y A2 no queda invalidada por esta corrección.

**Corrección propuesta, no aplicada:** sustituir 0,548 por 0,556 en ambas líneas, una vez terminada la reproducción numérica.

## Lo que comprobé y salió limpio

- La tabla del cuadernillo contiene n = [3, 8, 12, 12, 12] y medias [0,5040; 0,5561; 0,9276; 1,2414; 1,4952] (`entrega/notebook_proyecto.py:1701`, `:1702`).
- El fichero de datos de la figura contiene esas mismas cinco medias y esos tamaños (`entrega/datos_figuras/validacion.dat:2` a `:6`). Su suma es 47. Esta es todavía una comprobación de coherencia documental; la ejecución del modelo se documentará por separado.


## Continuaci?n sobre el ?rbol actualizado (`eb64755`)

Se han le?do los 13 commits de `git log --oneline dfd8cb2..HEAD`. No se han abierto otros informes. Las referencias hist?ricas de arriba se conservan para documentar el avance; las comprobaciones siguientes corresponden al ?rbol actual.

### A. Inventario reproducido: limpio

Inventario independiente de los 220 PDF de la ra?z de Downloads: selecci?n por nombres amplios, sin distinguir may?sculas (`learn\s*english`, `british\s*council`, prefijo de nivel con espacio o guion opcional), y por fecha de modificaci?n del 2 de septiembre. Resultado: 59 candidatos; todos contienen la marca British Council/LearnEnglish al extraerlos con `pypdf`. Sus fechas van del 02/09/2026 12:58:51 al 13:00:13. No hay duplicados binarios entre los cuerpos localizados.

La comparaci?n de conjuntos de nombres da cero diferencias en ambos sentidos entre disco, las 59 entradas del manifiesto y el patr?n actual `*LearnEnglish?Reading*.pdf` (`validar_local.py:100`; `entrega/manifiesto_corpus_externo.md:18`). Los 59 tienen nivel reconocible con el regex actual (`validar_local.py:29`). El manifiesto incluye el guion bajo de A2 en `:54` y el de B2 en `:84` (referencia pendiente de ratificar). No apareci? otra variante de nombre excluida.

Recuento bruto por nivel: A1 12, A2 10, B1 13, B2 12 y C1 12, id?ntico al manifiesto (`entrega/manifiesto_corpus_externo.md:11`).

### B. Extracci?n y filtro ejecutados: 59 ? 2 ? 10 = 47; estricto = 31

Se ejecutaron las funciones `cuerpo`, `cuerpo_estricto` y los regex extra?dos por AST del archivo actual, junto con `scoring.continuous_prose` y `scoring.words` reales, sobre los PDF le?dos mediante `pypdf`. No se reimplement? el filtro ni se modific? c?digo. La rama m?nima est? en `app/scoring.py:60`; la de listas, en `:71`.

Sin cuerpo: `A2__LearnEnglish-Reading-A2-An-airport-notice.pdf` y `A2__LearnEnglish-Reading-A2-An-infographic.pdf`.

Los diez rechazos devuelven exactamente `corto`:

| Nivel | Archivo (prefijo NIVEL__LearnEnglish-Reading-NIVEL- omitido) | Palabras |
|---|---|---:|
| A1 | A-poster-at-work.pdf | 66 |
| A1 | A-poster-for-exam-candidates.pdf | 98 |
| A1 | A-restaurant-menu.pdf | 101 |
| A1 | A-study-timetable.pdf | 129 |
| A1 | An-airport-departures-board.pdf | 43 |
| A1 | Business-cards.pdf | 79 |
| A1 | Notes-at-work.pdf | 50 |
| A1 | Student-card-application.pdf | 74 |
| A1 | Text-messages-to-a-friend.pdf | 48 |
| B1 | An-email-request-for-help.pdf | 128 |

Aceptados por nivel: 3, 8, 12, 12, 12 = **47**. Con saltos de l?nea: 1, 4, 6, 10, 10 = **31**. Se confirma el ?nico A1 del filtro estricto.

La ejecuci?n completa de `validar_local.py` con el Python 3.12.14 disponible arranc? y se detuvo en `validar_local.py:85` / `app/scoring.py:177`: falta `transformers`. Este int?rprete s? dispone de `pypdf` y NumPy, pero no de torch. La reproducci?n de las puntuaciones contin?a pendiente; los recuentos anteriores s? son resultados ejecutados, no cifras copiadas.

### C. Actualizaci?n de M1

Las dos frases est?n corregidas a ?0,504 frente a 0,556? en `entrega/notebook_proyecto.py:1751` y `:1987`. Se cierra el hallazgo del parcial; no se aplica ninguna correcci?n al cuadernillo.
