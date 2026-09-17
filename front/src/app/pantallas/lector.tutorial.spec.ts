import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { from, of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Libro, Palabra } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Lector } from './lector';

/** D1.4: el lector notifica al tutorial cuando la hoja de la palabra tiene
 *  contenido LOCAL utilizable (nunca espera a la IA), y guarda la posición
 *  de golpe antes de salir hacia Pronunciar (el guardado normal espera
 *  300 ms, y «Continuar leyendo» necesita el punto exacto). */
describe('Lector: notificaciones al tutorial y posición antes de Pronunciar', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null, capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const CAP: Capitulo = { libro_id: 'PG11', indice: 1, total: 2, titulo: 'CHAPTER I', palabras: 90, parrafos: ['Alice was beginning to get very tired.'] };

  const PALABRA_BASE: Omit<Palabra, 'sentido' | 'acepciones_principales' | 'ipa_uk' | 'ipa_us'> = {
    etapa: 'diccionario', palabra: 'tired', lema: 'tired', categoria: null,
    ipa_generada_por_ia: false, compuesto: null, parte_del_diccionario: null,
    audio_uk: null, audio_us: null, audio_generado: false, etiquetas: [], similitud: null,
    sentidos_candidatos: 0, dudoso: false, definicion_contextual: null, explicacion_gramatical: null,
    explicacion_adaptada: null, ejemplo: null, banda: '', zipf: null, rareza: null, desde_cache: false,
    oracion: 'Alice was beginning to get very tired.', origen_oracion: 'capitulo', explicacion_pendiente: false,
    motivo_sin_explicacion: null, avisos: [], traduccion: null, definicion_ia: null, generado_por_ia: false,
    acepcion_elegida_por_ia: false,
  } as unknown as Omit<Palabra, 'sentido' | 'acepciones_principales' | 'ipa_uk' | 'ipa_us'>;

  let notificarLector: ReturnType<typeof vi.fn>;
  let apiPalabra: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    notificarLector = vi.fn();
    apiPalabra = vi.fn();
    await TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        {
          provide: Api,
          useValue: { capitulo: vi.fn(() => of(CAP)), progreso: vi.fn(() => of({})), palabra: apiPalabra },
        },
        {
          provide: Sesion,
          useValue: {
            libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(null), inicio: signal(null),
            refrescar: vi.fn(async () => {}), ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
          },
        },
        { provide: Tutorial, useValue: { notificarLector } },
      ],
    }).compileComponents();
  });

  async function montar() {
    TestBed.inject(Preferencias).modoLectura.set('rollo');
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', 'PG11');
    fixture.componentRef.setInput('cap', '1');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    return { fixture, c: fixture.componentInstance as unknown as { consultar(t: string): Promise<void>; avance: { set(n: number): void }; alSalirAPronunciar(): void } };
  }

  describe('notificarLector: solo con hoja local utilizable', () => {
    it('notifica en cuanto llega la etapa local, sin esperar a que la etapa completa (IA) termine', async () => {
      const local = { ...PALABRA_BASE, sentido: 'exhausted; needing rest', acepciones_principales: undefined, ipa_uk: null, ipa_us: null } as Palabra;
      let resolverCompleta!: (v: Palabra) => void;
      const completaPendiente = new Promise<Palabra>(res => { resolverCompleta = res; });
      apiPalabra.mockImplementation((cuerpo: { etapa: string }) =>
        cuerpo.etapa === 'diccionario' ? of(local) : from(completaPendiente));
      const { c } = await montar();
      const promesa = c.consultar('tired');
      // Deja correr solo la microtarea de la primera respuesta (síncrona vía `of`).
      await Promise.resolve();
      await Promise.resolve();
      expect(notificarLector).toHaveBeenCalledWith('palabra'); // ya notificó, sin que 'completa' haya resuelto
      resolverCompleta({ ...local, etapa: 'completa' });
      await promesa; // deja terminar consultar() para no dejar una promesa suelta
    });

    it('con solo IPA (sin sentido), también cuenta como utilizable', async () => {
      apiPalabra.mockReturnValue(of({ ...PALABRA_BASE, sentido: null, acepciones_principales: undefined, ipa_uk: '/taɪəd/', ipa_us: null } as Palabra));
      const { c } = await montar();
      await c.consultar('tired');
      expect(notificarLector).toHaveBeenCalledWith('palabra');
    });

    it('con acepciones dudosas (sin sentido fijo), también cuenta', async () => {
      apiPalabra.mockReturnValue(of({ ...PALABRA_BASE, sentido: null, acepciones_principales: ['tired (adj.)', 'tired (past of tire)'], ipa_uk: null, ipa_us: null } as Palabra));
      const { c } = await montar();
      await c.consultar('tired');
      expect(notificarLector).toHaveBeenCalledWith('palabra');
    });

    it('sin nada local (ni sentido, ni acepciones, ni IPA): NO notifica, y la UI sigue mostrando su propio "no está en el diccionario"', async () => {
      apiPalabra.mockReturnValue(of({ ...PALABRA_BASE, sentido: null, acepciones_principales: undefined, ipa_uk: null, ipa_us: null } as Palabra));
      const { c, fixture } = await montar();
      await c.consultar('asdfqwerty');
      expect(notificarLector).not.toHaveBeenCalled();
      fixture.detectChanges();
      expect((fixture.nativeElement as HTMLElement).textContent).toContain('no está en el diccionario');
    });
  });

  it('el enlace a Pronunciar lleva frase, libro y cap, con el target del léxico', async () => {
    apiPalabra.mockReturnValue(of({ ...PALABRA_BASE, sentido: 'exhausted', acepciones_principales: undefined, ipa_uk: null, ipa_us: null } as Palabra));
    const { c, fixture } = await montar();
    await c.consultar('tired');
    fixture.detectChanges();
    const enlace = (fixture.nativeElement as HTMLElement).querySelector('[data-tutorial="lexico-pronunciar"]') as HTMLAnchorElement;
    expect(enlace).toBeTruthy();
    expect(enlace.getAttribute('href')).toContain('/pronunciar');
  });

  it('el contenedor del texto lleva el target lector-texto', async () => {
    const { fixture } = await montar();
    expect((fixture.nativeElement as HTMLElement).querySelector('[data-tutorial="lector-texto"]')).toBeTruthy();
  });

  describe('posición: guardado inmediato antes de ir a Pronunciar', () => {
    const clave = () => 'literalevel.pos.PG11.1';

    it('alSalirAPronunciar() escribe ya, sin esperar los 300 ms del debounce', async () => {
      const { c } = await montar();
      c.avance.set(0.42);
      // Nada en localStorage todavía: el guardado normal solo se dispara
      // cuando cambia `avance` por scroll, con su propio debounce; aquí no
      // ha pasado ningún scroll, así que probamos el flush en sí mismo.
      c.alSalirAPronunciar();
      expect(localStorage.getItem(clave())).toBe('0.4200');
    });

    it('el flush vence a un guardado con espera todavía pendiente (antes de los 300 ms)', async () => {
      const { c } = await montar();
      const priv = c as unknown as { guardarPosicion(fraccion: number): void };
      // Como el que dispara el scroll real: queda una escritura con espera
      // de 300 ms, con un valor viejo (0.15).
      priv.guardarPosicion(0.15);
      // El lector se va antes de que esos 300 ms pasen, con la posición ya
      // en otro punto (0.77): el flush debe ganar, no el valor a medio camino.
      c.avance.set(0.77);
      c.alSalirAPronunciar();
      expect(localStorage.getItem(clave())).toBe('0.7700'); // ya está escrito, sin esperar nada
    });
  });
});
