import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, cierreLabial, poseNumerica } from './escena';
import { SOPLO_S, aVelocidad, cicloSonido, lineaPalabra } from './animacion';
import { CatalogoPoses, poseDe, trocearIpa } from './poses';
import poses from './poses.ejemplo.json';

const catalogo = poses as unknown as CatalogoPoses;

describe('D4.4b v4: reposo con los labios casi juntos', () => {
  it('en reposo los labios neutros se cierran del todo, sin compresión', () => {
    const n = poseNumerica(catalogo.reposo);
    expect(n[I_CIERRE_LABIOS]).toBeGreaterThanOrEqual(0.9);
    expect(n[I_COMPRESION_LABIOS]).toBe(0);
  });
  it('se abren con la mandíbula: /æ/ (muy abierta) no cierra; /θ/ (semiabierta) a medias', () => {
    expect(cierreLabial(poseDe(catalogo, 'æ')!)).toBe(0);
    const theta = cierreLabial(poseDe(catalogo, 'θ')!);
    expect(theta).toBeGreaterThan(0.3);
    expect(theta).toBeLessThan(0.9);
  });
  it('los labios con forma propia (fruncidos, estirados, labiodental) no usan el cierre', () => {
    for (const s of ['u', 'i', 'f', 'v', 'w']) expect(cierreLabial(poseDe(catalogo, s)!)).toBe(0);
  });
  it('/p b m/ cierran del todo; solo /m/ comprime menos', () => {
    for (const s of ['p', 'b', 'm']) expect(cierreLabial(poseDe(catalogo, s)!)).toBe(1);
    expect(poseNumerica(poseDe(catalogo, 'm')!)[I_COMPRESION_LABIOS]).toBe(0.35);
  });
});

describe('D4.4b v4: soplo de aspiración de las oclusivas sordas', () => {
  it('/p t k/ llevan el soplo en la liberación (1,6 s); /b d ɡ/ no', () => {
    for (const s of ['p', 't', 'k']) {
      const l = cicloSonido(poseDe(catalogo, s)!, catalogo);
      expect(l.aspiracion).toEqual([{ en: 1.6, dura: SOPLO_S }]);
    }
    for (const s of ['b', 'd', 'ɡ', 'm', 'θ', 's']) {
      expect(cicloSonido(poseDe(catalogo, s)!, catalogo).aspiracion).toBeUndefined();
    }
  });
  it('se escala con la velocidad como el resto de la línea', () => {
    const l = aVelocidad(cicloSonido(poseDe(catalogo, 'p')!, catalogo), 0.5);
    expect(l.aspiracion).toEqual([{ en: 3.2, dura: SOPLO_S * 2 }]);
  });
  it('en una palabra, cada oclusiva sorda suelta su soplo al final de su cierre', () => {
    const { segmentos } = trocearIpa('pæt', catalogo);
    const l = lineaPalabra(segmentos, catalogo);
    expect(l.aspiracion?.length).toBe(2);
    for (const a of l.aspiracion!) expect(a.en).toBeGreaterThan(0);
    const sinSordas = lineaPalabra(trocearIpa('mæn', catalogo).segmentos, catalogo);
    expect(sinSordas.aspiracion).toBeUndefined();
  });
  it('soplar(): enciende el aire oral tras la liberación y lo apaga en rampa', () => {
    const e = Object.create(EscenaBoca.prototype);
    const material = new THREE.MeshStandardMaterial({ transparent: true, opacity: 0 });
    e.aireOral = new THREE.Mesh(new THREE.BufferGeometry(), material);
    e.linea = { claves: [], total: 2.8, aspiracion: [{ en: 1.6, dura: 0.55 }] };
    e.soplar(1.5); expect(material.opacity).toBe(0);
    e.soplar(1.6); expect(material.opacity).toBeCloseTo(0.85);
    e.soplar(1.6 + 0.55 / 2); expect(material.opacity).toBeGreaterThan(0.5);
    material.opacity = 0;
    e.soplar(1.6 + 0.55); expect(material.opacity).toBe(0);
    material.dispose(); e.aireOral.geometry.dispose();
  });
});
