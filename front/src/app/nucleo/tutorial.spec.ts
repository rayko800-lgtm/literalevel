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
          { path: 'libro/:id', component: Falsa },
          { path: 'leer/:id/:cap', component: Falsa },
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

      it('nivel-final avanza directo a encontrar-busqueda (vía el checkpoint encontrar-inicio) cuando el botón real navega a /encontrar, sin completar', async () => {
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
        // La misma navegación resuelve los dos pasos en cadena (D1.3): nunca
        // se queda esperando una segunda navegación que no va a llegar.
        expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
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

    it('completar() sigue existiendo pero ningún camino de D1.2/D1.3 lo invoca: todos los checkpoints dejan activo() en true', () => {
      // Cubierto arriba (Leer con nivel, Mis palabras, Pronunciar, nivel-final→…):
      // en todos los casos `t.activo()` se comprobó `true` al llegar al checkpoint.
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

    describe('D1.3: búsqueda y libro', () => {
      it('encontrar-inicio retoma correctamente desde D1.2 vía navegación real (no se queda esperando otra)', async () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'encontrar-inicio', estado: 'activo' }));
        const t = crear();
        const router = TestBed.inject(Router);
        expect(t.pasoActual()?.id).toBe('encontrar-inicio');
        await router.navigateByUrl('/encontrar');
        expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
      });

      it('restaurar encontrar-inicio y navegar a OTRA ruta no produce avance falso; conserva el checkpoint', async () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'encontrar-inicio', estado: 'activo' }));
        const t = crear();
        const router = TestBed.inject(Router);
        await router.navigateByUrl('/nivel');
        expect(t.pasoActual()?.id).toBe('encontrar-inicio'); // sigue esperando, sin bloquear la navegación
        expect(t.activo()).toBe(true);
      });

      it('búsqueda en curso, sin notificar todavía: sigue esperando en encontrar-busqueda, sin avanzar', async () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        const t = crear();
        const router = TestBed.inject(Router);
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!); // sin perfil: leer-eleccion
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === 'Buscar sin nivel')!); // → encontrar-inicio
        await router.navigateByUrl('/encontrar'); // → encontrar-busqueda (cadena de D1.3)
        expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
        // Ni «con-resultados» ni «sin-resultados» ni «error»: como si la promesa
        // de la API siguiera pendiente. No debe avanzar solo.
        expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
      });

      describe('en encontrar-busqueda', () => {
        function crearEnBusqueda(): { t: Tutorial; sesion: Sesion } {
          const sesion = TestBed.inject(Sesion);
          sesion.entrada.set(AUTENTICADA);
          sesion.perfil.set(PERFIL);
          const t = crear();
          t.iniciar();
          t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!); // con perfil: directo a encontrar-inicio
          return { t, sesion };
        }

        it('notificarBusqueda se ignora si el tutorial está inactivo', () => {
          const { t } = crearEnBusqueda();
          t.saltar();
          expect(t.activo()).toBe(false);
          t.notificarBusqueda('con-resultados'); // no debe lanzar ni reactivar nada
          expect(t.activo()).toBe(false);
        });

        it('notificarBusqueda se ignora si el paso actual no es encontrar-busqueda', () => {
          const { t } = crearEnBusqueda();
          // Con perfil, «Leer» deja el tutorial en encontrar-inicio (checkpoint),
          // no en encontrar-busqueda todavía (falta la navegación real).
          expect(t.pasoActual()?.id).toBe('encontrar-inicio');
          t.notificarBusqueda('con-resultados');
          expect(t.pasoActual()?.id).toBe('encontrar-inicio'); // sin cambios
        });

        it('con resultados avanza a encontrar-resultados y limpia el aviso', async () => {
          const { t, sesion } = crearEnBusqueda();
          const router = TestBed.inject(Router);
          await router.navigateByUrl('/encontrar');
          expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
          t.notificarBusqueda('sin-resultados');
          expect(t.avisoTransitorio()).toContain('No encontré resultados');
          t.notificarBusqueda('inicio'); // nueva búsqueda: limpia el aviso anterior
          expect(t.avisoTransitorio()).toBeNull();
          t.notificarBusqueda('con-resultados');
          expect(t.pasoActual()?.id).toBe('encontrar-resultados');
          expect(t.avisoTransitorio()).toBeNull();
          void sesion; // solo para reutilizar el helper
        });

        it('sin resultados: no avanza falsamente, deja un aviso no bloqueante', async () => {
          const { t } = crearEnBusqueda();
          await TestBed.inject(Router).navigateByUrl('/encontrar');
          t.notificarBusqueda('sin-resultados');
          expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
          expect(t.avisoTransitorio()).toBe('No encontré resultados. Prueba con otra búsqueda.');
          expect(t.activo()).toBe(true);
        });

        it('error: no marca progreso falso, deja Saltar disponible (activo sigue true)', async () => {
          const { t } = crearEnBusqueda();
          await TestBed.inject(Router).navigateByUrl('/encontrar');
          t.notificarBusqueda('error');
          expect(t.pasoActual()?.id).toBe('encontrar-busqueda');
          expect(t.avisoTransitorio()).toContain('problema');
          expect(t.activo()).toBe(true);
          t.saltar();
          expect(t.activo()).toBe(false); // Saltar sigue funcionando
        });
      });

      it('cualquier navegación válida a /libro/:id avanza a libro-ficha, sin importar qué tarjeta era', async () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        sesion.perfil.set(PERFIL);
        const t = crear();
        const router = TestBed.inject(Router);
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        await router.navigateByUrl('/encontrar');
        t.notificarBusqueda('con-resultados');
        expect(t.pasoActual()?.id).toBe('encontrar-resultados');
        await router.navigateByUrl('/libro/SWV12345'); // una tarjeta cualquiera, no la primera
        expect(t.pasoActual()?.id).toBe('libro-ficha');
        expect(t.pasoActual()?.silencioso).toBe(true);
        expect(t.activo()).toBe(true);
      });

      it('cualquiera de las rutas /leer/:id/:cap avanza hasta lector-palabra (vía el checkpoint lector-inicio) desde libro-ficha, sin completar', async () => {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        sesion.perfil.set(PERFIL);
        const t = crear();
        const router = TestBed.inject(Router);
        t.iniciar();
        t.elegir(t.pasoActual()!.opciones!.find(o => o.etiqueta === '📖 Leer')!);
        await router.navigateByUrl('/encontrar');
        t.notificarBusqueda('con-resultados');
        await router.navigateByUrl('/libro/PG11');
        expect(t.pasoActual()?.id).toBe('libro-ficha');
        await router.navigateByUrl('/leer/PG11/3'); // no el capítulo 0: cualquier capítulo vale
        // La misma navegación resuelve los dos pasos en cadena (D1.4), igual
        // que nivel-final → encontrar-inicio → encontrar-busqueda en D1.3.
        expect(t.pasoActual()?.id).toBe('lector-palabra');
        expect(t.activo()).toBe(true); // NO completado
      });

      it('llegar a lector-inicio sobrevive un refresh, sigue activo, no completado', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'lector-inicio', estado: 'activo' }));
        const t = crear();
        expect(t.activo()).toBe(true);
        expect(t.pasoActual()?.id).toBe('lector-inicio');
        expect(t.pasoActual()?.silencioso).toBe(true);
      });
    });

    describe('D1.4: lector, léxico y pronunciar', () => {
      function crearDesdeLectorInicio(): Tutorial {
        const sesion = TestBed.inject(Sesion);
        sesion.entrada.set(AUTENTICADA);
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'lector-inicio', estado: 'activo' }));
        return crear();
      }

      it('lector-inicio retoma correctamente y avanza a lector-palabra solo cuando el router está REALMENTE en /leer/', async () => {
        const t = crearDesdeLectorInicio();
        const router = TestBed.inject(Router);
        expect(t.pasoActual()?.id).toBe('lector-inicio');
        await router.navigateByUrl('/leer/PG11/1');
        expect(t.pasoActual()?.id).toBe('lector-palabra');
      });

      it('notificarLector se ignora mientras el paso todavía es lector-inicio (no lector-palabra)', () => {
        const t = crearDesdeLectorInicio();
        t.notificarLector('palabra'); // todavía en lector-inicio: el router no ha confirmado /leer/
        expect(t.pasoActual()?.id).toBe('lector-inicio');
      });

      it('notificarLector se ignora si el tutorial está inactivo', async () => {
        const t = crearDesdeLectorInicio();
        const router = TestBed.inject(Router);
        await router.navigateByUrl('/leer/PG11/1');
        t.saltar();
        expect(t.activo()).toBe(false);
        t.notificarLector('palabra');
        expect(t.activo()).toBe(false); // no se reactivó
      });

      it('lector-palabra → lexico-abierto vía notificarLector, sin palabra hardcodeada', async () => {
        const t = crearDesdeLectorInicio();
        const router = TestBed.inject(Router);
        await router.navigateByUrl('/leer/PG11/1');
        expect(t.pasoActual()?.id).toBe('lector-palabra');
        t.notificarLector('palabra'); // cualquier palabra vale: el lector ya decidió que es "utilizable"
        expect(t.pasoActual()?.id).toBe('lexico-abierto');
      });

      it('router a /pronunciar desde lexico-abierto avanza a pronunciar-grabar', async () => {
        const t = crearDesdeLectorInicio();
        const router = TestBed.inject(Router);
        await router.navigateByUrl('/leer/PG11/1');
        t.notificarLector('palabra');
        await router.navigateByUrl('/pronunciar');
        expect(t.pasoActual()?.id).toBe('pronunciar-grabar');
      });

      describe('en pronunciar-grabar', () => {
        async function irAPronunciarGrabar(): Promise<{ t: Tutorial; router: Router }> {
          const t = crearDesdeLectorInicio();
          const router = TestBed.inject(Router);
          await router.navigateByUrl('/leer/PG11/1');
          t.notificarLector('palabra');
          await router.navigateByUrl('/pronunciar');
          return { t, router };
        }

        it('notificarPronunciar se ignora si el tutorial está inactivo', async () => {
          const { t } = await irAPronunciarGrabar();
          t.saltar();
          expect(t.activo()).toBe(false);
          t.notificarPronunciar('resultado');
          expect(t.activo()).toBe(false); // no se reactivó
        });

        it('notificarPronunciar se ignora si el paso actual no es pronunciar-grabar', async () => {
          const { t } = await irAPronunciarGrabar();
          t.atras(); // vuelve a lexico-abierto
          expect(t.pasoActual()?.id).toBe('lexico-abierto');
          t.notificarPronunciar('resultado');
          expect(t.pasoActual()?.id).toBe('lexico-abierto'); // sin cambios
        });

        it('"inicio" limpia el aviso de un intento anterior', async () => {
          const { t } = await irAPronunciarGrabar();
          t.notificarPronunciar('error');
          expect(t.avisoTransitorio()).not.toBeNull();
          t.notificarPronunciar('inicio');
          expect(t.avisoTransitorio()).toBeNull();
        });

        it('"resultado" avanza a pronunciar-resultado', async () => {
          const { t } = await irAPronunciarGrabar();
          t.notificarPronunciar('resultado');
          expect(t.pasoActual()?.id).toBe('pronunciar-resultado');
          expect(t.activo()).toBe(true);
        });

        it('"error" (incluida la rama bloqueada de corregir()) deja el aviso, sin avanzar ni bloquear', async () => {
          const { t } = await irAPronunciarGrabar();
          t.notificarPronunciar('error');
          expect(t.pasoActual()?.id).toBe('pronunciar-grabar');
          expect(t.avisoTransitorio()).toContain('No se pudo completar la corrección');
          expect(t.activo()).toBe(true);
        });
      });

      describe('Continuar leyendo: reconocer el regreso al origen', () => {
        it('con contexto registrado, volver al MISMO libro/capítulo avanza a post-lectura-inicio, sin completar', async () => {
          const t = crearDesdeLectorInicio();
          const router = TestBed.inject(Router);
          await router.navigateByUrl('/leer/PG11/1');
          t.notificarLector('palabra');
          await router.navigateByUrl('/pronunciar');
          t.registrarContextoPronunciar({ id: 'PG11', cap: 1 });
          t.notificarPronunciar('resultado');
          await router.navigateByUrl('/leer/PG11/1');
          expect(t.pasoActual()?.id).toBe('post-lectura-inicio');
          expect(t.pasoActual()?.silencioso).toBe(true);
          expect(t.activo()).toBe(true); // NO completado
        });

        it('volver a OTRO libro/capítulo no cuenta como éxito contextual: no avanza, pero no bloquea la navegación', async () => {
          const t = crearDesdeLectorInicio();
          const router = TestBed.inject(Router);
          await router.navigateByUrl('/leer/PG11/1');
          t.notificarLector('palabra');
          await router.navigateByUrl('/pronunciar');
          t.registrarContextoPronunciar({ id: 'PG11', cap: 1 });
          t.notificarPronunciar('resultado');
          expect(t.pasoActual()?.id).toBe('pronunciar-resultado');
          await router.navigateByUrl('/leer/OTRO-LIBRO/0'); // el usuario decidió leer otra cosa
          expect(router.url).toBe('/leer/OTRO-LIBRO/0'); // la navegación real no se bloqueó
          expect(t.pasoActual()?.id).toBe('pronunciar-resultado'); // el tutorial no lo dio por válido
          expect(t.activo()).toBe(true);
        });

        it('sin contexto registrado (Pronunciar abierto sin libro/cap), cualquier /leer/ vale, como en D1.3', async () => {
          const t = crearDesdeLectorInicio();
          const router = TestBed.inject(Router);
          await router.navigateByUrl('/leer/PG11/1');
          t.notificarLector('palabra');
          await router.navigateByUrl('/pronunciar');
          t.registrarContextoPronunciar(null); // como si hubiera llegado desde la navegación, sin libro
          t.notificarPronunciar('resultado');
          await router.navigateByUrl('/leer/CUALQUIERA/0');
          expect(t.pasoActual()?.id).toBe('post-lectura-inicio');
        });
      });

      it('post-lectura-inicio sobrevive un refresh: sigue activo, no completado', () => {
        localStorage.setItem(CLAVE, JSON.stringify({ version: 1, pasoId: 'post-lectura-inicio', estado: 'activo' }));
        const t = crear();
        expect(t.activo()).toBe(true);
        expect(t.pasoActual()?.id).toBe('post-lectura-inicio');
        expect(t.pasoActual()?.silencioso).toBe(true);
      });
    });
  });
});
