import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Entrada, Libro, Palabra } from '../nucleo/api';
import { Preferencias } from '../nucleo/preferencias';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Lector } from './lector';

/** UX-F1 (Miguel, tras D3.V): sin perfil, pulsar «Consultar» ya mostraba una
 *  tarjeta explicando que la explicación de contexto necesita perfil, pero
 *  solo al llegar la respuesta de la etapa completa — el clic en sí no daba
 *  feedback. Ahora un toast breve aparece al instante, sin esperar red, sin
 *  bloquear nada ni cambiar el contrato de cuenta/OpenAI. */
describe('Lector: feedback inmediato al consultar sin perfil (UX-F1)', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null, capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const CAP: Capitulo = { libro_id: 'PG11', indice: 1, total: 2, titulo: 'CHAPTER I', palabras: 90, parrafos: ['Texto.'] };
  const PALABRA_DICCIONARIO: Palabra = {
    etapa: 'diccionario', palabra: 'tired', lema: 'tired', categoria: 'adjective',
    ipa_uk: '/taɪəd/', ipa_us: null, ipa_generada_por_ia: false, compuesto: null, parte_del_diccionario: null,
    audio_uk: null, audio_us: null, audio_generado: false, sentido: 'cansada, agotada', etiquetas: [],
    similitud: null, sentidos_candidatos: 1, dudoso: false, definicion_contextual: null, explicacion_gramatical: null,
    explicacion_adaptada: null, ejemplo: null, explicacion_pendiente: true,
  } as unknown as Palabra;
  const PALABRA_COMPLETA_SIN_PERFIL: Palabra = {
    ...PALABRA_DICCIONARIO, explicacion_pendiente: false,
    motivo_sin_explicacion: 'La explicación de contexto necesita tu perfil.',
    avisos: ['La explicación de contexto necesita tu perfil.'],
  } as unknown as Palabra;
  const ANONIMA: Entrada = { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' };
  const AUTENTICADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: 5, openai: true, mensaje: '' };

  let apiPalabra: ReturnType<typeof vi.fn>;

  function proveer(entrada: Entrada) {
    apiPalabra = vi.fn((cuerpo: { etapa: string }) =>
      of(cuerpo.etapa === 'diccionario' ? PALABRA_DICCIONARIO : PALABRA_COMPLETA_SIN_PERFIL));
    return TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { capitulo: vi.fn(() => of(CAP)), progreso: vi.fn(() => of({})), palabra: apiPalabra } },
        {
          provide: Sesion,
          useValue: {
            libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(entrada), inicio: signal(null),
            refrescar: vi.fn(async () => {}), ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
          },
        },
        { provide: Tutorial, useValue: { notificarLector: vi.fn() } },
      ],
    }).compileComponents();
  }

  async function montar() {
    TestBed.inject(Preferencias).modoLectura.set('rollo');
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', 'PG11');
    fixture.componentRef.setInput('cap', '1');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    return { fixture, raiz: fixture.nativeElement as HTMLElement, c: fixture.componentInstance as unknown as { consultar(t: string): Promise<void> } };
  }

  it('anónimo + Consultar: el toast aparece al instante, antes de que resuelva la red', async () => {
    await proveer(ANONIMA);
    const { fixture, raiz, c } = await montar();
    const promesa = c.consultar('tired');
    fixture.detectChanges(); // sin esperar ningún await: debe estar ya visible
    const toast = raiz.querySelector('.toast-perfil');
    expect(toast).toBeTruthy();
    expect(toast!.textContent).toContain('Para la explicación contextual, entra con tu perfil.');
    expect(toast!.textContent).toContain('El diccionario sigue disponible sin cuenta.');
    expect(toast!.querySelector('button')?.textContent).toContain('Entrar');
    await promesa;
  });

  it('usuario con perfil (autenticado): comportamiento normal, sin toast', async () => {
    await proveer(AUTENTICADA);
    const { fixture, raiz, c } = await montar();
    await c.consultar('tired');
    fixture.detectChanges();
    expect(raiz.querySelector('.toast-perfil')).toBeNull();
  });

  it('sin cuenta, el diccionario local sigue disponible: la hoja muestra el sentido igual', async () => {
    await proveer(ANONIMA);
    const { fixture, raiz, c } = await montar();
    await c.consultar('tired');
    fixture.detectChanges();
    expect(raiz.textContent).toContain('cansada, agotada');
  });
});
