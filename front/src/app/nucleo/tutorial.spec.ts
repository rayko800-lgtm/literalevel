import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { Entrada, Perfil } from './api';
import { Sesion } from './sesion';
import { Tutorial } from './tutorial';

/** Motor del tutorial guiado v2, D1.2: entrada e intención. Detrás de un
 *  flag de desarrollo, con persistencia versionada, degradación segura, y
 *  la máquina de estados como un grafo (no una lista lineal): elección
 *  entre Leer/Medir/Practicar, avance automático al completar una acción
 *  real (entrar, medir el nivel), y checkpoints donde D1.2 se detiene sin
 *  marcar el tutorial como completado. */
describe('Tutorial (D1.2)', () => {
  @Component({ selector: 'app-falsa', template: '<p>falsa</p>' })
  class Falsa {}

  const CLAVE = 'literalevel.tutorial';
  const CLAVE_DEV = 'literalevel.tutorial-dev';

  const ANONIMA: Entrada = { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' };
  const AUTENTICADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: null, openai: true, mensaje: '' };
  const PERFIL: Perfil = {
    nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
    nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
  };

  beforeEach(() => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    TestBed.configureTestingModule({
      providers: [
        provideRouter([
          { path: 'encontrar', component: Falsa },
          { path: 'nivel', component: Falsa },
          { path: 'palabras', component: Falsa },
          { path: 'pronunciar', component: Falsa },
        ]),
        provideHttpClient(), provideHttpClientTesting(),
      ],
    });
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

  it('activarDesarrollo() enciende el flag y lo deja guardado', () => {
    const t = crear();
    t.activarDesarrollo();
    expect(t.habilitado()).toBe(true);
    expect(localStorage.getItem(CLAVE_DEV)).toBe('on');
  });

  describe('con el flag ya activado', () => {
    beforeEach(() => { try { localStorage.setItem(CLAVE_DEV, 'on'); } catch { /* sin almacenamiento */ } });

    describe('sesión asíncrona: nunca cuenta-eleccion un instante a quien ya tiene sesión', () => {
      it('sesión ya conocida y autenticada al iniciar: arranca directo en intencion', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        expect(t.pasoActual()?.id).toBe('intencion');
        expect(t.puedeAtras()).toBe(false); // nunca pasó por cuenta-eleccion
      });

      it('sesión ya conocida y anónima al iniciar: arranca en cuenta-eleccion', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(ANONIMA);
        const t = crear();
        t.iniciar();
        expect(t.pasoActual()?.id).toBe('cuenta-eleccion');
      });

      it('sesión UNKNOWN → AUTHENTICATED: nunca se ve cuenta-eleccion, salta directo a intencion', () => {
        const sesion = TestBed.inject(Sesion);
        const t = crear();
        t.iniciar();
        expect(t.activo()).toBe(true);
        expect(t.pasoActual()).toBeNull(); // todavía no se sabe: no se muestra nada
        sesion.entrada.set(AUTENTICADA); // pasa a conocida y autenticada
        TestBed.tick(); // deja correr el `effect` que decide el salto
        expect(t.pasoActual()?.id).toBe('intencion');
      });

      it('sesión UNKNOWN → ANONYMOUS: cuenta-eleccion aparece solo después de saberlo', () => {
        const sesion = TestBed.inject(Sesion);
        const t = crear();
        t.iniciar();
        expect(t.pasoActual()).toBeNull();
        sesion.entrada.set(ANONIMA); // pasa a conocida y anónima
        expect(t.pasoActual()?.id).toBe('cuenta-eleccion');
      });
    });

    describe('cuenta-eleccion', () => {
      it('«Continuar sin cuenta» avanza directo a intencion', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(ANONIMA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Continuar sin cuenta')!);
        expect(t.pasoActual()?.id).toBe('intencion');
      });

      it('«Entrar» abre Ajustes y NO avanza hasta que la sesión pase a autenticada', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(ANONIMA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Entrar')!);
        expect(sesion.ajustesAbiertos()).toBe(true);
        expect(t.pasoActual()?.id).toBe('cuenta-eleccion'); // todavía esperando
        sesion.entrada.set(AUTENTICADA);
        TestBed.tick();
        expect(t.pasoActual()?.id).toBe('intencion');
      });
    });

    describe('intencion → Leer', () => {
      it('con nivel ya medido, navega a Encontrar y queda en el checkpoint encontrar-inicio, sin completar', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        sesion.perfil.set(PERFIL);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        expect(t.pasoActual()?.id).toBe('encontrar-inicio');
        expect(t.activo()).toBe(true); // NO completado
      });

      it('sin nivel, pasa por leer-eleccion antes de ir a Encontrar', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        expect(t.pasoActual()?.id).toBe('leer-eleccion');
      });

      it('leer-eleccion: «Buscar sin nivel» va a Encontrar sin pasar por Nivel', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Buscar sin nivel')!);
        expect(t.pasoActual()?.id).toBe('encontrar-inicio');
        expect(t.activo()).toBe(true);
      });

      it('leer-eleccion: «Medir mi nivel primero» entra por nivel-inicio, igual que el camino directo', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Medir mi nivel primero')!);
        expect(t.pasoActual()?.id).toBe('nivel-inicio');
      });
    });

    describe('intencion → Medir mi nivel → nivel-inicio → nivel-final', () => {
      it('al terminar el cuestionario (perfil() deja de ser null), avanza sola a nivel-final', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🎯 Medir mi nivel')!);
        expect(t.pasoActual()?.id).toBe('nivel-inicio');
        sesion.perfil.set(PERFIL); // como hace nivel.ts al contestar la última pregunta
        TestBed.tick(); // deja correr el `effect` que observa `perfil()`
        expect(t.pasoActual()?.id).toBe('nivel-final');
      });

      it('nivel-final no ofrece Atrás, aunque haya historial', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🎯 Medir mi nivel')!);
        sesion.perfil.set(PERFIL);
        TestBed.tick();
        expect(t.pasoActual()?.id).toBe('nivel-final');
        expect(t.puedeAtras()).toBe(false);
      });

      it('nivel-final avanza al checkpoint encontrar-inicio cuando el botón real navega a /encontrar, sin completar', async () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        const router = TestBed.inject(Router);
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🎯 Medir mi nivel')!);
        sesion.perfil.set(PERFIL);
        TestBed.tick();
        expect(t.pasoActual()?.id).toBe('nivel-final');
        await router.navigateByUrl('/encontrar'); // el clic real en el botón de nivel.html hace esto
        expect(t.pasoActual()?.id).toBe('encontrar-inicio');
        expect(t.activo()).toBe(true); // NO completado
      });

      it('si ya había perfil al llegar a nivel-inicio (perfil previo a este tutorial), salta directo a nivel-final', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        sesion.perfil.set(PERFIL); // perfil de una medición anterior
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🎯 Medir mi nivel')!);
        expect(t.pasoActual()?.id).toBe('nivel-final');
      });
    });

    describe('intencion → Practicar', () => {
      it('«Mis palabras» navega a /palabras y queda en el checkpoint practicar-inicio, sin completar', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🧠 Practicar')!);
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Mis palabras')!);
        expect(t.pasoActual()?.id).toBe('practicar-inicio');
        expect(t.activo()).toBe(true);
      });

      it('«Pronunciar» navega a /pronunciar y queda en el mismo checkpoint practicar-inicio, sin completar', () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🧠 Practicar')!);
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Pronunciar')!);
        expect(t.pasoActual()?.id).toBe('practicar-inicio');
        expect(t.activo()).toBe(true);
      });
    });

    it('Atrás vuelve al paso anterior; no ofrece nada si no hay historial', () => {
      const sesion = TestBed.inject(Sesion);
      sesion.entrada.set(AUTENTICADA);
      const t = crear();
      t.iniciar();
      expect(t.puedeAtras()).toBe(false); // intencion, sin cuenta-eleccion antes
      t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!); // sin perfil: leer-eleccion
      expect(t.pasoActual()?.id).toBe('leer-eleccion');
      expect(t.puedeAtras()).toBe(true);
      t.atras();
      expect(t.pasoActual()?.id).toBe('intencion');
      expect(t.puedeAtras()).toBe(false);
    });

    it('saltar() cierra el tutorial y guarda el estado "saltado" con el paso donde iba', () => {
      const sesion = TestBed.inject(Sesion);
      sesion.entrada.set(AUTENTICADA);
      const t = crear();
      t.iniciar();
      t.saltar();
      expect(t.activo()).toBe(false);
      const p = JSON.parse(localStorage.getItem(CLAVE)!);
      expect(p).toEqual({ version: 1, pasoId: 'intencion', estado: 'saltado' });
    });

    it('repetir() vuelve a empezar desde cuenta-eleccion o intencion, según la sesión', () => {
      const sesion = TestBed.inject(Sesion);
      sesion.entrada.set(AUTENTICADA);
      const t = crear();
      t.iniciar();
      t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '🧠 Practicar')!);
      t.saltar();
      t.repetir();
      expect(t.activo()).toBe(true);
      expect(t.pasoActual()?.id).toBe('intencion'); // ya autenticado, salta cuenta-eleccion
    });

    describe('persistencia y checkpoints entre recargas', () => {
      it('un checkpoint (encontrar-inicio) sobrevive un refresh: sigue activo, no completado', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'encontrar-inicio', estado: 'activo' }));
        const t = crear();
        expect(t.activo()).toBe(true);
        expect(t.pasoActual()?.id).toBe('encontrar-inicio');
        expect(t.pasoActual()?.silencioso).toBe(true);
      });

      it('un pasoId guardado que ya no existe degrada a estado seguro, sin romper nada', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'paso-que-ya-no-existe', estado: 'activo' }));
        const t = crear();
        expect(t.activo()).toBe(false);
        expect(t.pasoActual()).toBeNull();
        t.iniciar();
        expect(t.activo()).toBe(true);
      });

      it('una versión de progreso distinta se ignora, sin romper nada', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 2, pasoId: 'intencion', estado: 'activo' }));
        expect(() => crear()).not.toThrow();
        expect(crear().activo()).toBe(false);
      });

      it('con progreso "completado" o "saltado" guardado, NO se reactiva solo al crear el servicio', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'practicar-inicio', estado: 'completado' }));
        const t = crear();
        expect(t.activo()).toBe(false);
      });

      it('un JSON corrupto en el navegador se ignora, sin lanzar ni romper nada', () => {
        localStorage.setItem(CLAVE, '{no es json valido');
        expect(() => crear()).not.toThrow();
      });
    });

    it('completar() sigue existiendo pero ningún camino de D1.2 lo invoca: los tres checkpoints dejan activo() en true', () => {
      // Cubierto arriba (Leer con nivel, Mis palabras, Pronunciar, nivel-final→encontrar-inicio):
      // en los cuatro casos `t.activo()` se comprobó `true` al llegar al checkpoint.
      // Aquí solo se confirma que `completar()` en sí mismo sigue disponible para D1.5.
      const sesion = TestBed.inject(Sesion);
      sesion.entrada.set(AUTENTICADA);
      const t = crear();
      t.iniciar();
      t.completar();
      expect(t.activo()).toBe(false);
      const p = JSON.parse(localStorage.getItem(CLAVE)!);
      expect(p.estado).toBe('completado');
    });
  });
});
