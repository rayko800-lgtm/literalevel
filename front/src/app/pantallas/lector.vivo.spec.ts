import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Capitulo, Entrada, Libro } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { LECTURA_VIVO_CERRADA } from '../compartido/lectura-vivo/lectura-vivo';
import { Lector } from './lector';

/** Demo grabada del 4 oct: en el lector seguía el botón «Leer en voz alta (en vivo)» y, al pulsarlo,
 *  la hoja decía «No se pudo · La lectura en vivo está temporalmente desactivada» (cerrada por
 *  seguridad el 1 oct). Mientras siga cerrada el botón no se enseña, ni con una cuenta con OpenAI
 *  dentro de la puerta y un navegador con WebRTC y micrófono, que es cuando antes aparecía. */
describe('Lector: la lectura en vivo cerrada no enseña su botón', () => {
  const LIBRO: Libro = {
    id: 'PG11', titulo: 'Alice', autor: 'Carroll', palabras: 100, inicial: 1, dificultad: null, cefr: null,
    fuente_dificultad: null, capitulos: [{ indice: 0, titulo: 'Portada', palabras: 10 }, { indice: 1, titulo: 'CHAPTER I', palabras: 90 }],
    ficha: null, sugeridos: [], sinopsis: null,
  };
  const CAP: Capitulo = { libro_id: 'PG11', indice: 1, total: 2, titulo: 'CHAPTER I', palabras: 90, parrafos: ['Alice was beginning to get very tired.'] };
  const ENTRADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: 98, openai: true, mensaje: '' };
  const mediaDevicesOriginal = Object.getOwnPropertyDescriptor(Navigator.prototype, 'mediaDevices');

  beforeEach(async () => {
    try { localStorage.clear(); } catch { /* sin almacenamiento */ }
    vi.stubGlobal('RTCPeerConnection', class {});
    Object.defineProperty(navigator, 'mediaDevices', { value: { getUserMedia: vi.fn() }, configurable: true });
    await TestBed.configureTestingModule({
      imports: [Lector],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { capitulo: vi.fn(() => of(CAP)), progreso: vi.fn(() => of({})) } },
        { provide: Sesion, useValue: { libro: vi.fn(async () => LIBRO), perfil: signal(null), entrada: signal(ENTRADA), inicio: signal(null),
          refrescar: vi.fn(async () => {}), ajustesAbiertos: signal(false), abrirPerfil: vi.fn() } },
      ],
    }).compileComponents();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    if (mediaDevicesOriginal) Object.defineProperty(Navigator.prototype, 'mediaDevices', mediaDevicesOriginal);
    else delete (navigator as unknown as { mediaDevices?: unknown }).mediaDevices;
  });

  it('con cuenta, OpenAI, WebRTC y micrófono el botón no está mientras la función siga cerrada', async () => {
    expect(LECTURA_VIVO_CERRADA).toBe(true);
    const fixture = TestBed.createComponent(Lector);
    fixture.componentRef.setInput('id', 'PG11');
    fixture.componentRef.setInput('cap', '1');
    fixture.detectChanges();
    for (let i = 0; i < 4; i++) { await fixture.whenStable(); fixture.detectChanges(); }
    const raiz = fixture.nativeElement as HTMLElement;
    // El capítulo está y las condiciones de antes se cumplen...
    expect(raiz.textContent).toContain('Alice was beginning');
    expect(typeof RTCPeerConnection).not.toBe('undefined');
    expect(navigator.mediaDevices?.getUserMedia).toBeTruthy();
    // ...y aun así no hay botón que lleve a «No se pudo».
    expect(raiz.querySelector('.leer-vivo')).toBeNull();
    expect(raiz.textContent).not.toContain('Leer en voz alta (en vivo)');
  });
});
