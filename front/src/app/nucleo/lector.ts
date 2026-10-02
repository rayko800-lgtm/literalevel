import { HttpInterceptorFn } from '@angular/common/http';
import { HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { BASE_API } from './api';

const CLAVE = 'literalevel.lector';
const SESION = 'pleyade.sesion';
let tokenMemoria: string | null = null;

export function guardarSesion(token: string | null): void {
  tokenMemoria = token;
  try {
    if (token) sessionStorage.setItem(SESION, token);
    else sessionStorage.removeItem(SESION);
  } catch { /* disponible solo en esta visita */ }
}

export function tokenSesion(): string | null {
  try { return sessionStorage.getItem(SESION) ?? tokenMemoria; }
  catch { return tokenMemoria; }
}

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
  // No enviar una sesión a terceros que incluyan /api/ en su URL.
  const base = new URL(BASE_API || '/', location.origin);
  const url = new URL(peticion.url, location.origin);
  if (url.origin !== base.origin || !url.pathname.startsWith('/api/')) return siguiente(peticion);
  const token = tokenSesion();
  const headers: Record<string, string> = { 'X-Lector': idLector() };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return siguiente(peticion.clone({ setHeaders: headers })).pipe(catchError(error => {
    if (error instanceof HttpErrorResponse && error.status === 401) guardarSesion(null);
    return throwError(() => error);
  }));
};
