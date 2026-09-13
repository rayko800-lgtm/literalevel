import { HttpInterceptorFn } from '@angular/common/http';

const CLAVE = 'literalevel.lector';

/** El identificador de este navegador. Hace el papel del `session_hash` de
 *  Gradio: separa los datos de un lector de los de otro. No es una contraseña:
 *  lo que cuesta dinero va detrás de usuario y contraseña. */
function crearId(): string {
  try {
    if (crypto && 'randomUUID' in crypto) return crypto.randomUUID();
  } catch { /* contexto inseguro */ }
  const aleatorio = new Uint8Array(16);
  crypto.getRandomValues(aleatorio);
  return Array.from(aleatorio, b => b.toString(16).padStart(2, '0')).join('');
}

let enMemoria: string | null = null;

export function idLector(): string {
  if (enMemoria) return enMemoria;
  try {
    let id = localStorage.getItem(CLAVE);
    if (!id || id.length < 16) {
      id = crearId();
      localStorage.setItem(CLAVE, id);
    }
    enMemoria = id;
  } catch {
    // Ventana privada con almacenamiento bloqueado: vale para esta visita.
    enMemoria = crearId();
  }
  return enMemoria;
}

/** Pone `X-Lector` en todas las peticiones al motor. */
export const interceptorLector: HttpInterceptorFn = (peticion, siguiente) => {
  if (!peticion.url.includes('/api/')) return siguiente(peticion);
  return siguiente(peticion.clone({ setHeaders: { 'X-Lector': idLector() } }));
};
