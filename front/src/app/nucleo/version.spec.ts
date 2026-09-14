import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { esVersionVieja, recargarSiVersionVieja } from './version';

describe('versión vieja del front', () => {
  beforeEach(() => { sessionStorage.clear(); vi.useFakeTimers(); });
  afterEach(() => { vi.useRealTimers(); document.querySelectorAll('[role=status]').forEach(n => n.remove()); });

  it('reconoce los mensajes de chunk perdido de cada navegador', () => {
    expect(esVersionVieja(new TypeError('Failed to fetch dynamically imported module: https://x/chunk-CYi-NC6H.js'))).toBe(true);
    expect(esVersionVieja(new TypeError('error loading dynamically imported module'))).toBe(true);
    expect(esVersionVieja(new TypeError('Importing a module script failed.'))).toBe(true);
    expect(esVersionVieja(new Error('Http failure response for /api/salud: 0'))).toBe(false);
  });

  it('recarga una sola vez y en el destino, sin bucle', () => {
    const recargar = vi.fn();
    const error = new TypeError('Failed to fetch dynamically imported module: chunk-X.js');
    expect(recargarSiVersionVieja(error, '/estado', recargar)).toBe(true);
    vi.advanceTimersByTime(500);
    expect(recargar).toHaveBeenCalledTimes(1);
    expect(location.hash).toBe('#/estado');
    // Si tras recargar vuelve a fallar enseguida, no se recarga otra vez.
    expect(recargarSiVersionVieja(error, '/estado', recargar)).toBe(false);
    vi.advanceTimersByTime(500);
    expect(recargar).toHaveBeenCalledTimes(1);
  });

  it('otros errores de navegación no recargan', () => {
    const recargar = vi.fn();
    expect(recargarSiVersionVieja(new Error('Cannot match any routes'), '/nada', recargar)).toBe(false);
    vi.advanceTimersByTime(500);
    expect(recargar).not.toHaveBeenCalled();
  });
});
