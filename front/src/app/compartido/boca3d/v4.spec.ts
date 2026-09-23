import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, cierreLabial, poseNumerica } from './escena';
import { SOPLO_S, VOT_MS, aVelocidad, cicloSonido, lineaPalabra, seAspira, soploDe } from './animacion';
import { AjustesPoses3d, CatalogoPoses, conAjustes3d, poseDe, trocearIpa } from './poses';
import poses from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';

const catalogo = conAjustes3d(poses as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);

describe('D4.4b v4: reposo con los labios casi juntos', () => {
  it('en reposo los labios neutros se cierran del todo, sin compresión', () => {
    const n = poseNumerica(catalogo.reposo);
    expect(n[I_CIERRE_LABIOS]).toBeGreaterThanOrEqual(0.9);
    expect(n[I_COMPRESION_LABIOS]).toBe(0);
  });
  it('se abren con la mandíbula: /æ/ (muy abierta) y /θ/ (0,6) no cierran; /ɜː/ (semiabierta) a medias', () => {
    expect(cierreLabial(poseDe(catalogo, 'æ')!)).toBe(0);
    // Cierre de cara (22 sep): /θ ð/ pasan de mandíbula 0,36 a 0,6 para que la
    // punta quepa entre los incisivos con MAND_MAX 0,21: ya no cierran a medias.
    expect(cierreLabial(poseDe(catalogo, 'θ')!)).toBe(0);
    const media = cierreLabial(poseDe(catalogo, 'ɜː')!);
    expect(media).toBeGreaterThan(0.3);
    expect(media).toBeLessThan(0.9);
  });
  it('los labios con forma propia (fruncidos, estirados, labiodental) no usan el cierre', () => {
    for (const s of ['u', 'i', 'f', 'v', 'w']) expect(cierreLabial(poseDe(catalogo, s)!)).toBe(0);
  });
  it('/p b m/ cierran del todo (con 0,4 de la shape key, calculada para el reposo); solo /m/ comprime menos', () => {
    for (const s of ['p', 'b', 'm']) {
      expect(cierreLabial(poseDe(catalogo, s)!)).toBe(1);
      expect(poseNumerica(poseDe(catalogo, s)!)[I_CIERRE_LABIOS]).toBeCloseTo(0.4);
    }
    expect(poseNumerica(poseDe(catalogo, 'm')!)[I_COMPRESION_LABIOS]).toBe(0.35);
  });
});

