import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { throwError, of } from 'rxjs';
import { vi } from 'vitest';
import { Api, Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Tutorial } from '../nucleo/tutorial';
import { Pronunciar } from './pronunciar';

/** D1.4: Pronunciar notifica al tutorial al empezar/terminar una corrección
 *  (nunca al revés), y «Continuar leyendo»/«Volver al libro» usa `contexto()`
 *  — la misma fuente que ya usaba `traerFrase()`, sin otra paralela. */
describe('Pronunciar: notificaciones al tutorial y regreso contextual', () => {
  const AUTENTICADA: Entrada = { puerta: true, dentro: true, nombre: 'miguel', restantes: 5, openai: true, mensaje: '' };
  const RESULTADO_OK = {
    puntuacion: 88, transcripcion_ok: true, transcripcion: 'tired', palabras: [{ palabra: 'tired', bien: true }],
    entendidas: [] as [string, string][], resumen: null, detalles: [], audio_correcto: null, restantes: 4, ritmo: null,
  };

  let notificarPronunciar: ReturnType<typeof vi.fn>;
  let registrarContextoPronunciar: ReturnType<typeof vi.fn>;
  let notificarDisponibilidadCorregir: ReturnType<typeof vi.fn>;
  let notificarGrabacionLista: ReturnType<typeof vi.fn>;
  let apiPracticar: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    notificarPronunciar = vi.fn();
    registrarContextoPronunciar = vi.fn();
    notificarDisponibilidadCorregir = vi.fn();
    notificarGrabacionLista = vi.fn();
    apiPracticar = vi.fn();
    await TestBed.configureTestingModule({
      imports: [Pronunciar],
      providers: [
        provideRouter([]),
        {
          provide: Api,
          useValue: {
            frase: vi.fn(() => of({ frase: null })),
            practicar: apiPracticar,
            fonemas: vi.fn(() => of({})),
            debiles: vi.fn(() => of({ palabras: [], aviso: null })),
          },
        },
        {
          provide: Sesion,
          useValue: {
            entrada: signal<Entrada | null>(AUTENTICADA), perfil: signal(null), inicio: signal(null),
            ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
          },
        },
        { provide: Tutorial, useValue: { notificarPronunciar, registrarContextoPronunciar, notificarDisponibilidadCorregir, notificarGrabacionLista } },
      ],
    }).compileComponents();
  });

  async function montar(libro?: string, cap?: string) {
    const fixture = TestBed.createComponent(Pronunciar);
    if (libro !== undefined) fixture.componentRef.setInput('libro', libro);
    if (cap !== undefined) fixture.componentRef.setInput('cap', cap);
    document.body.appendChild(fixture.nativeElement);
    fixture.detectChanges();
    await fixture.whenStable();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const c = fixture.componentInstance as any;
    return { fixture, c, raiz: fixture.nativeElement as HTMLElement };
  }

  it('ngOnInit registra el contexto (libro/cap) en el Tutorial, con la misma fuente que ya usa traerFrase()', async () => {
    const { c } = await montar('PG11', '3');
    expect(registrarContextoPronunciar).toHaveBeenCalledWith({ id: 'PG11', cap: 3 });
    void c;
  });

  it('sin libro/cap, registra null: Pronunciar sin contexto sigue funcionando como antes', async () => {
    await montar();
    expect(registrarContextoPronunciar).toHaveBeenCalledWith(null);
  });

  describe('corregir(): notifica inicio/resultado/error', () => {
    async function prepararGrabacion(c: { frase: string; blob: unknown }) {
      c.frase = 'Don\'t you want to come with us?';
      c.blob = new Blob(['audio'], { type: 'audio/webm' });
    }

    it('éxito: notifica "inicio" y luego "resultado"', async () => {
      apiPracticar.mockReturnValue(of(RESULTADO_OK));
      const { c } = await montar('PG11', '3');
      await prepararGrabacion(c);
      await c.corregir();
      expect(notificarPronunciar.mock.calls.map((a: unknown[]) => a[0])).toEqual(['inicio', 'resultado']);
    });

    it('error de backend/red: notifica "inicio" y luego "error", sin bloquear nada', async () => {
      apiPracticar.mockReturnValue(throwError(() => new Error('sin red')));
      const { c } = await montar('PG11', '3');
      await prepararGrabacion(c);
      await c.corregir();
      expect(notificarPronunciar.mock.calls.map((a: unknown[]) => a[0])).toEqual(['inicio', 'error']);
    });

    it('bloqueada (sin cuenta): notifica "error" directamente, sin llamar a la API', async () => {
      TestBed.overrideProvider(Sesion, {
        useValue: {
          entrada: signal<Entrada | null>({ puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' }),
          perfil: signal(null), inicio: signal(null), ajustesAbiertos: signal(false), abrirPerfil: vi.fn(),
        },
      });
      const { c } = await montar('PG11', '3');
      await prepararGrabacion(c);
      await c.corregir();
      expect(apiPracticar).not.toHaveBeenCalled();
      expect(notificarPronunciar).toHaveBeenCalledWith('error');
    });
  });

  describe('Continuar leyendo / Volver al libro', () => {
    it('con contexto {id, cap}: muestra «Continuar leyendo» hacia /leer/:id/:cap', async () => {
      const { raiz } = await montar('PG11', '3');
      const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.trim() === 'Continuar leyendo') as HTMLAnchorElement;
      expect(enlace).toBeTruthy();
      expect(enlace.getAttribute('href')).toBe('/leer/PG11/3');
      expect(raiz.textContent).not.toContain('Volver al libro');
    });

    it('sin contexto: conserva «Volver al libro» genérico', async () => {
      const { raiz } = await montar();
      const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.trim() === 'Volver al libro') as HTMLAnchorElement;
      expect(enlace).toBeTruthy();
      expect(enlace.getAttribute('href')).toBe('/leer');
      expect(raiz.textContent).not.toContain('Continuar leyendo');
    });
  });
});
