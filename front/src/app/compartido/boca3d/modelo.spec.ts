import { describe, expect, it } from 'vitest';
import posesCompletas from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';
import { AjustesPoses3d, CatalogoPoses, conAjustes3d, poseDe } from './poses';
import { TramoFonema, clavesModelo } from './modelo';

const cat = conAjustes3d(posesCompletas as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
const tramo = (s: string, t0: number, t1: number): TramoFonema => ({ simbolo: s, pose: poseDe(cat, s)!, t0, t1 });

describe('25 sep: el modelo articulatorio aprendido (dominancia, GRID)', () => {
  const frase = [tramo('b', 0.3, 0.38), tramo('ɑ', 0.38, 0.6), tramo('p', 0.6, 0.68), tramo('u', 0.68, 0.95)];
  const claves = clavesModelo(frase, cat.reposo, 0, 1.3);

  it('una clave cada 40 ms, en orden, con la mandíbula dentro del rango', () => {
    expect(claves.length).toBe(33);
    for (let i = 1; i < claves.length; i++) expect(claves[i].t).toBeGreaterThan(claves[i - 1].t);
    for (const k of claves) expect(k.pose.mandibula).toBeGreaterThanOrEqual(0), expect(k.pose.mandibula).toBeLessThanOrEqual(1);
  });

  it('la mandíbula abre más en /ɑ/ que en /p/', () => {
    const en = (t: number) => claves.reduce((a, b) => (Math.abs(b.t - t) < Math.abs(a.t - t) ? b : a)).pose.mandibula;
    expect(en(0.49)).toBeGreaterThan(en(0.64) + 0.05);
  });

  it('en el centro de /p/ domina /p/ (labios cerrados)', () => {
    const k = claves.reduce((a, b) => (Math.abs(b.t - 0.64) < Math.abs(a.t - 0.64) ? b : a));
    expect(k.pose.labios).toBe('cerrados');
    expect(k.f ?? 0).toBeLessThan(0.5);
  });

  it('el redondeo de /u/ asoma antes de que suene (coarticulación anticipatoria)', () => {
    const antes = claves.filter(k => k.t > 0.55 && k.t < 0.68);
    expect(antes.some(k => (k.hacia?.labios === 'muy_redondeados' || k.hacia?.labios === 'redondeados') && (k.f ?? 0) > 0.1
      || k.pose.labios === 'muy_redondeados' || k.pose.labios === 'redondeados')).toBe(true);
  });
});