describe('D4.4b v4: soplo de aspiración de las oclusivas sordas', () => {
  it('/p t k/ llevan el soplo en la liberación (1,6 s); /b d ɡ/ no', () => {
    for (const s of ['p', 't', 'k']) {
      const l = cicloSonido(poseDe(catalogo, s)!, catalogo);
      expect(l.aspiracion).toEqual([{ en: 1.6, dura: soploDe(poseDe(catalogo, s)!) }]);
    }
    for (const s of ['b', 'd', 'ɡ', 'm', 'θ', 's']) {
      expect(cicloSonido(poseDe(catalogo, s)!, catalogo).aspiracion).toBeUndefined();
    }
  });
  it('se escala con la velocidad como el resto de la línea', () => {
    const l = aVelocidad(cicloSonido(poseDe(catalogo, 'p')!, catalogo), 0.5);
    expect(l.aspiracion).toEqual([{ en: 3.2, dura: soploDe(poseDe(catalogo, 'p')!) * 2 }]);
  });
  it('lote fase 3: el VOT crece hacia atrás, /p/ < /t/ < /k/ (25 / 35 / 42 ms), y /t/ conserva el soplo del 2D', () => {
    const [p, t, k] = ['p', 't', 'k'].map(s => cicloSonido(poseDe(catalogo, s)!, catalogo).aspiracion![0].dura);
    expect(p).toBeLessThan(t);
    expect(t).toBeLessThan(k);
    expect(t).toBeCloseTo(SOPLO_S);
    expect(p / t).toBeCloseTo(VOT_MS['bilabial'] / VOT_MS['alveolar']);
    expect(k / t).toBeCloseTo(VOT_MS['velar'] / VOT_MS['alveolar']);
    // En las palabras, igual y con el factor de «despacio».
    const pal = (ipa: string) => lineaPalabra(trocearIpa(ipa, catalogo).segmentos, catalogo, 2).aspiracion![0].dura;
    expect(pal('pɪn')).toBeCloseTo(soploDe(poseDe(catalogo, 'p')!) * 2);
    expect(pal('kɪn')).toBeGreaterThan(pal('tɪn'));
    expect(pal('tɪn')).toBeGreaterThan(pal('pɪn'));
  });
  it('soplo por contexto: sí en pin, play, try, kin; no tras /s/ (spin, stop, sky) ni al final (hot) ni ante consonante (act)', () => {
    const soplos = (ipa: string) => lineaPalabra(trocearIpa(ipa, catalogo).segmentos, catalogo, 1).aspiracion?.length ?? 0;
    const cuales = (ipa: string) => { const g = trocearIpa(ipa, catalogo).segmentos; return g.map((x, i) => seAspira(g, i) ? x.simbolo : '').filter(Boolean); };
    for (const ipa of ['pɪn', 'pleɪ', 'tɹaɪ', 'kɪn']) expect(soplos(ipa)).toBe(1);
    for (const ipa of ['spɪn', 'skaɪ', 'hɑt', 'bɪɡ', 'ækt']) expect(soplos(ipa)).toBe(0);
    expect(cuales('stɑp')).toEqual([]);
    expect(cuales('ˈpeɪ.pɚ')).toEqual(['p', 'p']);
    expect(cuales('ˈkæt')).toEqual(['k']);
  });
  it('lote fase 3: /ŋ/ es nasal velar sin oclusiva añadida: ni soplo ni [ɡ] en «sing»', () => {
    const ng = poseDe(catalogo, 'ŋ')!;
    expect(ng.dorso_velo).toBe(true);
    expect(ng.velo_abierto).toBe(true);
    expect(cicloSonido(ng, catalogo).aspiracion).toBeUndefined();
    // Sin suelta oclusiva: el cierre velar se deshace suave, como /m n/ (ninguna clave con `hacia`).
    expect(cicloSonido(ng, catalogo).claves.some(c => c.hacia)).toBe(false);
    const segs = trocearIpa('sɪŋ', catalogo).segmentos.map(x => x.simbolo);
    expect(segs).toEqual(['s', 'ɪ', 'ŋ']);
    // singer sin [ɡ]; finger lo trae escrito y lo enseña (app/fonemas.py, 22 sep).
    expect(trocearIpa('ˈsɪŋ.ɚ', catalogo).segmentos.map(x => x.simbolo)).not.toContain('ɡ');
    expect(trocearIpa('ˈfɪŋɡɚ', catalogo).segmentos.map(x => x.simbolo)).toContain('ɡ');
  });
  it('lote fase 3: hot RP /hɒt/ redondeada, breve y algo menos abierta que GA /hɑt/', () => {
    const o = poseDe(catalogo, 'ɒ', 'rp')!, a = poseDe(catalogo, 'ɑ')!;
    expect(o.labios).toBe('redondeados');
    expect(a.labios).toBe('neutros');
    expect(o.larga).toBe(false);
    expect(a.larga).toBe(true);
    expect(o.mandibula).toBeLessThan(a.mandibula);
    const total = (ipa: string, ac: 'ga' | 'rp') => lineaPalabra(trocearIpa(ipa, catalogo, ac).segmentos, catalogo, 1).total;
    expect(total('hɒt', 'rp')).toBeLessThan(total('hɑt', 'ga'));
  });
  it('en una palabra, la oclusiva sorda que se suelta hacia la vocal sopla al final de su cierre', () => {
    // Desde «aspiración por contexto»: la /t/ final de pat ya no sopla (antes eran 2).
    const { segmentos } = trocearIpa('pæt', catalogo);
    const l = lineaPalabra(segmentos, catalogo);
    expect(l.aspiracion?.length).toBe(1);
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
