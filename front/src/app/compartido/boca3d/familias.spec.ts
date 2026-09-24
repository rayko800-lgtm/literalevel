import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import {
  COLORES_POR_DEFECTO, EscenaBoca, I_AIRE_ORAL, LIMITES_GIRO, PRESETS_FAMILIA, materialDe, poseNumerica,
} from './escena';
import { AjustesPoses3d, CatalogoPoses, Familia, PoseSonido, REPOSO, conAjustes3d, familiaDe, poseDe } from './poses';
import posesCompletas from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';

const CATALOGO = conAjustes3d(posesCompletas as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
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

  it('/m/ tiene preset nasal-bilabial; /p b/ conservan el bilabial exterior', () => {
    expect(familiaDe(poseReal('m'))).toBe('nasal-bilabial');
    expect(familiaDe(poseReal('p'))).toBe('bilabial');
    expect(familiaDe(poseReal('b'))).toBe('bilabial');
  });

  it('róticos (punta retrofleja) aunque compartan lugar con postalveolares', () => {
    expect(familiaDe(pose({ lugar: 'postalveolar', punta: 'retrofleja' }))).toBe('rotico');
    // Lote fase 1: la rótica abombada (punta en reposo) va por el campo `rotica`.
    expect(familiaDe(pose({ lugar: 'postalveolar', punta: 'reposo', rotica: true }))).toBe('rotico');
    expect(familiaDe(pose({ lugar: '', punta: 'reposo', rotica: true, movimiento: 'vocal' }))).toBe('rotico');
    expect(familiaDe(pose({ lugar: '', punta: 'reposo', movimiento: 'vocal' }))).toBe('vocal');
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

describe('PRESETS_FAMILIA: corte principal dentro de los topes verificados', () => {
  const FAMILIAS: Familia[] = [
    'bilabial', 'nasal-bilabial', 'labiodental', 'dental', 'alveolar', 'postalveolar', 'rotico', 'velar', 'vocal',
  ];

  it('las nueve familias tienen preset', () => {
    expect(Object.keys(PRESETS_FAMILIA).sort()).toEqual([...FAMILIAS].sort());
  });

  for (const familia of FAMILIAS) {
    it(`${familia}: rango y azimut inicial dentro de los topes ya verificados`, () => {
      const p = PRESETS_FAMILIA[familia];
      const bilabial = familia === 'bilabial' || familia === 'nasal-bilabial';
      expect(p.limites.azimutMin).toBeGreaterThanOrEqual(LIMITES_GIRO.azimutMin);
      if (bilabial) expect(Math.abs(p.azimut)).toBeLessThan(10 * Math.PI / 180);
      expect(p.limites.azimutMax).toBeLessThanOrEqual(LIMITES_GIRO.azimutMax);
      expect(p.limites.polarMin).toBeGreaterThanOrEqual(LIMITES_GIRO.polarMin);
      expect(p.limites.polarMax).toBeLessThanOrEqual(LIMITES_GIRO.polarMax);
      expect(p.azimut).toBeGreaterThanOrEqual(p.limites.azimutMin);
      expect(p.azimut).toBeLessThanOrEqual(p.limites.azimutMax);
      expect(p.zoom).toBeGreaterThan(0);
      expect(p.zoom).toBeLessThanOrEqual(1);
    });
  }

  it('las bilabiales muestran ambas mitades de los labios; labiodentales esconden la mejilla', () => {
    expect(PRESETS_FAMILIA.bilabial.mejilla).toBe(true);
    expect(PRESETS_FAMILIA.labiodental.mejilla).toBe(false);
    for (const familia of FAMILIAS.filter(f => f !== 'bilabial' && f !== 'labiodental')) {
      expect(PRESETS_FAMILIA[familia].mejilla).toBe(true);
    }
  });

  it('el preset de /m/ abre el encuadre y conserva la anatomía interna', () => {
    expect(PRESETS_FAMILIA['nasal-bilabial'].zoom).toBeGreaterThanOrEqual(PRESETS_FAMILIA.bilabial.zoom);
    expect(PRESETS_FAMILIA['nasal-bilabial'].exterior).toBe('ninguna');
    expect(PRESETS_FAMILIA['nasal-bilabial'].target![0]).toBeGreaterThanOrEqual(PRESETS_FAMILIA.bilabial.target![0]);
  });

  it('cada familia de D4.4a declara su perfil dental semántico', () => {
    expect(PRESETS_FAMILIA.bilabial.dentadura).toBe('contexto-nasal');
    expect(PRESETS_FAMILIA['nasal-bilabial'].dentadura).toBe('contexto-nasal');
    expect(PRESETS_FAMILIA.labiodental.dentadura).toBe('incisivos-superiores');
    expect(PRESETS_FAMILIA.dental.dentadura).toBe('incisivos-relevantes');
    expect(PRESETS_FAMILIA.alveolar.dentadura).toBe('referencia-alveolar');
    expect(PRESETS_FAMILIA.postalveolar.dentadura).toBe('subordinada');
    expect(PRESETS_FAMILIA.velar.dentadura).toBe('sin-anteriores');
  });
});

describe('D4.4a: material de lengua', () => {
  it('la lengua es más mate y cromáticamente distinta de la encía', () => {
    const lengua = materialDe('lengua', COLORES_POR_DEFECTO.lengua);
    const encia = materialDe('encia', COLORES_POR_DEFECTO.encia);
    expect(lengua.roughness).toBeGreaterThan(encia.roughness);
    expect(lengua.clearcoat).toBeLessThan(encia.clearcoat);
    const distancia = Math.hypot(lengua.color.r - encia.color.r, lengua.color.g - encia.color.g, lengua.color.b - encia.color.b);
    expect(distancia).toBeGreaterThan(0.12);
    lengua.dispose(); encia.dispose();
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
    const mejilla = { visible: true, material: { opacity: 0.14 } };
    // D4.3c: vistaParaFamilia() ya llama a vistaExterior(), que toca lengua/
    // velo/las listas de piezas internas -- objetos/arrays de mentira, sin
    // WebGL de verdad.
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      camara, controles, mejilla, sucio: false,
      cabezaEntera: false, caraModelada: false,
      zoomActual: 1, targetFamilia: null, familiaActual: 'vocal', mejillaExterna: true, mejillaFamilia: true,
      giroBase: { azimut: 0, polar: 1.49, distancia: 13 },
      lengua: { visible: true }, lenguaGlb: null, velo: { visible: true },
      piezasCorte: [], piezasDentalesInferiores: [], piezasDentalesSuperiores: [],
      dentalSimple: [], dentalesModelados: false,
    }) as EscenaBoca;
    return { instancia, camara, controles, mejilla };
  }

  it('bilabial: encuadra el interior completo para acompañar al detalle labial', () => {
    const { instancia, camara, controles, mejilla } = escena();
    const antes = camara.position.distanceTo(controles.target);
    instancia.vistaParaFamilia('bilabial');
    const despues = camara.position.distanceTo(controles.target);
    expect(despues).toBeCloseTo(13 * PRESETS_FAMILIA.bilabial.zoom, 6);
    expect(mejilla.visible).toBe(true);
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

  it('restablecerVista() vuelve a la familia activa (azimut, zoom, target y límites), no a un azimut universal', () => {
    const { instancia, controles } = escena();
    instancia.vistaParaFamilia('bilabial');
    controles.getAzimuthalAngle();                       // fuerza a leer el estado tras vistaParaFamilia
    instancia.girar(0.3);                                 // el usuario explora
    instancia.restablecerVista();
    expect(controles.minAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMin, 6);
    expect(controles.maxAzimuthAngle).toBeCloseTo(PRESETS_FAMILIA.bilabial.limites.azimutMax, 6);
    expect(controles.target.x).toBeCloseTo(PRESETS_FAMILIA.bilabial.target![0], 6);
    expect(controles.target.y).toBeCloseTo(PRESETS_FAMILIA.bilabial.target![1], 6);
    expect(instancia.diagnostico.zoom).toBeCloseTo(PRESETS_FAMILIA.bilabial.zoom, 6);
  });

  it('Restaurar consume la inercia de un arrastre antes de colocar la cámara', () => {
    const { instancia, controles } = escena();
    controles.enableDamping = true;
    controles.dampingFactor = 0.12;
    instancia.vistaParaFamilia('nasal-bilabial');
    controles.rotateLeft(0.6);
    instancia.restablecerVista();
    for (let i = 0; i < 12; i++) controles.update();
    expect(controles.getAzimuthalAngle()).toBeCloseTo(PRESETS_FAMILIA['nasal-bilabial'].azimut, 8);
    expect(controles.enableDamping).toBe(true);
    controles.dispose();
  });

  it('diagnostico refleja la familia, el zoom y el target activos (D4.2.1, panel de depuración)', () => {
    const { instancia } = escena();
    instancia.vistaParaFamilia('velar');
    const d = instancia.diagnostico;
    expect(d.familia).toBe('velar');
    expect(d.zoom).toBeCloseTo(PRESETS_FAMILIA.velar.zoom, 6);
    expect(d.target.x).toBeCloseTo(PRESETS_FAMILIA.velar.target![0], 6);
    expect(d.target.y).toBeCloseTo(PRESETS_FAMILIA.velar.target![1], 6);
  });

  for (const familia of ['bilabial', 'nasal-bilabial', 'labiodental', 'dental', 'alveolar', 'postalveolar', 'rotico', 'velar'] as Familia[]) {
    it(`${familia}: el target de la cámara es el del preset, no el punto universal (0,9/0,1)`, () => {
      const { instancia, controles } = escena();
      instancia.vistaParaFamilia(familia);
      const [tx, ty] = PRESETS_FAMILIA[familia].target!;
      expect(controles.target.x).toBeCloseTo(tx, 6);
      expect(controles.target.y).toBeCloseTo(ty, 6);
    });
  }

  it('vocal: sin target propio, usa el punto universal de siempre', () => {
    const { instancia, controles } = escena();
    expect(PRESETS_FAMILIA.vocal.target).toBeNull();
    instancia.vistaParaFamilia('vocal');
    expect(controles.target.x).toBeCloseTo(0.1, 6);        // sin cabezaEntera/caraModelada en esta escena de mentira
  });
});

describe('EscenaBoca: modo guiado y explorar', () => {
  it('la guarda conserva ambas mitades de los labios bilabiales al bajar calidad', () => {
    for (const familia of ['bilabial', 'nasal-bilabial', 'alveolar']) {
      const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
        familiaActual: familia, mejilla: { visible: true },
        guarda: { midiendo: true, t0: performance.now() - 3000, cuadros: 1, etapa: 2 },
      });
      instancia.medirGuarda();
      expect(instancia.mejilla.visible).toBe(familia !== 'alveolar');
    }
  });
  it('solo Explorar habilita rotación y zoom; el pan se mantiene bloqueado', () => {
    const controles = { enableRotate: true, enableZoom: true, enablePan: true, update: vi.fn() };
    const canvas = document.createElement('canvas');
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      controles, canvas, libre: true, sucio: false,
    }) as EscenaBoca;
    instancia.girarLibre(false);
    expect(controles.enableRotate).toBe(false);
    expect(controles.enableZoom).toBe(false);
    expect(controles.enablePan).toBe(false);
    expect(canvas.style.touchAction).toBe('pan-y');
    instancia.girarLibre(true);
    expect(controles.enableRotate).toBe(true);
    expect(controles.enableZoom).toBe(true);
    expect(controles.enablePan).toBe(false);
    expect(canvas.style.touchAction).toBe('none');
  });
});

