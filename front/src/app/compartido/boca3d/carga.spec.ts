import { afterEach, describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { bajarGlb, EscenaBoca, MORFOS_LENGUA, poseNumerica } from './escena';
import { REPOSO } from './poses';

const respuesta = (status = 200) => ({ ok: status < 400, status, arrayBuffer: async () => new ArrayBuffer(8) });
const tanda = () => new Promise(r => setTimeout(r, 0));

describe('carga de lengua Blender', () => {
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

  async function ensayo(vivo: boolean, completa: boolean) {
    const grupo = new THREE.Group();
    const malla = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial());
    malla.morphTargetInfluences = MORFOS_LENGUA.map(() => 0);
    malla.morphTargetDictionary = Object.fromEntries(
      MORFOS_LENGUA.slice(0, completa ? undefined : -1).map((n, i) => [n, i]));
    grupo.add(malla);
    const liberarGeometria = vi.spyOn(malla.geometry, 'dispose');
    const liberarMaterial = vi.spyOn(malla.material, 'dispose');
    vi.stubGlobal('fetch', vi.fn(async () => respuesta()));
    vi.spyOn(GLTFLoader.prototype, 'parse').mockImplementation((_bytes, _ruta, cargar) => {
      cargar({ scene: grupo } as never);
    });
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      vivo, contenedor: document.createElement('div'), lengua: { visible: true },
      dentroMandibula: new THREE.Group(), actual: poseNumerica(REPOSO), aplicar: vi.fn(),
      // D4.3c: cargarLengua() ya llama a vistaExterior() al terminar.
      familiaActual: 'vocal', velo: { visible: true },
      piezasCorte: [], piezasDentalesInferiores: [], piezasDentalesSuperiores: [],
      dentalSimple: [], dentalesModelados: false,
    });
    instancia.cargarLengua('/boca3d/lengua.glb', '#d9727f');
    await tanda();
    return { instancia, malla, liberarGeometria, liberarMaterial };
  }

  it('libera un modelo que llega despues de desmontar el visor', async () => {
    const { instancia, liberarGeometria, liberarMaterial } = await ensayo(false, true);
    expect(liberarGeometria).toHaveBeenCalledOnce();
    expect(liberarMaterial).toHaveBeenCalledOnce();
    expect(instancia.lengua.visible).toBe(true);
  });

  it('no sustituye el respaldo si falta un morfo del contrato', async () => {
    const { instancia, liberarGeometria } = await ensayo(true, false);
    expect(instancia.lengua.visible).toBe(true);
    expect(instancia.dentroMandibula.children.length).toBe(0);
    expect(liberarGeometria).toHaveBeenCalledOnce();
  });

  it('conserva la geometria valida, libera material anterior y aplica la pose vigente', async () => {
    const { instancia, malla, liberarGeometria, liberarMaterial } = await ensayo(true, true);
    expect(instancia.lengua.visible).toBe(false);
    expect(malla.parent).toBe(instancia.dentroMandibula);
    expect(liberarMaterial).toHaveBeenCalledOnce();
    expect(liberarGeometria).not.toHaveBeenCalled();
    expect(instancia.contenedor.dataset.lengua).toBe('blender');
    expect(instancia.aplicar).toHaveBeenCalledWith(instancia.actual);
  });
});

/** 4e, ronda 3: cada apertura volvía a bajar cara.glb y lengua.glb (URL firmada distinta). */
describe('bajada de los .glb', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('baja cada archivo una vez por página, aunque el visor se abra muchas veces', async () => {
    const pedir = vi.fn(async (_url: string) => respuesta());
    vi.stubGlobal('fetch', pedir);
    const [una, otra] = await Promise.all([bajarGlb('/prueba/cara.glb'), bajarGlb('/prueba/cara.glb')]);
    await bajarGlb('/prueba/cara.glb');
    await bajarGlb('/prueba/lengua.glb');
    expect(una).toBe(otra);
    expect(pedir.mock.calls.map(c => c[0])).toEqual(['/prueba/cara.glb', '/prueba/lengua.glb']);
  });

  it('un fallo no se queda guardado: la siguiente apertura lo vuelve a pedir', async () => {
    const pedir = vi.fn().mockResolvedValueOnce(respuesta(503)).mockResolvedValueOnce(respuesta());
    vi.stubGlobal('fetch', pedir);
    await expect(bajarGlb('/prueba/falla.glb')).rejects.toThrow('503');
    expect((await bajarGlb('/prueba/falla.glb')).byteLength).toBe(8);
    expect(pedir).toHaveBeenCalledTimes(2);
  });
});
