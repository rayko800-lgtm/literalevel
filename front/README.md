# LiteraLevel · front

La interfaz que se entrega (decisión de Miguel, 13 sep 2026): Angular 22,
componentes standalone con signals y sin zone.js, pensada primero para un
móvil de 390 px y a una mano. Habla con el motor por HTTP (`app/api.py`, el
Space de Gradio `MikeMaki1763/literalevel`) y se publica como Space estático
aparte (`MikeMaki1763/literalevel-front`).

## Pantallas (`src/app/pantallas`, rutas en `app.routes.ts`, todas perezosas)

| Ruta | Pantalla | Qué hace |
|---|---|---|
| `/` | `inicio.ts` | Portada: seguir leyendo con el extracto de donde lo dejaste, demo del lector. |
| `/encontrar` | `encontrar.ts` | Buscador en español o inglés (ordena por tu nivel si lo hay), «A mi nivel» y «Mis libros» con subida de `.epub/.pdf/.txt`. |
| `/libro/:id` | `libro.ts` | Ficha: portada, nivel, aviso de contenido, veredicto para ti, curva capítulo a capítulo, índice. |
| `/leer/:id/:cap` | `lector.html/.ts/.css` | El lector: por páginas o seguido, consulta de palabras, «¿Cómo de difícil es?», teñido con el color del libro. |
| `/nivel` | `nivel.html/.ts/.css` | Tu nivel: cuestionario de una pregunta por pantalla, muestra de texto o un libro que ya leíste. |
| `/pronunciar` | `pronunciar.html/.ts/.css` | Grabar una frase, corrección con ritmo y lectura natural, tabla del AFI, «Escuchar y ver» (corte 2D y boca 3D). |
| `/palabras` | `palabras.ts` | Mis palabras: el cuaderno y las palabras que peor pronuncias. |
| `/estado` | `estado.ts` | Estado del sistema (lo lee de `/api/estado`). |

Lo compartido va en `src/app/compartido` (portada, tinte del lector, tarjeta de
libro, curva, ajustes, «Escuchar y ver», ritmo, boca 3D) y lo transversal en
`src/app/nucleo` (cliente de la API, sesión, preferencias, lector anónimo con
`X-Lector`, formato de números y recarga cuando se publica un build nuevo).

## Piezas que conviene conocer antes de tocar

- **Portadas** (`compartido/portada.ts`): tipográficas y deterministas, en SVG
  y CSS, sin imágenes externas. La familia (12: misterio, ciencia, amor,
  infantil…) sale de los `temas` que da la API; los colores, de una huella del
  id; el título pasa de 4,5:1 sobre el fondo. Si la API trae `portada_ia`
  (archivo en `/data/portadas`), se enseña esa con «Portada generada por IA, no
  oficial» y, si no carga, vuelve la tipográfica.
- **Lector teñido** (`compartido/tinte.ts`): fondo y acento de la paleta de la
  portada, en claro u oscuro según el tema, con el texto a 7:1 o más y el
  acento a 4,5:1. Se apaga en Ajustes («Color del libro en el lector»).
- **Boca 3D** (`compartido/boca3d`, su propio `README.md`): se enciende o apaga
  en `compartido/boca3d/interruptor.ts`. `pantallas/pronunciar.ts` importa
  `Boca3d` **directamente** desde `./boca3d/boca3d`: con una reexportación el
  `@defer` no separa el componente y three.js (unos 730 KB) entra en el chunk
  de Pronunciar. Los modelos `.glb` están en `public/boca3d` y en la demo;
  `node tools/boca3d_demo/comprobar_modelos.mjs` (desde la raíz) comprueba que
  coinciden y que los labios exponen sus shape keys.
- **Medido en bloque**: los cuentos libres cortos traen `medido_en_bloque`; la
  tarjeta lo dice junto a la letra y la ficha explica que el nivel es el del
  grupo.

## Desarrollo

```bash
# el motor, desde la raíz del repositorio
python -X utf8 -m uvicorn app.api:app --host 127.0.0.1 --port 8000

# el front, con el proxy de /api al motor
cd front
npx ng serve --host 127.0.0.1 --port 4210 --proxy-config proxy.conf.json
```

Sin `--proxy-config` la app arranca pero dice «No consigo hablar con el motor».
Pruébalo siempre a 390 px con emulación táctil (ver la skill
`probar-la-app-de-verdad`).

```bash
npx ng test --watch=false   # Vitest
npx ng build                # a dist/front/browser
```

## Publicar

```bash
python -X utf8 tools/desplegar_front.py --seco   # build y hashes, sin red ni token
python -X utf8 tools/desplegar_front.py          # publica en MikeMaki1763/literalevel-front
```

Lo que hace y por qué:

- **Solo publica lo confirmado**: si `front/` tiene cambios sin commit, no sube
  nada. En este árbol trabajan varias sesiones a la vez; para publicar HEAD sin
  tocar su trabajo a medias, usa un worktree limpio (`git worktree add --detach
  <dir> HEAD`, con `front/node_modules` enlazado como *junction*) y lanza la
  herramienta desde ahí.
- **Escribe la dirección del motor en la meta** `literalevel-api` del
  `index.html`. El build de Angular minifica `content=""` a `content` sin
  valor, y un publicador anterior la dejaba vacía: el front pedía `/api` a su
  propio dominio y todo daba 404. Ahora aborta si la meta no queda apuntando a
  la API (`pruebas_despliegue_front.py` lo cubre con el HTML minificado).
- **No borra chunks viejos**: una pestaña abierta con el build anterior los
  sigue pidiendo. Si aun así falla un chunk perezoso, `nucleo/version.ts`
  recarga una vez sola; el `@defer` del 3D tiene su botón «Recargar y
  reintentar».

Después de publicar, comprueba en el Space: `index.html` sirve el `main-*.js`
nuevo y la meta con la URL de la API, y la pantalla que cambiaste funciona a
390 px.
