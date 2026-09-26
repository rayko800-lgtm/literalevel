import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { buscarVersionNueva, reiniciarConsultaVersion } from './version';

describe('build nuevo con el index viejo en caché', () => {
  let script: HTMLScriptElement;
  beforeEach(() => {
    sessionStorage.clear(); reiniciarConsultaVersion(); vi.useFakeTimers();
    script = document.createElement('script'); script.setAttribute('src', 'main-VIEJO123.js'); document.head.appendChild(script);
  });
  afterEach(() => {
    vi.useRealTimers(); script.remove(); document.querySelectorAll('[role=status]').forEach(n => n.remove());
  });

  it('recarga una vez si el servidor sirve otro main', async () => {
    const recargar = vi.fn();
    const pedir = vi.fn(async (_url: string) => '<script src="main-NUEVO456.js" type="module"></script>');
    expect(await buscarVersionNueva(recargar, pedir, 1_000_000)).toBe(true);
    expect(pedir.mock.calls[0][0]).toMatch(/^index\.html\?v=/);
    vi.advanceTimersByTime(500);
    expect(recargar).toHaveBeenCalledTimes(1);
    // Dentro de la ventana no vuelve a recargar (sin bucles).
    reiniciarConsultaVersion();
    expect(await buscarVersionNueva(recargar, pedir, 1_010_000)).toBe(false);
  });

  it('no hace nada si es el mismo build, ni pregunta más de una vez por minuto', async () => {
    const recargar = vi.fn();
    const pedir = vi.fn(async () => '<script src="main-VIEJO123.js"></script>');
    expect(await buscarVersionNueva(recargar, pedir, 2_000_000)).toBe(false);
    expect(await buscarVersionNueva(recargar, pedir, 2_030_000)).toBe(false);
    expect(pedir).toHaveBeenCalledTimes(1);
    expect(recargar).not.toHaveBeenCalled();
  });

  it('sin red o sin main en la respuesta, sigue igual', async () => {
    const recargar = vi.fn();
    expect(await buscarVersionNueva(recargar, async () => { throw new Error('offline'); }, 3_000_000)).toBe(false);
    reiniciarConsultaVersion();
    expect(await buscarVersionNueva(recargar, async () => '', 3_100_000)).toBe(false);
    expect(recargar).not.toHaveBeenCalled();
  });
});
