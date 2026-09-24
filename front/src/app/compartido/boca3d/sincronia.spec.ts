import { describe, expect, it } from 'vitest';
import posesCompletas from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';
import { AjustesPoses3d, CatalogoPoses, conAjustes3d, poseDe } from './poses';
import { ADELANTO, alAudio, alCompasDeTramos, cicloSonido } from './animacion';
import { finSonoro, tramosSonoros } from './audio';

const catalogo = conAjustes3d(posesCompletas as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
const ciclo = (s: string) => cicloSonido(poseDe(catalogo, s)!, catalogo);

describe('24 sep: la boca al compás del audio medido', () => {
  it('una fricativa sostiene la pose exactamente lo que suena su audio', () => {
    const base = ciclo('f');
    const l = alAudio(base, 'fricativa', 1.4);
    expect(l.sonidoEn).toBeCloseTo(base.claves[2].t);
    expect(l.claves[3].t - l.claves[2].t).toBeCloseTo(1.4);
    // Lo de después se desplaza sin cambiar su duración.
    expect(l.claves[4].t - l.claves[3].t).toBeCloseTo(base.claves[4].t - base.claves[3].t);
    expect(l.total).toBeCloseTo(base.total + 1.4 - (base.claves[3].t - base.claves[2].t));
  });

  it('una oclusiva suena en la explosión (fin del cierre), no al cerrar', () => {
    const base = ciclo('p');
    const l = alAudio(base, 'oclusiva', 0.3);
    expect(l.sonidoEn).toBeCloseTo(base.claves[3].t);
    expect(l.sonidoEn).toBeGreaterThan(base.sonidoEn);
    expect(l.claves[5].t - l.claves[3].t).toBeCloseTo(0.3);
    // El soplo de la sorda sigue dentro del tramo que suena.
    const soplo = l.aspiracion![0].en;
    expect(soplo).toBeGreaterThanOrEqual(l.claves[3].t);
    expect(soplo).toBeLessThanOrEqual(l.claves[5].t);
  });

  it('un diptongo reparte lo que suena entre sus dos objetivos', () => {
    const base = ciclo('aɪ');
    const l = alAudio(base, 'diptongo', 1.0);
    expect(l.sonidoEn).toBeCloseTo(base.claves[2].t);
    expect(l.claves[5].t - l.claves[2].t).toBeCloseTo(1.0);
  });

  it('sin audio medido (0) la línea no cambia', () => {
    const base = ciclo('s');
    expect(alAudio(base, 'fricativa', 0)).toBe(base);
  });

  it('finSonoro no cuenta el silencio del final', () => {
    const f = 1000, canal = new Float32Array(f);        // 1 s
    for (let i = 100; i < 600; i++) canal[i] = 0.3;       // suena de 0,1 a 0,6 s
    expect(finSonoro([canal], f)).toBeCloseTo(0.6, 3);
  });
});

describe('24 sep: la boca en cada tramo que suena del audio de Miguel', () => {
  it('tramosSonoros separa sonido largo, sonido corto y ejemplo, y no cuenta el ruido de fondo', () => {
    const f = 1000, canal = new Float32Array(5 * f);
    for (let i = 0; i < canal.length; i++) canal[i] = 0.004 * Math.sin(i);        // ruido de fondo
    const suena = (a: number, b: number) => { for (let i = a * f; i < b * f; i++) canal[i] = 0.3 * Math.sin(i / 3); };
    suena(0.1, 2.2); suena(3.3, 3.7); suena(4.5, 5.0);
    const t = tramosSonoros([canal], f);
    expect(t.length).toBe(3);
    expect(t[0].inicio).toBeCloseTo(0.1, 1); expect(t[0].fin).toBeCloseTo(2.2, 1);
    expect(t[2].inicio).toBeCloseTo(4.5, 1);
  });

  it('una fricativa llega a la pose al empezar cada tramo y la sostiene hasta que acaba', () => {
    const tramos = [{ inicio: 0.1, fin: 2.2 }, { inicio: 3.3, fin: 3.7 }];
    const l = alCompasDeTramos(poseDe(catalogo, 'f')!, catalogo, tramos, 0.1, 5)!;
    const pa = l.quieta;
    for (const { inicio, fin } of tramos) {
      const llega = l.claves.find(k => Math.abs(k.t - (ADELANTO + inicio)) < 1e-6);
      const sale = l.claves.find(k => Math.abs(k.t - (ADELANTO + fin)) < 1e-6);
      expect(llega?.pose).toBe(pa);
      expect(sale?.pose).toBe(pa);
    }
    // El audio arranca (archivo en 0) cuando la línea va por ADELANTO.
    expect(l.sonidoEn - 0.1).toBeCloseTo(ADELANTO);
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThan(l.claves[i - 1].t);
  });

  it('una oclusiva cierra antes de cada tramo y explota al empezar; la sorda lleva soplo en cada una', () => {
    const tramos = [{ inicio: 0.1, fin: 0.2 }, { inicio: 0.8, fin: 1.0 }, { inicio: 1.7, fin: 1.9 }];
    const l = alCompasDeTramos(poseDe(catalogo, 'p')!, catalogo, tramos, 0.1, 5)!;
    expect(l.aspiracion?.length).toBe(3);
    for (const { inicio } of tramos) {
      const explosion = l.claves.find(k => Math.abs(k.t - (ADELANTO + inicio)) < 1e-6);
      expect(explosion?.pose).toBe(l.quieta);
    }
  });

  it('sin tramos medidos no hay línea (se usa el ciclo de siempre)', () => {
    expect(alCompasDeTramos(poseDe(catalogo, 'f')!, catalogo, [], 0.1, 5)).toBeNull();
  });
});
