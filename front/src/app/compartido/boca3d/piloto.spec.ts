import { EscenaBoca, I_CIERRE_LABIOS, I_COMPRESION_LABIOS, I_NEUTRO_ARTICULADO, cierreLabial, poseNumerica, actualizarSeccionSagital, normalesDelGesto, pielQueSigueLaMandibula } from './escena';
import { aVelocidad, cicloSonido } from './animacion';
import { AjustesPoses3d, CatalogoPoses, conAjustes3d, poseDe } from './poses';
import poses from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';
import * as THREE from 'three';

const catalogo = conAjustes3d(poses as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
describe('iluminación del gesto', () => {
  it('suaviza el movimiento en piel contigua a la ranura y conserva el borde labial', () => {
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute([-3,.149,0,-3,.151,0,-3,.149,0,-3,.151,0],3));
    g.setAttribute('uv1',new THREE.Float32BufferAttribute([.3,0,.3,0,0,0,0,0],2));
    const piel=pielQueSigueLaMandibula(g,true,true,true);
    expect(Math.abs(piel.pesos[0]-piel.pesos[1])).toBeLessThan(.001);
    expect(piel.pesos[2]-piel.pesos[3]).toBeGreaterThan(1);
    g.dispose();
  });
  it('preserva las normales del escaneo nasal mientras recalcula la zona móvil', () => {
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,1,0,0,0,1,0, 0,2,0,1,2,0,0,3,0],3));
    g.setAttribute('normal',new THREE.Float32BufferAttribute([0,0,1,0,0,1,0,0,1, .6,0,.8,.6,0,.8,.6,0,.8],3));
    g.setIndex([0,1,2,3,4,5]);g.morphTargetsRelative=true;
    g.morphAttributes.position=[new THREE.Float32BufferAttribute([0,0,0,0,0,1,0,0,0, 0,0,0,0,0,0,0,0,0],3)];
    const mesh=new THREE.Mesh(g),actualizar=normalesDelGesto(mesh,true);
    mesh.morphTargetInfluences![0]=1;actualizar();
    const normales=g.getAttribute('normal');
    for(let i=0;i<3;i++)expect(new THREE.Vector3().fromBufferAttribute(normales,i).distanceTo(new THREE.Vector3(-1,0,1).normalize())).toBeLessThan(1e-6);
    for(let i=3;i<6;i++)expect(new THREE.Vector3().fromBufferAttribute(normales,i).distanceTo(new THREE.Vector3(.6,0,.8))).toBeLessThan(1e-6);
    g.dispose();(mesh.material as THREE.Material).dispose();
  });
  it('actualiza la normal geométrica a través de una costura sin cambiar posiciones ni buffer', () => {
    const g=new THREE.BufferGeometry();
    const base=[0,0,0, 1,0,0, 1,1,0, 0,0,0, 1,1,0, 0,1,0];
    g.setAttribute('position',new THREE.Float32BufferAttribute(base,3));
    g.setIndex([0,1,2,3,4,5]);
    g.morphTargetsRelative=true;
    g.morphAttributes.position=[new THREE.Float32BufferAttribute([0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0],3)];
    const mesh=new THREE.Mesh(g),actualizar=normalesDelGesto(mesh),buffer=g.getAttribute('normal');
    for (const f of [0,.5,1,0]) {
      mesh.morphTargetInfluences![0]=f;actualizar();
      const esperada=new THREE.Vector3(-f,0,1).normalize();
      for(let i=0;i<6;i++) expect(new THREE.Vector3().fromBufferAttribute(buffer,i).distanceTo(esperada)).toBeLessThan(1e-6);
      expect(g.getAttribute('normal')).toBe(buffer);
      expect(Array.from(g.getAttribute('position').array)).toEqual(base);
    }
    g.dispose();
  });
});
describe('relleno de sección anatómica', () => {
  it('conserva el área al formar una concavidad y reutiliza el índice GPU', () => {
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,3,0,0,3,3,0,1.5,3,0,0,3,0],3));
    g.morphTargetsRelative=true;
    g.morphAttributes.position=[new THREE.Float32BufferAttribute([0,0,0,0,0,0,0,0,0,0,-2,0,0,0,0],3)];
    g.setIndex(new THREE.Uint16BufferAttribute(new Uint16Array(9),1));
    const m=new THREE.Mesh(g),indice=g.index;
    for(const f of [0,.5,1,0]) {
      m.morphTargetInfluences![0]=f;actualizarSeccionSagital(m);
      let area=0;
      for(let i=0;i<g.drawRange.count;i+=3) {
        const [a,b,c]=[0,1,2].map(j => m.getVertexPosition(g.index!.getX(i+j),new THREE.Vector3()));
        area+=new THREE.Triangle(a,b,c).getArea();
      }
      expect(area).toBeCloseTo(9-3*f,5);
      expect(g.index).toBe(indice);
    }
    g.dispose();(m.material as THREE.Material).dispose();
  });
});
describe('exterior: articulación neutra y reposo', () => {
  it('no confunde reposo descrito con una vocal ni sella los neutros articulados', () => {
    expect(poseNumerica({...catalogo.reposo, leyenda: 'boca en reposo'})[I_NEUTRO_ARTICULADO]).toBe(0);
    for (const s of ['t','d','n','k','ɡ','ŋ','l','h','θ','ð','ɪ','ɛ','ɑ','ʌ','ə','ɚ'])
      expect(poseNumerica(poseDe(catalogo,s)!)[I_NEUTRO_ARTICULADO], s).toBe(1);
    for (const s of ['p','b','m','f','v','i','u'])
      expect(poseNumerica(poseDe(catalogo,s)!)[I_NEUTRO_ARTICULADO], s).toBe(0);
  });
});
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
        // v5: en reposo (mandíbula 0,2) el cierre vale 1; en /p b/ (0,08), 0,4
        // (la shape key se calculó para el reposo y se escala por mandíbula/0,2).
        expect(en(simbolo, velocidad, 0.42)[I_CIERRE_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 0.42)[I_COMPRESION_LABIOS]).toBe(0);
        expect(en(simbolo, velocidad, 0.70)[I_COMPRESION_LABIOS]).toBeGreaterThan(0);
        expect(en(simbolo, velocidad, 0.70)[I_COMPRESION_LABIOS]).toBeLessThan(1);
        expect(en(simbolo, velocidad, 1.2)[I_CIERRE_LABIOS]).toBeCloseTo(0.4);
        expect(en(simbolo, velocidad, 1.2)[I_COMPRESION_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.5)[I_COMPRESION_LABIOS]).toBe(1);
        expect(en(simbolo, velocidad, 1.6)[I_COMPRESION_LABIOS]).toBeCloseTo(0.5);
        expect(en(simbolo, velocidad, 2.25)[I_COMPRESION_LABIOS]).toBe(0);
      });
    }
    it(`/m/ mantiene contacto con menor compresion a ${velocidad}x`, () => {
      expect(en('m', velocidad, 1.6)[I_CIERRE_LABIOS]).toBeCloseTo(0.4);
      expect(en('m', velocidad, 1.9)[I_CIERRE_LABIOS]).toBeCloseTo(0.4);
      expect(en('m', velocidad, 1.6)[I_COMPRESION_LABIOS]).toBe(0.35);
      expect(en('p', velocidad, 1.2)[I_COMPRESION_LABIOS]).toBe(1);
    });
  }
  it('sin labios cerrados no hay compresion; el cierre neutro sigue la mandibula (v4)', () => {
    for (const s of ['θ','k','t','ŋ']) {
      const n = poseNumerica(poseDe(catalogo,s)!);
      expect(n[I_COMPRESION_LABIOS]).toBe(0);
      expect(n[I_CIERRE_LABIOS]).toBeCloseTo(cierreLabial(poseDe(catalogo,s)!) * Math.min(1, poseDe(catalogo,s)!.mandibula / 0.2));
    }
  });
});

