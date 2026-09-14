# Auditoria de voz recuperada de [Central]

Fecha: 13 de septiembre de 2026. Base inspeccionada: `f1cfb5d`.
Encargo original: cambios de `3a3d546` y su estado posterior en voz, lexicon
y los consumidores de Gradio/API. Este informe no modifica esos modulos.
Revision estatica: `git show` y lectura dirigida. No se ejecuto la app,
ninguna prueba, ninguna migracion sobre datos reales ni llamadas a OpenAI.
Las lineas siguientes corresponden a los archivos de esa base, no al diff
historico. No se han leido otras auditorias para obtener los hallazgos.

## Hallazgos

### Serio: la cache TTS no evita solicitudes simultaneas duplicadas

- Archivo: `app/voz.py:469`, `app/voz.py:483`, `app/voz.py:614`.
- Cita: `if reutilizable.is_file() and reutilizable.stat().st_size > 0:`.
- Escenario: dos lectores fallan la misma palabra con cache vacia. Ambos
  comprueban que falta el mp3 y ambos llaman a `audio.speech.create` antes de
  que ninguno lo publique. La escritura atomica evita un mp3 parcial, pero
  no impide pagar dos solicitudes. El grupo de hilos deduplica dentro de UNA
  llamada, no entre llamadas. Gradio y API comparten esta funcion.
- Arreglo: exclusion mutua por clave de audio alrededor de releer cache,
  generar y publicar, con liberacion en `finally`; si se usan varios procesos,
  la exclusion debe abarcar tambien esos procesos.
- Falta una prueba con dos consumidores y un proveedor simulado bloqueado
  por barrera: esperar una solicitud y dos rutas identicas. No reproduje
  concurrencia ni cobros reales en esta revision.

### Serio: una migracion concurrente puede descartar un nuevo fallo

- Archivo: `app/voz.py:508`, `app/voz.py:510`, `app/voz.py:541`.
- Citas: `PRAGMA table_info(palabras_debiles)` y
  `ALTER TABLE palabras_debiles ADD COLUMN frase TEXT`.
- Escenario: dos conexiones sobre una base vieja leen el esquema sin
  `frase`. La primera hace ALTER; la segunda intenta el mismo ALTER y falla
  por columna duplicada. Si procede de `registrar_fallos`, el `except`
  silencioso termina la operacion antes del INSERT: ese intento no se guarda.
  Si procede de la consulta, se devuelve `[]` aunque exista historial.
  No se afirma que la migracion borre filas viejas: no hay DROP ni reemplazo
  de tabla en este camino.
- Arreglo: serializar comprobacion y ALTER con transaccion `BEGIN IMMEDIATE`,
  confirmar antes de entregar la conexion y cerrarla si falla; alternativamente
  releer el esquema tras un conflicto de migracion antes de continuar.
- La prueba de `pruebas_extremas.py:6876` comprueba migracion secuencial y
  conservacion de contadores, no la carrera. No se ejecuto dicha prueba.

### Menor: el filtro de indices rechaza prosa con nombres propios

- Archivo: `app/ui.py:2988`, consumidor `app/ui.py:3557`.
- Cita: `if minusculas < 3: return True`.
- Escenario construido, deducido de la regla: `Alice met Mary near London
  Bridge.` tiene seis palabras, solo `met` y `near` empiezan en minuscula; es prosa
  admisible y se descarta. Tambien se descarta `STOP THAT NOISE AND COME HERE!`
  por el umbral de mayusculas, aun pudiendo ser dialogo de novela.
- Falso negativo construido: `Chapter one: the road to the old house 12`
  tiene suficientes minusculas y solo un numero; el filtro lo acepta. Es un
  posible titulo de indice, no una cita encontrada en el corpus. La seleccion
  final depende ademas del partidor y de `_empieza_entera`.
- Arreglo: combinar estructura de parrafo/encabezado y columnas de paginas;
  no usar el recuento absoluto de minusculas como veto suficiente para prosa.
  Anadir estos contraejemplos al conjunto de regresion antes de afinar umbrales.

