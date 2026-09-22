import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, poseNumerica } from './escena';
import { aVelocidad, cicloSonido } from './animacion';
import { CatalogoPoses, poseDe } from './poses';
import poses from './poses.ejemplo.json';

const catalogo = poses as unknown as CatalogoPoses;
// Prueba la interpolacion que utiliza la escena real sin crear WebGL.
const en = (simbolo: string, velocidad: number, tiempo: number) => {
  const escena = Object.create(EscenaBoca.prototype);
  const linea = aVelocidad(cicloSonido(poseDe(catalogo, simbolo)!, catalogo), velocidad);
  escena.linea = { total: linea.total, claves: linea.claves.map(c => {
    const n = poseNumerica(c.pose);
    if (c.hacia) {
      const hacia = poseNumerica(c.hacia);
      n.forEach((v, i) => n[i] = v + (hacia[i] - v) * (c.f ?? 0.5));
    }
    return { t: c.t, n };
  }) };
  return escena.poseDeLinea(tiempo / velocidad) as Float64Array;
};

describe('D4.4b: cierre bilabial en la linea existente', () => {
  for (const velocidad of [1, 0.5, 0.25]) {
    for (const simbolo of ['p', 'b']) {
      it(`/${simbolo}/ cierra, mantiene y libera a ${velocidad}x`, () => {
        expect(en(simbolo, velocidad, 0.42)[I_CIERRE_LABIOS]).toBe(0);
        expect(en(simbolo, velocidad, 0.70)[I_CIERRE_LABIOS]).toBeGreaterThan(0);
        expect(en(simbolo, velocidad, 0.70)[I_CIERRE_LABIOS]).toBeLessThan(1);
        expect(en(simbolo, velocidad, 1.2)[I_CIERRE_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.5)[I_CIERRE_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.6)[I_CIERRE_LABIOS]).toBeCloseTo(0.5);
        expect(en(simbolo, velocidad, 2.25)[I_CIERRE_LABIOS]).toBe(0);
      });
    }
    it(`/m/ mantiene contacto con menor compresion a ${velocidad}x`, () => {
      expect(en('m', velocidad, 1.6)[I_CIERRE_LABIOS]).toBe(1);
      expect(en('m', velocidad, 1.9)[I_CIERRE_LABIOS]).toBe(1);
      expect(en('m', velocidad, 1.6)[I_COMPRESION_LABIOS]).toBe(0.35);
      expect(en('p', velocidad, 1.2)[I_COMPRESION_LABIOS]).toBe(1);
    });
  }
  it('no activa el cierre en la punta, la raiz ni sus controles', () => {
    for (const s of ['θ','k','t','ŋ']) {
      expect(poseNumerica(poseDe(catalogo,s)!)[I_CIERRE_LABIOS]).toBe(0);
    }
  });
});
