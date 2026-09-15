/** Avisos y ayudas que se ven una vez: se guardan en el navegador, sin cuenta.
 *  Si no hay almacenamiento (modo privado estricto), se enseñan siempre. */

export function sinVer(clave: string): boolean {
  try { return localStorage.getItem(clave) !== 'vista'; } catch { return true; }
}

export function marcarVista(clave: string): void {
  try { localStorage.setItem(clave, 'vista'); } catch { /* sin almacenamiento */ }
}

export function olvidarVista(clave: string): void {
  try { localStorage.removeItem(clave); } catch { /* sin almacenamiento */ }
}
