import { afterEach, describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import { EscenaBoca } from './escena';

/** Auditoría de 4e, ronda 2: cerrar el visor dejaba vivas la escena y su contexto
 *  (el keydown de OrbitControls en el document) y el audio podía sonar después. */
describe('cerrar el visor 3D', () => {
  afterEach(() => vi.restoreAllMocks());

  function escenaDeMentira() {
    const orden: string[] = [];
    const tecla = () => {};
    const raiz = { removeEventListener: vi.fn(() => orden.push('raiz')) };
    const mapa = new THREE.Texture();
    const soltarMapa = vi.spyOn(mapa, 'dispose');
    const escena = new THREE.Scene();
    escena.add(new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial({ map: mapa })));
    const renderer = { dispose: vi.fn(() => orden.push('renderer')), forceContextLoss: vi.fn(() => orden.push('contexto')) };
    const canvas = document.createElement('canvas');
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      vivo: true, rafId: 0, observador: null, raiz, escena, renderer, canvas,
      controles: { _interceptControlDown: tecla, dispose: vi.fn(() => orden.push('controles')) },
      papilas: null, hueso: null, luzPrincipal: { shadow: { dispose: vi.fn() } },
    });
    return { instancia, raiz, tecla, orden, renderer, soltarMapa };
  }

  it('quita el keydown de la raíz guardada antes de soltar los controles, y suelta mapas y contexto', () => {
    const { instancia, raiz, tecla, orden, renderer, soltarMapa } = escenaDeMentira();
    instancia.destruir();
    expect(raiz.removeEventListener).toHaveBeenCalledWith('keydown', tecla, { capture: true });
    expect(orden).toEqual(['raiz', 'controles', 'renderer', 'contexto']);
    expect(soltarMapa).toHaveBeenCalledOnce();
    expect(renderer.forceContextLoss).toHaveBeenCalledOnce();
    instancia.destruir();                       // dos veces no suelta dos veces
    expect(renderer.dispose).toHaveBeenCalledOnce();
  });
});
