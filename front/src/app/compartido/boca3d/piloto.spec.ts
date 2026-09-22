import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, cierreLabial, poseNumerica } from './escena';
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
        // v4: en reposo los labios ya están casi juntos (cierre 1 con la
        // mandíbula de reposo); lo que va y viene en /p b/ es la COMPRESIÓN.
        expect(en(simbolo, velocidad, 0.42)[I_CIERRE_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 0.42)[I_COMPRESION_LABIOS]).toBe(0);
        expect(en(simbolo, velocidad, 0.70)[I_COMPRESION_LABIOS]).toBeGreaterThan(0);
        expect(en(simbolo, velocidad, 0.70)[I_COMPRESION_LABIOS]).toBeLessThan(1);
        expect(en(simbolo, velocidad, 1.2)[I_CIERRE_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.2)[I_COMPRESION_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.5)[I_COMPRESION_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.6)[I_COMPRESION_LABIOS]).toBeCloseTo(0.5);
        expect(en(simbolo, velocidad, 2.25)[I_COMPRESION_LABIOS]).toBe(0);
      });
    }
    it(`/m/ mantiene contacto con menor compresion a ${velocidad}x`, () => {
      expect(en('m', velocidad, 1.6)[I_CIERRE_LABIOS]).toBe(1);
      expect(en('m', velocidad, 1.9)[I_CIERRE_LABIOS]).toBe(1);
      expect(en('m', velocidad, 1.6)[I_COMPRESION_LABIOS]).toBe(0.35);
      expect(en('p', velocidad, 1.2)[I_COMPRESION_LABIOS]).toBe(1);
    });
  }
  it('sin labios cerrados no hay compresion; el cierre neutro sigue la mandibula (v4)', () => {
    for (const s of ['θ','k','t','ŋ']) {
      const n = poseNumerica(poseDe(catalogo,s)!);
      expect(n[I_COMPRESION_LABIOS]).toBe(0);
      expect(n[I_CIERRE_LABIOS]).toBe(cierreLabial(poseDe(catalogo,s)!));
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
        getPixelRatio: () => 2, setRenderTarget: vi.fn(),
        shadowMap:{autoUpdate:true}, setScissorTest: vi.fn(), setScissor: vi.fn(), setViewport: vi.fn(), setClearColor: vi.fn(), clear: vi.fn(),
      };
      e.linea = null; e.hacia = null; e.detalleCuadro = 0; e.detalleListo = false;
      e.dibujar(); e.dibujar();
      // v4: la pasada del detalle va a su textura y el recuadro se copia con un plano.
      expect(cuadros).toEqual([
        [e.escena,e.camara,false,0,false], [e.escena,e.camaraLabios,true,1,true], [e.detalle.escena,e.detalle.camara,false,0,false],
        [e.escena,e.camara,false,0,false], [e.escena,e.camaraLabios,true,1,true], [e.detalle.escena,e.detalle.camara,false,0,false],
      ]);
      expect(e.renderer.setRenderTarget).toHaveBeenCalledWith(e.detalle.rt);
      expect(e.renderer.setRenderTarget).toHaveBeenLastCalledWith(null);
      // En movimiento, el detalle se repinta uno de cada tres cuadros y el recuadro siempre.
      e.linea = { claves: [], total: 1 };
      cuadros.length = 0;
      for (let k = 0; k < 6; k++) e.dibujar();
      expect(cuadros.filter(c => (c as unknown[])[1] === e.camaraLabios).length).toBe(2);
      expect(cuadros.filter(c => (c as unknown[])[0] === e.detalle.escena).length).toBe(6);
      e.detalle.rt.dispose(); e.detalle.material.dispose();
      expect(e.camaraLabios.layers.mask).toBe(2);
      expect(e.renderer.setScissorTest).toHaveBeenLastCalledWith(false);
      expect(e.renderer.shadowMap.autoUpdate).toBe(true);
      expect(material.transparent).toBe(true);
      material.dispose(); e.mejilla.geometry.dispose();
    });
  }
});
