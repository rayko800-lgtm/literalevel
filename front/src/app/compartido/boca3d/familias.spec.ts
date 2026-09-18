import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EscenaBoca, I_AIRE_ORAL, LIMITES_GIRO, PRESETS_FAMILIA, poseNumerica } from './escena';
import { CatalogoPoses, Familia, PoseSonido, REPOSO, familiaDe, poseDe } from './poses';
import posesCompletas from './poses.ejemplo.json';

const CATALOGO = posesCompletas as unknown as CatalogoPoses;
const poseReal = (simbolo: string) => poseDe(CATALOGO, simbolo, 'ga')!;
// I_CONTACTO no se exporta (es un detalle interno de escena.ts), pero su
// posición sí está documentada: justo después de I_AIRE_ORAL (ver escena.ts).
const I_CONTACTO = I_AIRE_ORAL + 1;

/** D4.2 (Miguel, 18 sep): una vista inicial por familia, no por fonema, y
 *  ningún preset gira más lejos de lo que `LIMITES_GIRO` ya tiene verificado
 *  sin revelar los planos de corte de la media cabeza. */
describe('familiaDe: agrupar por articulador protagonista', () => {
  // Las consonantes reales nunca tienen `movimiento: 'vocal'|'diptongo'` (ver
  // PARAMETROS del 2D): el helper lo fija a 'oclusiva' para que la prueba
  // refleje datos reales y no dispare el caso de vocal por defecto de REPOSO.
  const pose = (extra: Partial<PoseSonido>): PoseSonido => ({ ...REPOSO, movimiento: 'oclusiva', ...extra });

  it('bilabiales, labiodentales, dentales, alveolares, postalveolares y velares por su lugar', () => {
    expect(familiaDe(pose({ lugar: 'bilabial' }))).toBe('bilabial');
    expect(familiaDe(pose({ lugar: 'labiodental' }))).toBe('labiodental');
    expect(familiaDe(pose({ lugar: 'interdental' }))).toBe('dental');
    expect(familiaDe(pose({ lugar: 'alveolar' }))).toBe('alveolar');
    expect(familiaDe(pose({ lugar: 'postalveolar' }))).toBe('postalveolar');
    expect(familiaDe(pose({ lugar: 'velar' }))).toBe('velar');
  });

  it('róticos (punta retrofleja) aunque compartan lugar con postalveolares', () => {
    expect(familiaDe(pose({ lugar: 'postalveolar', punta: 'retrofleja' }))).toBe('rotico');
  });

  it('vocales y diptongos, aunque tengan lugar vacío', () => {
    expect(familiaDe(pose({ movimiento: 'vocal', lugar: '' }))).toBe('vocal');
    expect(familiaDe(pose({ movimiento: 'diptongo', lugar: '' }))).toBe('vocal');
  });

  it('/h/ (glotal) y el reposo, sin articulador protagonista, caen en vocal', () => {
    expect(familiaDe(pose({ movimiento: 'fricativa', lugar: 'glotal' }))).toBe('vocal');
    expect(familiaDe(REPOSO)).toBe('vocal');
  });
});

describe('PRESETS_FAMILIA: cada preset es un subconjunto seguro de LIMITES_GIRO', () => {
  const FAMILIAS: Familia[] = [
    'bilabial', 'labiodental', 'dental', 'alveolar', 'postalveolar', 'rotico', 'velar', 'vocal',
  ];

  it('las ocho familias tienen preset', () => {
    expect(Object.keys(PRESETS_FAMILIA).sort()).toEqual([...FAMILIAS].sort());
  });

  for (const familia of FAMILIAS) {
    it(`${familia}: rango y azimut inicial dentro de los topes ya verificados`, () => {
      const p = PRESETS_FAMILIA[familia];
      expect(p.limites.azimutMin).toBeGreaterThanOrEqual(LIMITES_GIRO.azimutMin);
      expect(p.limites.azimutMax).toBeLessThanOrEqual(LIMITES_GIRO.azimutMax);
      expect(p.limites.polarMin).toBeGreaterThanOrEqual(LIMITES_GIRO.polarMin);
      expect(p.limites.polarMax).toBeLessThanOrEqual(LIMITES_GIRO.polarMax);
      expect(p.azimut).toBeGreaterThanOrEqual(p.limites.azimutMin);
      expect(p.azimut).toBeLessThanOrEqual(p.limites.azimutMax);
      expect(p.zoom).toBeGreaterThan(0);
      expect(p.zoom).toBeLessThanOrEqual(1);
    });
  }

  it('bilabiales y labiodentales esconden la mejilla; el resto la deja', () => {
    expect(PRESETS_FAMILIA.bilabial.mejilla).toBe(false);
    expect(PRESETS_FAMILIA.labiodental.mejilla).toBe(false);
    for (const familia of FAMILIAS.filter(f => f !== 'bilabial' && f !== 'labiodental')) {
      expect(PRESETS_FAMILIA[familia].mejilla).toBe(true);
    }
  });
});

