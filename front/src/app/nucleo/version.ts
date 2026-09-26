/** Una pestaña abierta con un build anterior, tras publicar uno nuevo.
 *
 *  El Space estático solo guarda el último build. La pestaña vieja pide al
 *  navegar un chunk que ya da 404 y el router fallaba en silencio: el logo y
 *  los enlaces no hacían nada (f4, 13 sep; quizá lo que le pasó a Miguel en el
 *  móvil). Se recarga una sola vez en el destino, con una marca en
 *  sessionStorage para no entrar en bucle si el chunk falta de verdad. */

const CLAVE = 'literalevel.recargaPorVersion';
const VENTANA_MS = 30_000;
// Chrome, Firefox, Safari y el mensaje de webpack, por si acaso.
const PATRON = /Failed to fetch dynamically imported module|error loading dynamically imported module|Importing a module script failed|Loading chunk/i;

export function esVersionVieja(error: unknown): boolean {
  const texto = error instanceof Error ? `${error.name}: ${error.message}` : String(error ?? '');
  return PATRON.test(texto);
}

/** true si va a recargar. `recargar` se inyecta para poder probarlo. */
export function recargarSiVersionVieja(
  error: unknown,
  destino: string | undefined,
  recargar: () => void = () => location.reload(),
): boolean {
  if (!esVersionVieja(error)) return false;
  try {
    const antes = Number(sessionStorage.getItem(CLAVE) || 0);
    if (Date.now() - antes < VENTANA_MS) return false;
    sessionStorage.setItem(CLAVE, String(Date.now()));
  } catch {
    /* sin sessionStorage: sin marca, pero la recarga trae el build nuevo igual */
  }
  avisar();
  setTimeout(() => {
    // Recargar ya en la pantalla a la que iba. Justo antes de recargar y no al
    // principio: tras el error, el router devuelve la URL a la de antes y
    // pisaba el destino (la prueba acabó en «#/» en vez de «#/estado»).
    if (destino) {
      try { history.replaceState(history.state, '', '#' + destino); } catch { /* sigue en la actual */ }
    }
    recargar();
  }, 400);
  return true;
}

function avisar(): void {
  if (typeof document === 'undefined') return;
  const aviso = document.createElement('div');
  aviso.setAttribute('role', 'status');
  aviso.textContent = 'Hay una versión nueva de Pléyade. Recargando…';
  aviso.style.cssText = 'position:fixed;left:50%;top:12px;transform:translateX(-50%);z-index:9999;'
    + 'padding:.6rem 1rem;border-radius:999px;background:#1f2a44;color:#fff;font:600 14px system-ui,sans-serif;'
    + 'box-shadow:0 6px 20px rgba(0,0,0,.3)';
  document.body.appendChild(aviso);
}

/** Un móvil que guarda el index.html viejo (26 sep: el Space no manda
 *  Cache-Control, y el de Miguel siguió con el build anterior en todas las
 *  pestañas menos la portada). El chunk viejo sigue existiendo, así que no
 *  hay 404 que lo delate: se pregunta al servidor por el index actual, sin
 *  caché, y si su main-*.js no es el que corre aquí, se recarga una vez. */
const PATRON_MAIN = /main-[A-Za-z0-9_-]+\.js/;
const CADA_MS = 60_000;
let ultimaConsulta = 0;

export function mainActual(doc: Document = document): string | null {
  for (const s of Array.from(doc.querySelectorAll('script[src]'))) {
    const m = (s.getAttribute('src') ?? '').match(PATRON_MAIN);
    if (m) return m[0];
  }
  return null;
}

/** true si ha pedido recargar. En desarrollo (sin hash en main.js) no hace nada. */
export async function buscarVersionNueva(
  recargar: () => void = () => location.reload(),
  pedir: (url: string) => Promise<string> = url => fetch(url, { cache: 'no-store' }).then(r => r.ok ? r.text() : ''),
  ahora = Date.now(),
): Promise<boolean> {
  const actual = mainActual();
  if (!actual || ahora - ultimaConsulta < CADA_MS) return false;
  ultimaConsulta = ahora;
  let html = '';
  try { html = await pedir('index.html?v=' + ahora); } catch { return false; }
  const servido = html.match(PATRON_MAIN)?.[0];
  if (!servido || servido === actual) return false;
  try {
    const antes = Number(sessionStorage.getItem(CLAVE) || 0);
    if (ahora - antes < VENTANA_MS) return false;
    sessionStorage.setItem(CLAVE, String(ahora));
  } catch { /* sin sessionStorage: recarga igual */ }
  avisar();
  setTimeout(recargar, 400);
  return true;
}

/** Solo para las pruebas. */
export function reiniciarConsultaVersion(): void { ultimaConsulta = 0; }
