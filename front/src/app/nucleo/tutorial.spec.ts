import { TestBed } from '@angular/core/testing';
import { Tutorial } from './tutorial';

/** Motor del tutorial guiado v2 (D1.1): detrás de un flag de desarrollo,
 *  con pasos de relleno, persistencia versionada y degradación segura ante
 *  un progreso guardado que ya no tiene sentido. */
describe('Tutorial', () => {
  const CLAVE = 'literalevel.tutorial';
  const CLAVE_DEV = 'literalevel.tutorial-dev';

  beforeEach(() => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    TestBed.configureTestingModule({});
  });

  function crear(): Tutorial {
    return TestBed.inject(Tutorial);
  }

  it('sin el flag de desarrollo, está deshabilitado y no se activa solo', () => {
    const t = crear();
    expect(t.habilitado()).toBe(false);
    t.iniciar();
    expect(t.activo()).toBe(false);
    expect(t.pasoActual()).toBeNull();
  });

  it('activarDesarrollo() enciende el flag y lo deja guardado en el navegador', () => {
    const t = crear();
    t.activarDesarrollo();
    expect(t.habilitado()).toBe(true);
    expect(localStorage.getItem(CLAVE_DEV)).toBe('on');
  });

  describe('con el flag ya activado', () => {
    beforeEach(() => { try { localStorage.setItem(CLAVE_DEV, 'on'); } catch { /* sin almacenamiento */ } });

    it('iniciar() activa el tutorial en el primer paso', () => {
      const t = crear();
      t.iniciar();
      expect(t.activo()).toBe(true);
      expect(t.pasoActual()?.id).toBe(t.pasos[0].id);
      expect(t.esPrimero()).toBe(true);
      expect(t.esUltimo()).toBe(false);
    });

    it('siguiente()/atrás() navegan y guardan el historial de pasos visitados', () => {
      const t = crear();
      t.iniciar();
      t.siguiente();
      expect(t.pasoActual()?.id).toBe(t.pasos[1].id);
      expect(t.esPrimero()).toBe(false);
      t.siguiente();
      expect(t.pasoActual()?.id).toBe(t.pasos[2].id);
      expect(t.esUltimo()).toBe(true);
      t.atras();
      expect(t.pasoActual()?.id).toBe(t.pasos[1].id);
      t.atras();
      expect(t.pasoActual()?.id).toBe(t.pasos[0].id);
      // Ya no hay más historial: atrás() en el primer paso no hace nada raro.
      t.atras();
      expect(t.pasoActual()?.id).toBe(t.pasos[0].id);
    });

    it('siguiente() en el último paso completa el tutorial', () => {
      const t = crear();
      t.iniciar();
      t.siguiente();
      t.siguiente();
      expect(t.esUltimo()).toBe(true);
      t.siguiente();
      expect(t.activo()).toBe(false);
      expect(t.pasoActual()).toBeNull();
      const p = JSON.parse(localStorage.getItem(CLAVE)!);
      expect(p).toEqual({ version: 1, pasoId: t.pasos[2].id, estado: 'completado' });
    });

    it('saltar() cierra el tutorial y guarda el estado "saltado" con el paso donde iba', () => {
      const t = crear();
      t.iniciar();
      t.siguiente();
      t.saltar();
      expect(t.activo()).toBe(false);
      const p = JSON.parse(localStorage.getItem(CLAVE)!);
      expect(p).toEqual({ version: 1, pasoId: t.pasos[1].id, estado: 'saltado' });
    });

    it('repetir() vuelve a empezar desde el primer paso', () => {
      const t = crear();
      t.iniciar();
      t.siguiente();
      t.saltar();
      t.repetir();
      expect(t.activo()).toBe(true);
      expect(t.pasoActual()?.id).toBe(t.pasos[0].id);
    });

    it('con progreso "activo" guardado y válido, retoma exactamente ese paso al crear el servicio', () => {
      const previo = crear();
      previo.iniciar();
      previo.siguiente();
      const pasoGuardado = previo.pasoActual()!.id;

      const t = crear(); // simula una recarga: nueva instancia del servicio
      expect(t.activo()).toBe(true);
      expect(t.pasoActual()?.id).toBe(pasoGuardado);
    });

    it('con progreso "completado" o "saltado" guardado, NO se reactiva solo al crear el servicio', () => {
      const previo = crear();
      previo.iniciar();
      previo.saltar();

      const t = crear();
      expect(t.activo()).toBe(false);
      expect(t.pasoActual()).toBeNull();
    });

    it('un pasoId guardado que ya no existe degrada a estado seguro, sin romper nada', () => {
      localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'paso-que-ya-no-existe', estado: 'activo' }));
      const t = crear();
      expect(t.activo()).toBe(false);
      expect(t.pasoActual()).toBeNull();
      // Sigue siendo utilizable con normalidad.
      t.iniciar();
      expect(t.activo()).toBe(true);
    });

    it('una versión de progreso distinta se ignora, sin romper nada', () => {
      localStorage.setItem(CLAVE, JSON.stringify({ version: 2, pasoId: 'placeholder-1', estado: 'activo' }));
      const t = crear();
      expect(t.activo()).toBe(false);
    });

    it('un JSON corrupto en el navegador se ignora, sin lanzar ni romper nada', () => {
      localStorage.setItem(CLAVE, '{no es json valido');
      expect(() => crear()).not.toThrow();
      expect(crear().activo()).toBe(false);
    });
  });
});