describe('EscenaBoca.vistaParaFamilia: cámara, límites y mejilla', () => {
  /** Una escena a medias: cámara y controles reales (OrbitControls solo
   *  necesita el DOM, no WebGL), sin renderer, como en limites-giro.spec.ts. */
  function escena() {
    const camara = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    camara.position.set(0.3, 0.9, 10.5);
    const controles = new OrbitControls(camara, document.createElement('canvas'));
    controles.target.set(0.1, 0.05, 0);
    controles.update();
    const mejilla = { visible: true };
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      camara, controles, mejilla, sucio: false,
      cabezaEntera: false, caraModelada: false,
      zoomActual: 1, familiaActual: 'vocal', mejillaExterna: true, mejillaFamilia: true,
      giroBase: { azimut: 0, polar: 1.49, distancia: 13 },
    }) as EscenaBoca;
    return { instancia, camara, controles, mejilla };
  }

  it('bilabial: acerca la cámara (zoom < 1) y esconde la mejilla', () => {
    const { instancia, camara, controles, mejilla } = escena();
    const antes = camara.position.distanceTo(controles.target);
    instancia.vistaParaFamilia('bilabial');
    const despues = camara.position.distanceTo(controles.target);
    expect(despues).toBeLessThan(antes);
    expect(mejilla.visible).toBe(false);
    expect(controles.minAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMin, 6);
    expect(controles.maxAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMax, 6);
  });

  it('velar: mantiene la mejilla y usa el rango de giro velar, no el de bilabial', () => {
    const { instancia, mejilla, controles } = escena();
    instancia.vistaParaFamilia('velar');
    expect(mejilla.visible).toBe(true);
    expect(controles.minAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.velar.limites.azimutMin, 6);
    expect(controles.maxAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.velar.limites.azimutMax, 6);
  });

  it('la mejilla externa (rendimiento) manda aunque el preset la permita', () => {
    const { instancia, mejilla } = escena();
    instancia.mostrarMejilla(false);
    instancia.vistaParaFamilia('alveolar');            // preset permite mejilla=true
    expect(mejilla.visible).toBe(false);                // pero el input del componente la apagó
  });

  it('restablecerVista() vuelve a la familia activa, no a un azimut universal', () => {
    const { instancia, controles } = escena();
    instancia.vistaParaFamilia('bilabial');
    controles.getAzimuthalAngle();                       // fuerza a leer el estado tras vistaParaFamilia
    instancia.girar(0.3);                                 // el usuario explora
    instancia.restablecerVista();
    expect(controles.minAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMin, 6);
    expect(controles.maxAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMax, 6);
  });
});

/** D4.2, casos de aceptación obligatorios (Miguel, 18 sep): /b/ labios, /θ/
 *  punta+dientes, /t/ punta/lámina+alvéolo, /k/ dorso+velo. Con las poses
 *  reales del catálogo (no sintéticas), la familia y el marcador de contacto
 *  deben señalar justo ese articulador. */
describe('D4.2, casos de aceptación: /b/ /θ/ /t/ /k/', () => {
  it('/b/: familia bilabial, con contacto real (labios cerrados)', () => {
    const p = poseReal('b');
    expect(familiaDe(p)).toBe('bilabial');
    const n = poseNumerica(p);
    expect(n[I_CONTACTO + 2]).toBe(1);
  });

  it('/θ/: familia dental, con contacto en la punta (interdental)', () => {
    const p = poseReal('θ');
    expect(familiaDe(p)).toBe('dental');
    const n = poseNumerica(p);
    expect(n[I_CONTACTO + 2]).toBe(1);
  });

  it('/t/: familia alveolar, con contacto en la punta/lámina', () => {
    const p = poseReal('t');
    expect(familiaDe(p)).toBe('alveolar');
    expect(p.punta_toca).toBe(true);
    const n = poseNumerica(p);
    expect(n[I_CONTACTO + 2]).toBe(1);
  });

  it('/k/: familia velar, con contacto del dorso contra el velo', () => {
    const p = poseReal('k');
    expect(familiaDe(p)).toBe('velar');
    expect(p.dorso_velo).toBe(true);
    const n = poseNumerica(p);
    expect(n[I_CONTACTO + 2]).toBe(1);
  });

  it('una vocal no marca contacto: no hay articulador que toque otro', () => {
    const n = poseNumerica(poseReal('i'));
    expect(n[I_CONTACTO + 2]).toBe(0);
  });
});
