import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Spotlight } from './spotlight';

/** Overlay del tutorial guiado v2, D1.2: tarjetas de elección, objetivos
 *  reales (D1.1, reutilizado en `nivel-final`), y la píldora no modal de
 *  los pasos silenciosos (checkpoints y el cuestionario de nivel). Nunca a
 *  la vez que Ajustes; siempre se puede cerrar. */
describe('Spotlight (D1.2)', () => {
  @Component({ selector: 'app-falsa', template: '<p>falsa</p>' })
  class Falsa {}

  @Component({ selector: 'app-raiz-prueba', imports: [Spotlight], template: '<app-spotlight />' })
  class Raiz {}

  const CLAVE_DEV = 'literalevel.tutorial-dev';
  const AUTENTICADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: null, openai: true, mensaje: '' };

  beforeEach(() => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    try { localStorage.setItem(CLAVE_DEV, 'on'); } catch { /* sin almacenamiento */ }
    TestBed.configureTestingModule({
      imports: [Raiz],
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

  function montar() {
    const fixture = TestBed.createComponent(Raiz);
    document.body.appendChild(fixture.nativeElement);
    const tutorial = TestBed.inject(Tutorial);
    const sesion = TestBed.inject(Sesion);
    const raiz = fixture.nativeElement as HTMLElement;
    const dialogo = () => raiz.querySelector('[role=dialog]') as HTMLElement | null;
    const pildora = () => raiz.querySelector('.pildora-tutorial') as HTMLElement | null;
    const boton = (texto: string) => [...(dialogo()?.querySelectorAll('button') ?? [])]
      .find(b => b.textContent?.trim().startsWith(texto)) as HTMLButtonElement | undefined;
    const pulsar = (texto: string) => { boton(texto)!.click(); fixture.detectChanges(); };
    return { fixture, tutorial, sesion, raiz, dialogo, pildora, boton, pulsar };
  }

  afterEach(() => {
    document.querySelectorAll('app-raiz-prueba').forEach(n => n.remove());
  });

  it('no muestra nada si el tutorial no está activo', () => {
    const { fixture, dialogo, pildora } = montar();
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
    expect(pildora()).toBeNull();
  });

  it('activarDesarrollo() (la vía real de `?tutorialv2=on`) sin progreso previo: se activa solo y cierra Bienvenida v1, sin «Repetir tutorial» manual', () => {
    const { fixture, tutorial, sesion, dialogo } = montar();
    sesion.bienvenida.set(true); // como llegaría cualquier visitante nuevo
    tutorial.activarDesarrollo();
    fixture.detectChanges();
    expect(tutorial.activo()).toBe(true);
    sesion.entrada.set(AUTENTICADA); // se sabe la sesión: ya hay algo que mostrar
    fixture.detectChanges();
    expect(dialogo()).toBeTruthy(); // Tutorial v2 realmente en pantalla, no solo el flag
    expect(sesion.bienvenida()).toBe(false); // nunca los dos a la vez (D1.1, punto 6)
  });

  it('cuenta-eleccion: tarjeta con sus dos opciones, sin «Siguiente» genérico', () => {
    const { fixture, tutorial, dialogo, boton } = montar();
    tutorial.iniciar(); // sesión desconocida al llegar aquí: queda oculto hasta saberse anónima
    TestBed.inject(Sesion).entrada.set({ puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' });
    fixture.detectChanges();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Ya tienes cuenta?');
    expect(boton('Entrar')).toBeTruthy();
    expect(boton('Continuar sin cuenta')).toBeTruthy();
    expect(boton('Siguiente')).toBeUndefined();
    expect(boton('Terminar')).toBeUndefined();
  });

  it('elegir una opción llama a tutorial.elegir() y la tarjeta pasa al siguiente paso', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué quieres hacer?');
    pulsar('🧠 Practicar');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué practicas hoy?');
  });

  it('«Atrás» solo aparece cuando tutorial.puedeAtras() es verdad', () => {
    const { fixture, tutorial, dialogo, boton, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    expect(boton('Atrás')).toBeUndefined(); // intencion, sin historial
    pulsar('🧠 Practicar');
    expect(boton('Atrás')).toBeTruthy();
    pulsar('Atrás');
    expect(dialogo()?.querySelector('h2')?.textContent).toBe('¿Qué quieres hacer?');
  });

  it('nunca se muestra a la vez que Ajustes', () => {
    const { fixture, tutorial, sesion, dialogo } = montar();
    tutorial.iniciar();
    sesion.entrada.set(AUTENTICADA);
    fixture.detectChanges();
    sesion.ajustesAbiertos.set(true);
    fixture.detectChanges();
    expect(dialogo()).toBeNull();
  });

  it('«Saltar» cierra el tutorial', () => {
    const { fixture, tutorial, dialogo, pulsar } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    pulsar('Saltar');
    expect(tutorial.activo()).toBe(false);
    expect(dialogo()).toBeNull();
  });

  it('Escape cierra el tutorial', () => {
    const { fixture, tutorial, dialogo } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
    fixture.detectChanges();
    expect(tutorial.activo()).toBe(false);
  });

  it('Tab no saca el foco de la tarjeta', () => {
    const { fixture, tutorial, dialogo, boton } = montar();
    tutorial.iniciar();
    TestBed.inject(Sesion).entrada.set(AUTENTICADA);
    fixture.detectChanges();
    const primero = boton('Saltar')!;
    const botones = dialogo()!.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    botones[botones.length - 1].focus();
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }));
    expect(document.activeElement).toBe(primero);
  });

  describe('pasos silenciosos (checkpoints y nivel-inicio): sin tarjeta, con píldora', () => {
    it('nivel-inicio no muestra tarjeta modal, solo la píldora, y no roba el foco', () => {
      const { fixture, tutorial, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      TestBed.inject(Sesion).entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      expect(dialogo()).toBeNull();
      expect(pildora()?.textContent).toContain('Midiendo tu nivel');
      expect(pildora()?.textContent).toContain('Salir');
      // No roba el foco: a diferencia de la tarjeta modal, nada aquí lo mueve.
      expect(pildora()!.contains(document.activeElement)).toBe(false);
    });

    it('«Salir» de la píldora cierra el tutorial igual que «Saltar»', () => {
      const { fixture, tutorial, pildora, pulsar } = montar();
      tutorial.iniciar();
      TestBed.inject(Sesion).entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      const salir = [...pildora()!.querySelectorAll('button')].find(b => b.textContent?.includes('Salir'))!;
      salir.click();
      fixture.detectChanges();
      expect(tutorial.activo()).toBe(false);
    });

    it('un checkpoint (encontrar-inicio) tampoco muestra tarjeta modal, y no bloquea nada', () => {
      const { fixture, tutorial, sesion, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      fixture.detectChanges();
      pulsar('📖 Leer');
      expect(dialogo()).toBeNull();
      expect(pildora()).toBeTruthy();
      expect(tutorial.activo()).toBe(true); // no completado
    });

    it('la píldora desaparece al llegar a nivel-final (deja de ser silencioso)', () => {
      const { fixture, tutorial, sesion, dialogo, pildora, pulsar } = montar();
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      fixture.detectChanges();
      pulsar('🎯 Medir mi nivel');
      expect(pildora()).toBeTruthy();
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      TestBed.tick();
      fixture.detectChanges();
      expect(pildora()).toBeNull();
      expect(dialogo()).toBeTruthy();
    });
  });

  describe('nivel-final: objetivo real, avanza sin «Siguiente»', () => {
    function abrirNivelFinal(fixture: ReturnType<typeof montar>['fixture'], tutorial: Tutorial, sesion: Sesion) {
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      fixture.detectChanges();
      const boton = [...(fixture.nativeElement as HTMLElement).querySelectorAll('button')]
        .find(b => b.textContent?.trim().startsWith('🎯 Medir mi nivel')) as HTMLButtonElement;
      boton.click();
      fixture.detectChanges();
      sesion.perfil.set({
        nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
        nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B2',
      });
      TestBed.tick();
      fixture.detectChanges();
    }

    it('sin el elemento real en pantalla: tarjeta centrada con «Reintentar», nunca «Siguiente»', async () => {
      const { fixture, tutorial, sesion, dialogo, boton } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      await new Promise(r => setTimeout(r, 1700)); // agota el margen de espera del objetivo
      fixture.detectChanges();
      expect(dialogo()?.textContent).toContain('No encuentro esa parte de la pantalla ahora mismo.');
      expect(boton('Reintentar')).toBeTruthy();
      expect(boton('Siguiente')).toBeUndefined();
      expect(boton('Saltar')).toBeTruthy(); // sigue siendo posible cerrarlo
    });

    it('con el elemento real en pantalla, se posiciona sobre él sin esperar', () => {
      const marca = document.createElement('a');
      marca.setAttribute('data-tutorial', 'nivel-ver-libros');
      document.body.appendChild(marca);
      const { fixture, tutorial, sesion, dialogo } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      marca.remove();
    });

    it('avanza hasta encontrar-busqueda cuando el router navega a /encontrar (el clic real en el botón de la app), no por un botón del tutorial', async () => {
      const { fixture, tutorial, sesion } = montar();
      abrirNivelFinal(fixture, tutorial, sesion);
      expect(tutorial.pasoActual()?.id).toBe('nivel-final');
      await TestBed.inject(Router).navigateByUrl('/encontrar');
      // La misma navegación resuelve encontrar-inicio → encontrar-busqueda en cadena (D1.3).
      expect(tutorial.pasoActual()?.id).toBe('encontrar-busqueda');
      expect(tutorial.activo()).toBe(true);
    });
  });

  describe('D1.3: búsqueda y libro', () => {
    const PERFIL = {
      nivel: 1.2, banda: 'intermedio', origen: 'cuestionario' as const, creado: '',
      nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4] as [number, number], cefr: 'B2',
    };

    async function irAEncontrarBusqueda(fixture: ReturnType<typeof montar>['fixture'], tutorial: Tutorial, sesion: Sesion) {
      tutorial.iniciar();
      sesion.entrada.set(AUTENTICADA);
      sesion.perfil.set(PERFIL);
      fixture.detectChanges();
      const leer = [...(fixture.nativeElement as HTMLElement).querySelectorAll('button')]
        .find(b => b.textContent?.trim().startsWith('📖 Leer')) as HTMLButtonElement;
      leer.click();
      fixture.detectChanges();
      await TestBed.inject(Router).navigateByUrl('/encontrar');
      fixture.detectChanges();
    }

    it('encontrar-busqueda: tarjeta apuntando al buscador, sin opciones ni «Siguiente»', async () => {
      const { fixture, tutorial, sesion, dialogo, boton } = montar();
      await irAEncontrarBusqueda(fixture, tutorial, sesion);
      expect(tutorial.pasoActual()?.id).toBe('encontrar-busqueda');
      expect(dialogo()?.querySelector('h2')?.textContent).toBe('Busca algo que te gustaría leer');
      expect(boton('Siguiente')).toBeUndefined();
      expect(boton('Terminar')).toBeUndefined();
    });

    it('el aviso transitorio ("sin resultados"/"error") se muestra bajo la tarjeta cuando existe', async () => {
      const { fixture, tutorial } = montar();
      await irAEncontrarBusqueda(fixture, tutorial, TestBed.inject(Sesion));
      tutorial.notificarBusqueda('sin-resultados');
      fixture.detectChanges();
      expect((fixture.nativeElement as HTMLElement).textContent).toContain('No encontré resultados');
    });

    it('encontrar-resultados: la zona de resultados aparece tarde y el spotlight la encuentra', async () => {
      const { fixture, tutorial, dialogo } = montar();
      const sesion = TestBed.inject(Sesion);
      await irAEncontrarBusqueda(fixture, tutorial, sesion);
      tutorial.notificarBusqueda('con-resultados');
      fixture.detectChanges();
      expect(dialogo()?.classList.contains('centrada')).toBe(true); // todavía buscando la zona

      await new Promise(r => setTimeout(r, 300));
      const zona = document.createElement('div');
      zona.setAttribute('data-tutorial', 'encontrar-resultados');
      document.body.appendChild(zona);
      await new Promise(r => setTimeout(r, 300));
      fixture.detectChanges();

      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      expect(dialogo()?.textContent).toContain('Elige el libro que más te interese');
      zona.remove();
    });

    it('dos o más tarjetas presentes: cualquiera puede navegar y avanzar, no se exige pulsar la primera', async () => {
      const { fixture, tutorial } = montar();
      const sesion = TestBed.inject(Sesion);
      await irAEncontrarBusqueda(fixture, tutorial, sesion);
      tutorial.notificarBusqueda('con-resultados');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('encontrar-resultados');
      // Ni siquiera hace falta que exista la zona en el DOM: lo que demuestra
      // progreso es la navegación real a /libro/:id, sea cual sea la tarjeta.
      await TestBed.inject(Router).navigateByUrl('/libro/SWV99999'); // no la primera tarjeta, una cualquiera
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('libro-ficha');
    });

    it('libro-ficha: no modal, píldora sin foco robado ni clics bloqueados', async () => {
      const { fixture, tutorial, dialogo, pildora } = montar();
      const sesion = TestBed.inject(Sesion);
      await irAEncontrarBusqueda(fixture, tutorial, sesion);
      tutorial.notificarBusqueda('con-resultados');
      await TestBed.inject(Router).navigateByUrl('/libro/PG11');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('libro-ficha');
      expect(dialogo()).toBeNull(); // sin tarjeta modal ni velo
      expect(pildora()?.textContent).toContain('Mira la ficha y abre el libro cuando estés listo');
      expect(pildora()!.contains(document.activeElement)).toBe(false); // no roba el foco
    });

    it('cualquiera de las rutas válidas /leer/:id/:cap avanza hasta lector-palabra (D1.4 le da comportamiento a lector-inicio)', async () => {
      const { fixture, tutorial, dialogo } = montar();
      const sesion = TestBed.inject(Sesion);
      await irAEncontrarBusqueda(fixture, tutorial, sesion);
      tutorial.notificarBusqueda('con-resultados');
      await TestBed.inject(Router).navigateByUrl('/libro/PG11');
      await TestBed.inject(Router).navigateByUrl('/leer/PG11/7'); // capítulo cualquiera, no el 0
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('lector-palabra');
      expect(tutorial.activo()).toBe(true); // NO completado
      expect(dialogo()).toBeTruthy(); // lector-palabra sí muestra tarjeta (con objetivo)
    });
  });

  describe('D1.4: lector, léxico y pronunciar', () => {
    it('lector-palabra: spotlight sobre la región de lectura (lector-texto), sin palabra hardcodeada', async () => {
      const marca = document.createElement('div');
      marca.setAttribute('data-tutorial', 'lector-texto');
      document.body.appendChild(marca);
      localStorage.setItem('literalevel.tutorial-dev', 'on');
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'lector-inicio', estado: 'activo' }));
      const { fixture, tutorial, dialogo } = montar();
      await TestBed.inject(Router).navigateByUrl('/leer/PG11/1');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('lector-palabra');
      expect(dialogo()?.querySelector('h2')?.textContent).toBe('Prueba manteniendo pulsada una palabra');
      expect(dialogo()?.classList.contains('centrada')).toBe(false); // encontró la región
      marca.remove();
    });

    it('lexico-abierto: spotlight sobre el CTA real hacia Pronunciar (lexico-pronunciar)', async () => {
      const marca = document.createElement('a');
      marca.setAttribute('data-tutorial', 'lexico-pronunciar');
      document.body.appendChild(marca);
      localStorage.setItem('literalevel.tutorial-dev', 'on');
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'lector-palabra', estado: 'activo' }));
      const { fixture, tutorial, dialogo } = montar();
      tutorial.notificarLector('palabra');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('lexico-abierto');
      expect(dialogo()?.classList.contains('centrada')).toBe(false);
      marca.remove();
    });

    it('pronunciar-grabar: spotlight sobre pronunciar-practica; el aviso transitorio aparece con el error', async () => {
      const marca = document.createElement('div');
      marca.setAttribute('data-tutorial', 'pronunciar-practica');
      document.body.appendChild(marca);
      localStorage.setItem('literalevel.tutorial-dev', 'on');
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'lexico-abierto', estado: 'activo' }));
      const { fixture, tutorial, dialogo } = montar();
      await TestBed.inject(Router).navigateByUrl('/pronunciar');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('pronunciar-grabar');
      expect(dialogo()?.querySelector('h2')?.textContent).toBe('Grábate y después pide la corrección');
      tutorial.notificarPronunciar('error');
      fixture.detectChanges();
      expect(dialogo()?.textContent).toContain('No se pudo completar la corrección');
      marca.remove();
    });

    it('pronunciar-resultado: tarjeta simple, sin objetivo obligatorio, menciona Escuchar y ver', async () => {
      localStorage.setItem('literalevel.tutorial-dev', 'on');
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'lexico-abierto', estado: 'activo' }));
      const { fixture, tutorial, dialogo } = montar();
      await TestBed.inject(Router).navigateByUrl('/pronunciar');
      tutorial.notificarPronunciar('resultado');
      fixture.detectChanges();
      expect(tutorial.pasoActual()?.id).toBe('pronunciar-resultado');
      expect(dialogo()).toBeTruthy();
      expect(dialogo()?.textContent).toContain('Escuchar y ver');
      // Sin objetivo: no se queda esperando ni pide «Reintentar».
      expect(dialogo()?.textContent).not.toContain('No encuentro esa parte');
    });

    it('post-lectura-inicio → cierre-palabras: checkpoint sin tarjeta, luego tarjeta real, tutorial activo (no completado)', async () => {
      localStorage.setItem('literalevel.tutorial-dev', 'on');
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'lexico-abierto', estado: 'activo' }));
      const { fixture, tutorial, dialogo } = montar();
      await TestBed.inject(Router).navigateByUrl('/pronunciar');
      tutorial.registrarContextoPronunciar({ id: 'PG11', cap: 1 });
      tutorial.notificarPronunciar('resultado');
      await TestBed.inject(Router).navigateByUrl('/leer/PG11/1');
      fixture.detectChanges();
      // La misma navegación resuelve post-lectura-inicio → cierre-palabras (D1.5).
      expect(tutorial.pasoActual()?.id).toBe('cierre-palabras');
      expect(tutorial.activo()).toBe(true); // NO completado
      expect(dialogo()).toBeTruthy(); // cierre-palabras sí muestra tarjeta (opciones)
    });
  });

  describe('D1.5: cierre del onboarding', () => {
    function prepararCierrePalabras() {
      localStorage.setItem('literalevel.tutorial', JSON.stringify({ version: 1, pasoId: 'post-lectura-inicio', estado: 'activo' }));
    }

    async function montarEnCierrePalabras() {
      prepararCierrePalabras();
      const m = montar();
      m.sesion.entrada.set(AUTENTICADA);
      await TestBed.inject(Router).navigateByUrl('/leer/PG11/1');
      m.fixture.detectChanges();
      return m;
    }

    it('cierre-palabras: tarjeta con «Ver mis palabras», sin prometer una palabra concreta', async () => {
      const { dialogo, boton } = await montarEnCierrePalabras();
      expect(dialogo()?.querySelector('h2')?.textContent).toBe('Vuelve a lo que vas aprendiendo');
      expect(dialogo()?.textContent).not.toContain('acabas de consultar');
      expect(boton('Ver mis palabras')).toBeTruthy();
    });

    it('tutorial-final: sin botón «Saltar» (D1.5), con «Terminar tutorial»', async () => {
      const { fixture, dialogo, boton, pulsar } = await montarEnCierrePalabras();
      pulsar('Ver mis palabras');
      await new Promise(r => setTimeout(r, 0));
      fixture.detectChanges();
      expect(dialogo()?.querySelector('h2')?.textContent).toBe('Ya conoces lo esencial de LiteraLevel');
      expect(boton('Saltar')).toBeUndefined(); // ocultado a propósito, único paso sin él
      expect(boton('Terminar tutorial')).toBeTruthy();
    });

    it('Escape no hace nada en tutorial-final (coherente con ocultar Saltar)', async () => {
      const { fixture, tutorial, dialogo, pulsar } = await montarEnCierrePalabras();
      pulsar('Ver mis palabras');
      await new Promise(r => setTimeout(r, 0));
      fixture.detectChanges();
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }));
      fixture.detectChanges();
      expect(tutorial.activo()).toBe(true); // no se saltó
      expect(dialogo()).toBeTruthy();
    });

    it('«Terminar tutorial» completa y se queda en /palabras', async () => {
      const { fixture, tutorial, pulsar } = await montarEnCierrePalabras();
      pulsar('Ver mis palabras');
      await new Promise(r => setTimeout(r, 0));
      fixture.detectChanges();
      const router = TestBed.inject(Router);
      const antes = router.url;
      pulsar('Terminar tutorial');
      expect(tutorial.activo()).toBe(false);
      expect(router.url).toBe(antes);
    });
  });
});
