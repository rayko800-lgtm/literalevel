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