describe('vista lateral única en el visor', () => {
  it('girar el exterior no lo sustituye automáticamente por el corte', () => {
    const e = Object.create(EscenaBoca.prototype);
    e.exploracionDidactica = true;e.cabezaEntera = true;e.corteDidactico = false;
    e.camara = new THREE.PerspectiveCamera();
    e.dibujarExteriorDidactico = vi.fn();
    for (const a of [0, .61, 1.57, 3.14, -1.57]) {
      e.camara.position.set(Math.sin(a)*10,0,Math.cos(a)*10);
      e.dibujar();
    }
    expect(e.dibujarExteriorDidactico).toHaveBeenCalledTimes(5);
  });
  it('el botón de vista cambia solo cámara/corte y conserva el gesto', () => {
    const e = Object.create(EscenaBoca.prototype);
    e.exploracionDidactica=true;e.controles={};e.vista=vi.fn();
    e.camara=new THREE.PerspectiveCamera(32);
    const pose=poseNumerica(poseDe(catalogo,'f')!);e.actual=pose;
    e.vistaDidactica(false);
    expect(e.corteDidactico).toBe(true);
    expect(e.controles.minAzimuthAngle).toBeLessThan(0);
    expect(e.controles.maxAzimuthAngle).toBeLessThan(Math.PI/2);
    e.vistaDidactica(true);
    expect(e.corteDidactico).toBe(false);
    expect(e.controles.maxAzimuthAngle).toBe(Infinity);
    expect(e.camara.fov).toBeLessThan(32);
    expect(e.actual).toBe(pose);
    e.vistaDidactica(false);
    expect(e.camara.fov).toBe(32);
  });
  it.each(['bilabial', 'nasal-bilabial', 'labiodental'])('%s: pinta solo el corte con la cabeza cargada', (familia) => {
    const e = Object.create(EscenaBoca.prototype);
    e.escena = new THREE.Scene();
    e.camara = new THREE.PerspectiveCamera();
    e.cabezaEntera = true; e.familiaActual = familia; e.detalleFrontalActivo = false;
    const mat = new THREE.MeshPhysicalMaterial({ transparent: true, opacity: 0, depthWrite: false });
    e.mejilla = new THREE.Mesh(new THREE.BufferGeometry(), mat);
    const vistas: THREE.Camera[] = [];
    e.renderer = { render: (_: THREE.Scene, camara: THREE.Camera) => { vistas.push(camara); } };
    e.dibujar();
    expect(vistas).toEqual([e.camara]);
    mat.dispose(); e.mejilla.geometry.dispose();
  });
});

describe('D4.4b v3: detalle frontal sincronizado', () => {
  for (const familia of ['bilabial', 'nasal-bilabial']) {
    it(`${familia}: dibuja el mismo estado y restaura la transparencia del corte`, () => {
      const e = Object.create(EscenaBoca.prototype);
      e.escena = new THREE.Scene();
      e.camara = new THREE.PerspectiveCamera();
      e.camaraLabios = new THREE.PerspectiveCamera();
      e.cabezaEntera = true; e.familiaActual = familia; e.detalleFrontalActivo = true;
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
