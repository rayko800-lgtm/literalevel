import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { giroPara } from './animacion';
import { EscenaBoca, LIMITES_GIRO, aplicarLimitesGiro } from './escena';
import { REPOSO } from './poses';

/** Miguel giró la cara con el dedo y vio media cabeza seccionada (auditoria/boca3d_giro_2026-09-16.md).
 *  El visor limita ahora el giro al rango donde el modelo se lee de perfil. Estas pruebas usan unos
 *  OrbitControls de verdad, porque el tope lo aplican ellos en cada update(). */
describe('límites de giro de la boca 3D', () => {
  const grados = (r: number) => (r * 180) / Math.PI;

  /** Una escena a medias: la cámara y los controles reales, sin renderer (jsdom no tiene WebGL). */
  function escena() {
    const camara = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    camara.position.set(0.3, 0.9, 10.5);                    // como el constructor
    const controles = new OrbitControls(camara, document.createElement('canvas'));
    controles.target.set(0.9, 0.05, 0);                     // tras cargar la cara (cabeza entera)
    aplicarLimitesGiro(controles);
    controles.update();
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      camara, controles, sucio: false,
      giroBase: { azimut: 0, polar: Math.PI / 2, distancia: 10 },
    });
    const azimut = () => grados(controles.getAzimuthalAngle());
    const polar = () => grados(controles.getPolarAngle());
    return { instancia, controles, azimut, polar };
  }

  it('los topes son los medidos: −34°/+20° de azimut y 75°–96° de elevación', () => {
    expect(grados(LIMITES_GIRO.azimutMin)).toBeCloseTo(-34, 6);
    expect(grados(LIMITES_GIRO.azimutMax)).toBeCloseTo(20, 6);
    expect(grados(LIMITES_GIRO.polarMin)).toBeCloseTo(75, 6);
    expect(grados(LIMITES_GIRO.polarMax)).toBeCloseTo(96, 6);
  });

  it('el perfil de partida queda dentro de los topes', () => {
    const { azimut, polar } = escena();
    expect(azimut()).toBeGreaterThan(-5);
    expect(azimut()).toBeLessThan(0);
    expect(polar()).toBeGreaterThan(80);
    expect(polar()).toBeLessThan(90);
  });

  it('girar hacia la cara se para en −34° aunque se insista', () => {
    const { instancia, azimut } = escena();
    for (let i = 0; i < 10; i++) instancia.girar(-Math.PI / 8);
    expect(azimut()).toBeCloseTo(-34, 1);
  });

  it('girar hacia la nuca se para en +20° aunque se insista', () => {
    const { instancia, azimut } = escena();
    for (let i = 0; i < 10; i++) instancia.girar(Math.PI / 8);
    expect(azimut()).toBeCloseTo(20, 1);
  });

  it('la elevación se para en 75° y 96° aunque la cámara se lleve encima o debajo de la cabeza', () => {
    const { controles, polar } = escena();
    const o = controles.target;
    controles.object.position.set(o.x + 0.1, o.y + 10, o.z + 0.1);   // casi cenital
    controles.update();
    expect(polar()).toBeCloseTo(75, 1);
    controles.object.position.set(o.x + 0.1, o.y - 10, o.z + 0.1);   // casi desde los pies
    controles.update();
    expect(polar()).toBeCloseTo(96, 1);
  });

  it('el giro automático de los labios redondeados cabe entero desde el perfil', () => {
    const { azimut } = escena();
    const giro = grados(giroPara({ ...REPOSO, labios: 'redondeados' }));
    expect(giro).toBeCloseTo(-30, 6);
    expect(azimut() + giro).toBeGreaterThanOrEqual(grados(LIMITES_GIRO.azimutMin));
  });
});
