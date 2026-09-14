import { afterEach, describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { EscenaBoca, MORFOS_LENGUA, poseNumerica } from './escena';
import { REPOSO } from './poses';

describe('carga de lengua Blender', () => {
  afterEach(() => vi.restoreAllMocks());

  function ensayo(vivo: boolean, completa: boolean) {
    const grupo = new THREE.Group();
    const malla = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial());
    malla.morphTargetInfluences = MORFOS_LENGUA.map(() => 0);
    malla.morphTargetDictionary = Object.fromEntries(
      MORFOS_LENGUA.slice(0, completa ? undefined : -1).map((n, i) => [n, i]));
    grupo.add(malla);
    const liberarGeometria = vi.spyOn(malla.geometry, 'dispose');
    const liberarMaterial = vi.spyOn(malla.material, 'dispose');
    vi.spyOn(GLTFLoader.prototype, 'load').mockImplementation((_url, cargar) => {
      cargar({ scene: grupo } as never);
    });
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      vivo, contenedor: document.createElement('div'), lengua: { visible: true },
      dentroMandibula: new THREE.Group(), actual: poseNumerica(REPOSO), aplicar: vi.fn(),
    });
    instancia.cargarLengua('/boca3d/lengua.glb', '#d9727f');
    return { instancia, malla, liberarGeometria, liberarMaterial };
  }

  it('libera un modelo que llega despues de desmontar el visor', () => {
    const { instancia, liberarGeometria, liberarMaterial } = ensayo(false, true);
    expect(liberarGeometria).toHaveBeenCalledOnce();
    expect(liberarMaterial).toHaveBeenCalledOnce();
    expect(instancia.lengua.visible).toBe(true);
  });

  it('no sustituye el respaldo si falta un morfo del contrato', () => {
    const { instancia, liberarGeometria } = ensayo(true, false);
    expect(instancia.lengua.visible).toBe(true);
    expect(instancia.dentroMandibula.children.length).toBe(0);
    expect(liberarGeometria).toHaveBeenCalledOnce();
  });

  it('conserva la geometria valida, libera material anterior y aplica la pose vigente', () => {
    const { instancia, malla, liberarGeometria, liberarMaterial } = ensayo(true, true);
    expect(instancia.lengua.visible).toBe(false);
    expect(malla.parent).toBe(instancia.dentroMandibula);
    expect(liberarMaterial).toHaveBeenCalledOnce();
    expect(liberarGeometria).not.toHaveBeenCalled();
    expect(instancia.contenedor.dataset.lengua).toBe('blender');
    expect(instancia.aplicar).toHaveBeenCalledWith(instancia.actual);
  });
});
