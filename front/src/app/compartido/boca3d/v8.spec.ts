import { describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import { EscenaBoca, bermellonEscaneo } from './escena';

describe('D4.4b v8: cara neutra en el recuadro', () => {
  it('el bermellón cubre la banda medida del escaneo y nada más', () => {
    // Línea media: el rojo de la textura va de y 0,36 a −0,08 (contacto 0,15).
    for (const y of [0.33, 0.15, -0.05]) expect(bermellonEscaneo(-3.1, y, 0)).toBeGreaterThan(0.9);
    for (const y of [0.45, -0.2, 0.9]) expect(bermellonEscaneo(-3.1, y, 0)).toBe(0);
    // Detrás del frente de la cara (mejilla, cuello) y más allá de las comisuras, piel.
    expect(bermellonEscaneo(-2.3, 0.15, 0)).toBe(0);
    expect(bermellonEscaneo(-3.1, 0.15, 1.2)).toBe(0);
  });

  it('el recuadro pinta la piel lisa y la escena principal conserva su material', () => {
    const e = Object.create(EscenaBoca.prototype);
    e.escena = new THREE.Scene();
    e.camara = new THREE.PerspectiveCamera();
    e.camaraLabios = new THREE.PerspectiveCamera(22, 1.25);
    e.cabezaEntera = true; e.familiaActual = 'bilabial';
    const foto = new THREE.MeshPhysicalMaterial({ transparent: true, opacity: 0, depthWrite: false });
    const lisa = new THREE.MeshPhysicalMaterial();
    e.mejilla = new THREE.Mesh(new THREE.BufferGeometry(), foto);
    e.pielesNeutras = [{ malla: e.mejilla, neutro: lisa }];
    const vistos: [THREE.Camera, THREE.Material][] = [];
    e.renderer = {
      render: (escena: THREE.Scene, camara: THREE.Camera) => vistos.push([camara, e.mejilla.material]),
      getSize: (v: THREE.Vector2) => v.set(288, 420), getClearColor: (c: THREE.Color) => c.set('#ffffff'), getClearAlpha: () => 0,
      getPixelRatio: () => 2, setRenderTarget: vi.fn(),
      shadowMap: { autoUpdate: true }, setScissorTest: vi.fn(), setScissor: vi.fn(), setViewport: vi.fn(), setClearColor: vi.fn(), clear: vi.fn(),
    };
    e.linea = null; e.hacia = null; e.detalleCuadro = 0; e.detalleListo = false;
    e.dibujar();
    expect(vistos.find(([c]) => c === e.camara)?.[1]).toBe(foto);
    expect(vistos.find(([c]) => c === e.camaraLabios)?.[1]).toBe(lisa);
    expect(e.mejilla.material).toBe(foto);
    e.detalle.rt.dispose(); e.detalle.material.dispose(); foto.dispose(); lisa.dispose();
  });
});