## Coste Y Limites

- `audios_de_palabras` limita a **8** entradas unicas en HEAD
  (`app/voz.py:602`); el commit original limitaba a 6. Cinco palabras pueden
  producir cinco TTS, pero NO se solicitan sin tope: existe ese maximo por
  practica y la puerta exterior por hora/cuenta. No es correcto reportar
  simplemente "TTS ilimitados".
- `app/ui.py:3732` y `app/api.py:1613` aplican el tope de voz; luego comprueban
  clave y `_puede_pagar` antes de `voz.practicar`.
- `SesionVoz` no tiene `llamadas_de_pago`. `generar_audio_correcto` devuelve
  ruta o None, no informacion de cobro. No se puede verificar el requisito de
  contar solicitudes exitosas despues de cada TTS con este contrato. El uso
  es por PRACTICA, no una unidad por cada llamada al proveedor. La politica
  conservadora de no devolverlo esta explicada en `app/ui.py:3760`.
- La normalizacion ocurre antes en `evaluar_pronunciacion` y en las piezas
  de `practicar`. La funcion publica `audios_de_palabras` por si sola NO
  normaliza; `['Fetters', 'fetters.']` produce claves diferentes porque el
  hash usa `texto` original (`app/voz.py:428`). No encontre un consumidor
  actual que entregue esas variantes en la misma practica; se registra como
  limite del contrato, no como regresion demostrada de la pantalla.

## Comprobado Y Correcto

- Sin clave, `_cliente` retorna antes de importar/construir OpenAI; las tres
  operaciones de voz devuelven None. `generar_audio_correcto` comprueba cache
  antes y puede devolver un mp3 existente sin clave. El contador de proveedor
  real no se ha medido.
- `usar_openai=False` existe en lexicon, NO en `voz.practicar`.
  `app/lexicon.py:942` evita construir cliente; sin cliente no se pide IPA,
  explicacion ni TTS a OpenAI. No se afirma que eso impida toda posible red
  de dependencias/modelos locales ausentes o del navegador al reproducir audio.
- La IPA de la definicion IA solo rellena los acentos ausentes en Kaikki
  (`app/lexicon.py:1104`) y activa `ipa_generada_por_ia`. La ficha Gradio
  muestra la marca (`app/ui.py:3234`) y la API expone el campo. En compuestos
  se pide IPA del compuesto, no se presenta la de una pieza como la del todo.
- `ResultadoLexico.ipa_generada_por_ia=False` y
  `SesionVoz.audios_palabras=field(default_factory=dict)` son adiciones
  compatibles. `Evaluacion.entendidas` tiene default y era anterior a
  `3a3d546`. `DetallePalabra.fonema` sigue obligatorio: no se anadio en ese
  commit y no debe atribuirsele como una nueva ruptura.
- En el esquema fuente los campos IPA son `str` obligatorios; el fonema
  lleva enum del inventario mas `ninguno`. No se ejecuto la conversion del
  SDK a esquema estricto ni una peticion Structured Outputs: no se da por
  verificada la aceptacion remota de ese esquema.
- La migracion agrega una columna nullable, conserva las filas viejas y usa
  UPSERT con `COALESCE` para conservar frase previa si no se proporciona otra.
  Ante DB corrupta, las consultas retornan `[]` y el registro silencia el
  error; no borra ni repara la base, ni distingue ausencia de historial de
  fallo de lectura en pantalla (`app/ui.py:3829`).
- UI y API llaman a `voz.practicar(..., guardar_fallos=False)` y registran
  luego solo con transcripcion valida, usando la ruta del lector. La funcion
  directa, con su default True, si registra todo como fallado si no hay
  transcripcion; es comportamiento anterior, no nuevo en este commit.

## Pendiente De Validacion

Concurrencia de migracion y cache con dobles sin red; cierre de conexiones
en error; parser/HTML real de Gradio y pantalla Angular; calidad fonetica de
IPA generada; facturacion del proveedor. Ninguna cifra de gasto o calidad se
ha inferido de un timeout o de que el SDK devuelva una ruta.