/** D4.4a: perfiles dentales de runtime, por familia y sin tocar el GLB. */
describe('EscenaBoca.vistaParaFamilia: perfiles dentales', () => {
  function escenaConPiezas() {
    const camara = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    const controles = new OrbitControls(camara, document.createElement('canvas'));
    const pieza = (grupo?: string, indice = -1, z = 0) => ({
      visible: true, position: { z }, userData: grupo ? { grupoDental: grupo, indiceDental: indice } : {},
    });
    const corte1 = pieza(), corte2 = pieza();
    const soporteSup = pieza('soporte-superior');
    const soporteInf = pieza('soporte-inferior');
    const incisivosSup = [pieza('incisivo-superior', 4), pieza('incisivo-superior', 5)];
    const incisivosInf = [pieza('incisivo-inferior', 5), pieza('incisivo-inferior', 7)];
    const posterioresSup = [pieza('posterior-superior', 2, 1), pieza('posterior-superior', 9, -1)];
    const posterioresInf = [pieza('posterior-inferior', 2, 1), pieza('posterior-inferior', 9, -1)];
    const dientesInf = [soporteInf, ...incisivosInf, ...posterioresInf];
    const dientesSup = [soporteSup, ...incisivosSup, ...posterioresSup];
    const lengua = pieza(), velo = pieza();
    const mejilla = { visible: true, material: { opacity: 0.14 } };
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      camara, controles, mejilla, sucio: false, cabezaEntera: false, caraModelada: false,
      zoomActual: 1, targetFamilia: null, familiaActual: 'vocal', mejillaExterna: true, mejillaFamilia: true,
      giroBase: { azimut: 0, polar: 1.49, distancia: 13 },
      lengua, lenguaGlb: null, velo,
      piezasCorte: [corte1, corte2],
      piezasDentalesInferiores: dientesInf,
      piezasDentalesSuperiores: dientesSup,
      dientesLaterales: [...posterioresInf, ...posterioresSup],
      lateralesOcultos: 'ninguno', perfilDentalActual: 'completa',
      dentalSimple: [], dentalesModelados: true,
    }) as EscenaBoca;
    return {
      instancia, lengua, velo, corte: [corte1, corte2], soporteSup, soporteInf,
      incisivosSup, incisivosInf, posterioresSup, posterioresInf, dientesInf, dientesSup,
    };
  }

  // Las caras del corte (corte_craneo/nariz/maxilar/mandibula, pared del
  // fondo) NO se esconden: cierran la cavidad, y esconderlas dejaba huecos
  // reales en la cabeza (visto en el navegador tras el primer intento).
  // Solo dientes/lengua/velo, piezas sueltas dentro de la cavidad.

  it('bilabial: mantiene el interior en el corte principal y subordina los dientes', () => {
    const { instancia, lengua, velo, corte, dientesInf, soporteSup, incisivosSup, posterioresSup } = escenaConPiezas();
    instancia.vistaParaFamilia('bilabial');
    expect(lengua.visible).toBe(true);
    expect(velo.visible).toBe(true);
    expect(corte.every(o => o.visible)).toBe(true);
    expect(dientesInf.every(o => !o.visible)).toBe(true);
    expect(soporteSup.visible).toBe(true);
    expect([...incisivosSup, ...posterioresSup].every(o => !o.visible)).toBe(true);
  });

  it('labiodental: deja soporte e incisivos superiores, no la hilera completa ni el arco inferior', () => {
    const { instancia, lengua, velo, corte, soporteSup, incisivosSup, posterioresSup, dientesInf } = escenaConPiezas();
    instancia.vistaParaFamilia('labiodental');
    expect(lengua.visible).toBe(false);
    expect(velo.visible).toBe(false);
    expect(corte.every(o => o.visible)).toBe(true);
    expect(dientesInf.every(o => !o.visible)).toBe(true);
    expect(soporteSup.visible).toBe(true);
    expect(incisivosSup.every(o => o.visible)).toBe(true);
    expect(posterioresSup.every(o => !o.visible)).toBe(true);
  });

  it('nasal-bilabial (/m/): conserva lengua, velo y techo; la dentadura no compite', () => {
    const { instancia, lengua, velo, soporteSup, dientesInf, incisivosSup, posterioresSup } = escenaConPiezas();
    instancia.vistaParaFamilia('nasal-bilabial');
    expect(lengua.visible).toBe(true);
    expect(velo.visible).toBe(true);
    expect(soporteSup.visible).toBe(true);
    expect(dientesInf.every(o => !o.visible)).toBe(true);
    expect([...incisivosSup, ...posterioresSup].every(o => !o.visible)).toBe(true);
  });

  it('dental: conserva incisivos superiores y solo los inferiores centrales; posteriores fuera', () => {
    const { instancia, incisivosSup, incisivosInf, posterioresSup, posterioresInf } = escenaConPiezas();
    instancia.vistaParaFamilia('dental');
    expect(incisivosSup.every(o => o.visible)).toBe(true);
    expect(incisivosInf[0].visible).toBe(true);   // índice 5: central
    expect(incisivosInf[1].visible).toBe(false);  // índice 7: lateral que tapa la punta
    expect([...posterioresSup, ...posterioresInf].every(o => !o.visible)).toBe(true);
  });

  it('alveolar: soporte superior y referencia central mínima; sin arco inferior ni posteriores', () => {
    const { instancia, lengua, velo, corte, soporteSup, incisivosSup, dientesInf, posterioresSup } = escenaConPiezas();
    instancia.vistaParaFamilia('alveolar');
    expect(lengua.visible).toBe(true);
    expect(velo.visible).toBe(true);
    expect(corte.every(o => o.visible)).toBe(true);
    expect(soporteSup.visible).toBe(true);
    expect(incisivosSup[0].visible).toBe(false);  // índice 4
    expect(incisivosSup[1].visible).toBe(true);   // índice 5
    expect(dientesInf.every(o => !o.visible)).toBe(true);
    expect(posterioresSup.every(o => !o.visible)).toBe(true);
  });

  it.each(['postalveolar', 'velar'] as const)('%s: lengua/velo dominan y solo queda el soporte superior', familia => {
    const { instancia, lengua, velo, soporteSup, dientesInf, incisivosSup, posterioresSup } = escenaConPiezas();
    instancia.vistaParaFamilia(familia);
    expect(lengua.visible).toBe(true);
    expect(velo.visible).toBe(true);
    expect(soporteSup.visible).toBe(true);
    expect([...dientesInf, ...incisivosSup, ...posterioresSup].every(o => !o.visible)).toBe(true);
  });

  it('cambiar a una familia completa restaura todas las piezas ocultadas', () => {
    const { instancia, lengua, dientesInf, dientesSup } = escenaConPiezas();
    instancia.vistaParaFamilia('bilabial');
    expect(lengua.visible).toBe(true);
    instancia.vistaParaFamilia('vocal');
    expect(lengua.visible).toBe(true);
    expect(dientesInf.every(o => o.visible)).toBe(true);
    expect(dientesSup.every(o => o.visible)).toBe(true);
  });

  it('restaurar el mismo preset recalcula los molares laterales y no los deja reaparecer por la caché', () => {
    const { instancia, dientesInf, dientesSup } = escenaConPiezas();
    instancia.vistaParaFamilia('dental');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (instancia as any).ocultarLaterales();
    const primera = [...dientesInf, ...dientesSup].map(o => o.visible);
    instancia.vistaParaFamilia('dental');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (instancia as any).ocultarLaterales();
    expect([...dientesInf, ...dientesSup].map(o => o.visible)).toEqual(primera);
  });
});

