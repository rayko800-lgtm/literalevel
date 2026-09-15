import { afterEach, describe, expect, it, vi } from 'vitest';
import * as THREE from 'three';
import { EscenaBoca } from './escena';

/** Auditoría de 4e, ronda 2: cerrar el visor dejaba vivas la escena y su contexto
 *  (el keydown de OrbitControls en el document, y un renderer nuevo por apertura). */
describe('cerrar el visor 3D', () => {
  afterEach(() => vi.restoreAllMocks());

  function escenaDeMentira(propio: boolean) {
    const orden: string[] = [];
    const tecla = () => {};
    const raiz = { removeEventListener: vi.fn(() => orden.push('raiz')) };
    const mapa = new THREE.Texture();
    const soltarMapa = vi.spyOn(mapa, 'dispose');
    const escena = new THREE.Scene();
    escena.add(new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial({ map: mapa })));
    const renderer = {
      dispose: vi.fn(() => orden.push('renderer')), forceContextLoss: vi.fn(() => orden.push('contexto')),
      renderLists: { dispose: vi.fn(() => orden.push('listas')) }, setRenderTarget: vi.fn(),
    };
    const canvas = document.createElement('canvas');
    const instancia = Object.assign(Object.create(EscenaBoca.prototype), {
      vivo: true, rafId: 0, observador: null, raiz, escena, renderer, canvas, propio,
      alPerderContexto: () => {},
      controles: { _interceptControlDown: tecla, dispose: vi.fn(() => orden.push('controles')) },
      papilas: null, hueso: null, luzPrincipal: { shadow: { dispose: vi.fn() } },
    });
    return { instancia, raiz, tecla, orden, renderer, soltarMapa };
  }

  it('quita el keydown de la raíz guardada antes de soltar los controles, y suelta los mapas', () => {
    const { instancia, raiz, tecla, orden, soltarMapa } = escenaDeMentira(false);
    instancia.destruir();
    expect(raiz.removeEventListener).toHaveBeenCalledWith('keydown', tecla, { capture: true });
    expect(orden.slice(0, 2)).toEqual(['raiz', 'controles']);
    expect(soltarMapa).toHaveBeenCalledOnce();
  });

  it('el renderer compartido se vacía y se conserva; uno propio se suelta con su contexto', () => {
    const compartido = escenaDeMentira(false);
    compartido.instancia.destruir();
    expect(compartido.renderer.renderLists.dispose).toHaveBeenCalledOnce();
    expect(compartido.renderer.dispose).not.toHaveBeenCalled();
    expect(compartido.renderer.forceContextLoss).not.toHaveBeenCalled();

    const propio = escenaDeMentira(true);
    propio.instancia.destruir();
    expect(propio.orden.slice(-2)).toEqual(['renderer', 'contexto']);
    propio.instancia.destruir();                // dos veces no suelta dos veces
    expect(propio.renderer.dispose).toHaveBeenCalledOnce();
  });
});
