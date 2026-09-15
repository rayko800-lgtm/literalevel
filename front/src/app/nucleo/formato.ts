/** Formatos en español y la única regla de letra MCER del front.
 *  `cefr` es la de `ui._cefr`: empates hacia arriba, no `Math.round`. */

const ANCLAS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const;

export function cefr(publico: number | null | undefined): string {
  if (publico == null || !Number.isFinite(publico)) return '';
  const i = Math.floor(Math.min(5, Math.max(0, publico * 2.5)) + 0.5);
  return ANCLAS[Math.min(i, 5)];
}

export function num(x: number | null | undefined, decimales = 2): string {
  if (x == null || !Number.isFinite(x)) return '—';
  return x.toFixed(decimales).replace('.', ',');
}

/** 1.197 y no 1,197: en español el separador de miles es el punto. */
export function miles(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return '—';
  return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

export function reloj(minutos: number): string {
  if (minutos < 90) return `${Math.max(1, Math.round(minutos))} min`;
  const h = Math.floor(minutos / 60);
  const m = Math.round(minutos % 60);
  return m ? `${h} h ${String(m).padStart(2, '0')} min` : `${h} h`;
}

/** El tiempo que da la API (`ficha.reloj`) dice «1 minutos» con un cuento de un
 *  minuto, y «entre 1 minuto y 1 minuto» cuando el ritmo cómodo y el exigente
 *  coinciden: aquí se dice llano hasta que el motor lo diga bien (f4 y Central). */
export function tiempoLlano(tiempo: string | null | undefined): string {
  return (tiempo ?? '')
    .replace(/(^|[^\d,.])1 minutos\b/g, '$11 minuto')
    // Cada extremo es un tiempo entero de `ficha.reloj` («2 h 05 min», «2 h», «12 minutos»):
    // con un comodín, «entre 1 h y 1 h 30 min» se quedaba en «1 h 30 min».
    .replace(/\bentre (\d+ h \d+ min|\d+ h|\d+ minutos?) y (\d+ h \d+ min|\d+ h|\d+ minutos?)/g,
      (todo, a: string, b: string) => a === b ? a : todo);
}

/** Minutos de lectura de un capítulo: 180 palabras/min cómodo (`ficha.PPM_COMODO`). */
export function minutosDe(palabras: number): number {
  return Math.max(1, Math.round(palabras / 180));
}

export interface Encaje { texto: string; clase: 'verde' | 'ambar' | 'acento' | ''; }

/** Cómo le queda un texto a este lector, con el margen de `perfil.RETO` (0,15). */
export function encaje(dificultad: number | null | undefined, nivel: number | null | undefined): Encaje | null {
  if (dificultad == null || nivel == null) return null;
  const d = dificultad - nivel;
  if (d <= -0.45) return { texto: 'Fácil para ti', clase: 'acento' };
  if (d <= 0.15) return { texto: 'A tu medida', clase: 'verde' };
  if (d <= 0.45) return { texto: 'Un reto', clase: 'ambar' };
  return { texto: 'Exigente', clase: '' };
}

export const BANDAS: Record<string, string> = {
  'básico': 'Básico', basico: 'Básico', intermedio: 'Intermedio', avanzado: 'Avanzado',
};