/** D4.2.1 (Miguel, 18 sep): el bug de zoom -- `cargarCara()` recolocaba la
 *  cámara con `distanciaEncuadre()` a secas al terminar de cargar `cara.glb`,
 *  sin `zoomActual`, a diferencia de `redimensionar()` -- se corrigió
 *  extrayendo la misma lógica a `recentrarConservandoAngulo()`, que ahora
 *  usan los dos sitios. Aquí se prueba esa lógica sola, sin depender de
 *  cargar un GLB de verdad. */
describe('EscenaBoca.recentrarConservandoAngulo: no pierde el zoom ni el target al cargar cara.glb', () => {
  function escenaConPreset(familia: Familia, zoom: number, target: readonly [number, number] | null) {
    const camara = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    const controles = new OrbitControls(camara, document.createElement('canvas'));
    const mejilla = { visible: true };
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      camara, controles, mejilla, sucio: false,
      cabezaEntera: false, caraModelada: false,       // como antes de que cara.glb termine de cargar
      zoomActual: zoom, targetFamilia: target, familiaActual: familia,
      mejillaExterna: true, mejillaFamilia: true,
      giroBase: { azimut: 0, polar: 1.49, distancia: 13 },
    }) as unknown as { recentrarConservandoAngulo(): void; diagnostico: EscenaBoca['diagnostico'] };
    // Coloca la cámara como si `vistaParaFamilia` ya hubiera puesto el
    // preset (mismo cálculo que `vista()`, sin llamarlo para no depender
    // de él en esta prueba).
    const o = target ? { x: target[0], y: target[1] } : { x: 0.1, y: 0.05 };
    controles.target.set(o.x, o.y, 0);
    const distancia = 13 * zoom;                        // distanciaEncuadre() sin cabezaEntera/caraModelada
    camara.position.set(o.x + distancia * Math.sin(1.49) * Math.sin(-30 * Math.PI / 180),
      o.y + distancia * Math.cos(1.49), distancia * Math.sin(1.49) * Math.cos(-30 * Math.PI / 180));
    controles.update();
    return { instancia, camara, controles };
  }

  it('al activarse caraModelada (cara.glb recién cargado), conserva el zoom del preset, no lo pierde', () => {
    const { instancia, camara, controles } = escenaConPreset('bilabial', 0.5, [-2.75, 0.15]);
    const distanciaAntes = camara.position.distanceTo(controles.target);
    (instancia as unknown as { caraModelada: boolean }).caraModelada = true;   // simula que cara.glb acaba de cargar
    instancia.recentrarConservandoAngulo();
    const distanciaDespues = camara.position.distanceTo(controles.target);
    // Antes del fix: distanciaDespues habria sido distanciaEncuadre() SIN
    // zoom (17,5, mucho mayor). Con el fix, sigue habiendo zoom.
    expect(distanciaDespues).toBeCloseTo(17.5 * 0.5, 1);
    expect(distanciaDespues).toBeLessThan(17.5 * 0.9);
  });

  it('al activarse caraModelada, conserva el target de la familia (no lo pisa con 0,9 universal)', () => {
    const { instancia, controles } = escenaConPreset('bilabial', 0.5, [-2.75, 0.15]);
    (instancia as unknown as { caraModelada: boolean }).caraModelada = true;
    instancia.recentrarConservandoAngulo();
    expect(controles.target.x).toBeCloseTo(-2.75, 6);
    expect(controles.target.y).toBeCloseTo(0.15, 6);
  });

  it('familia vocal (sin target propio): al activarse caraModelada SÍ pasa al punto universal 0,9, como siempre', () => {
    const { instancia, controles } = escenaConPreset('vocal', 1, null);
    (instancia as unknown as { caraModelada: boolean }).caraModelada = true;
    instancia.recentrarConservandoAngulo();
    expect(controles.target.x).toBeCloseTo(0.9, 6);
  });

  it('conserva el ángulo de vista (azimut) al recentrar, no vuelve a un azimut de perfil', () => {
    const { instancia, camara, controles } = escenaConPreset('bilabial', 0.5, [-2.75, 0.15]);
    const azimutAntes = Math.atan2(camara.position.x - controles.target.x, camara.position.z - controles.target.z);
    (instancia as unknown as { caraModelada: boolean }).caraModelada = true;
    instancia.recentrarConservandoAngulo();
    const azimutDespues = Math.atan2(camara.position.x - controles.target.x, camara.position.z - controles.target.z);
    expect(azimutDespues).toBeCloseTo(azimutAntes, 6);
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

/** D4.3b (Miguel, 18 sep): el 3D reutiliza el significado del aire y la
 *  vibración del 2D -- continuo en fricativas y en /h/, señal de
 *  sonoridad aparte del aire, nunca lo mismo. */
describe('poseNumerica: aire oral y sonoridad (D4.3b)', () => {
  // I_SONORA tampoco se exporta; su posición sí está documentada en
  // escena.ts, tres después de I_CONTACTO (x, y, activo).
  const I_SONORA = I_CONTACTO + 3;

  it('fricativas sordas y sonoras: aire oral activo por igual', () => {
    for (const s of ['θ', 'ð', 'f', 'v', 's', 'z']) {
      expect(poseNumerica(poseReal(s))[I_AIRE_ORAL]).toBe(1);
    }
  });

  it('/h/ (glotal): aire oral activo, igual que las fricativas', () => {
    expect(poseNumerica(poseReal('h'))[I_AIRE_ORAL]).toBe(1);
  });

  it('oclusivas, nasales y vocales: sin aire oral continuo (no son fricativas)', () => {
    for (const s of ['p', 't', 'k', 'm', 'n', 'i']) {
      expect(poseNumerica(poseReal(s))[I_AIRE_ORAL]).toBe(0);
    }
  });

  it('sonoridad: /v z ð/ (sonoras) marcan 1; /f s θ/ (sordas) marcan 0', () => {
    for (const s of ['v', 'z', 'ð']) expect(poseNumerica(poseReal(s))[I_SONORA]).toBe(1);
    for (const s of ['f', 's', 'θ']) expect(poseNumerica(poseReal(s))[I_SONORA]).toBe(0);
  });

  it('aire y sonoridad son independientes: /f/ tiene aire sin sonoridad, /v/ tiene las dos', () => {
    const f = poseNumerica(poseReal('f')), v = poseNumerica(poseReal('v'));
    expect(f[I_AIRE_ORAL]).toBe(1);
    expect(f[I_SONORA]).toBe(0);
    expect(v[I_AIRE_ORAL]).toBe(1);
    expect(v[I_SONORA]).toBe(1);
  });
});

describe('EscenaBoca.aplicar: el pulso de vibración sigue la pose activa (D4.3b)', () => {
  // Una escena mínima con solo lo que `aplicar()` toca para I_SONORA/marcaVibracion:
  // el resto de piezas, como objetos vacíos que aceptan cualquier propiedad.
  function escenaMinima() {
    const pieza = () => ({ position: { set: () => {} }, rotation: { z: 0 }, geometry: { dispose: () => {} },
      material: { opacity: 0 }, userData: {}, visible: true, scale: { set: () => {} } });
    const marcaVibracion = pieza();
    const marcaContacto = pieza();
    const aireNasal = pieza(), aireOral = pieza();
    const labioSup = pieza(), labioInf = pieza();
    // deformarLengua necesita una BufferGeometry real, con el numero exacto
    // de vertices que espera (MUESTRAS+1)*LADOS+2 = 57*16+2 (ver escena.ts).
    const geometriaLengua = new THREE.BufferGeometry();
    geometriaLengua.setAttribute('position', new THREE.BufferAttribute(new Float32Array(914 * 3), 3));
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      marcaVibracion, marcaContacto, aireNasal, aireOral, labioSup, labioInf,
      mandibula: { rotation: { z: 0 } }, velo: { rotation: { z: 0 } },
      pielesDeformables: [], pielesConLabios: [], lenguaGlb: null,
      lengua: { geometry: geometriaLengua, visible: true }, sucio: false, sonoroActivo: false,
    }) as unknown as { aplicar(n: Float64Array): void; sonoroActivo: boolean; marcaVibracion: ReturnType<typeof pieza> };
    return instancia;
  }

  it('pose sonora: sonoroActivo pasa a true (bucle() la hará pulsar)', () => {
    const instancia = escenaMinima();
    const n = poseNumerica(poseReal('v'));
    instancia.aplicar(n);
    expect(instancia.sonoroActivo).toBe(true);
  });

  it('pose sorda: sonoroActivo pasa a false y la vibración se apaga de inmediato', () => {
    const instancia = escenaMinima();
    const n = poseNumerica(poseReal('f'));
    instancia.aplicar(n);
    expect(instancia.sonoroActivo).toBe(false);
    expect(instancia.marcaVibracion.material.opacity).toBe(0);
    expect(instancia.marcaVibracion.visible).toBe(false);
  });
});
