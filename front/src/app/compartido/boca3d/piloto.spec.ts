import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, poseNumerica } from './escena';
import { aVelocidad, cicloSonido } from './animacion';
import { CatalogoPoses, poseDe } from './poses';
import poses from './poses.ejemplo.json';
import * as THREE from 'three';

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

describe('D4.4b v3: detalle frontal sincronizado', () => {
  for (const familia of ['bilabial', 'nasal-bilabial']) {
    it(`${familia}: dibuja el mismo estado y restaura la transparencia del corte`, () => {
      const e = Object.create(EscenaBoca.prototype);
      e.escena = new THREE.Scene();
      e.camara = new THREE.PerspectiveCamera();
      e.camaraLabios = new THREE.PerspectiveCamera();
      e.cabezaEntera = true; e.familiaActual = familia;
      const material = new THREE.MeshPhysicalMaterial({transparent:true, opacity:0, depthWrite:false});
      e.mejilla = new THREE.Mesh(new THREE.BufferGeometry(), material);
      e.mejilla.visible = false;
      const cuadros: unknown[] = [];
      e.renderer = {
        render: (escena: THREE.Scene, camara: THREE.Camera) => cuadros.push([escena, camara, e.mejilla.visible, material.opacity, material.depthWrite]),
        getSize: (v: THREE.Vector2) => v.set(288,420), getClearColor: (c: THREE.Color) => c.set('#ffffff'), getClearAlpha: () => 0,
        shadowMap:{autoUpdate:true}, setScissorTest: vi.fn(), setScissor: vi.fn(), setViewport: vi.fn(), setClearColor: vi.fn(), clear: vi.fn(),
      };
      e.dibujar(); e.dibujar();
      expect(cuadros).toEqual([
        [e.escena,e.camara,false,0,false], [e.escena,e.camaraLabios,true,1,true],
        [e.escena,e.camara,false,0,false], [e.escena,e.camaraLabios,true,1,true],
      ]);
      expect(e.camaraLabios.layers.mask).toBe(2);
      expect(e.renderer.setScissorTest).toHaveBeenLastCalledWith(false);
      expect(e.renderer.shadowMap.autoUpdate).toBe(true);
      expect(material.transparent).toBe(true);
      material.dispose(); e.mejilla.geometry.dispose();
    });
  }
});
