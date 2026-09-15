import { describe, expect, it } from 'vitest';
import { Sonador } from './audio';

/** Auditoría de 4e, ronda 2: con «Escuchar y ver» y «Cerrar 3D» en el mismo turno,
 *  el mp3 terminaba de prepararse con el visor desmontado y sonaba igual. */
describe('el sonador del visor 3D', () => {
  it('destruido, no prepara ni hace sonar nada', async () => {
    const s = new Sonador();
    s.destruir();
    await expect(s.preparar('/api/audio/x.mp3')).resolves.toBeNull();
  });
});
