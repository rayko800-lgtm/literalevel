import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { Api, EntradaBiblioteca, Inicio as InicioApi, Perfil } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Inicio } from './inicio';

/** D2: `sesion.inicio()?.seguir` ya alimentaba «Donde lo dejaste». D3.1
 *  (Miguel): Inicio evoluciona a «Mi espacio» cuando hay historial real
 *  (libros, consultas o un nivel ya medido) — sin pantalla `/espacio`
 *  nueva, sin quinta pestaña. Sin historial, se conserva la puerta de
 *  siempre (presentación + puertas + cómo funciona), sin dashboard vacío. */
describe('Inicio: Mi espacio (D3.1) y CTA de continuar leyendo', () => {
  const SEGUIR: EntradaBiblioteca = {
    id: 'PG11', titulo: 'Alice in Wonderland', autor: 'Lewis Carroll',
    capitulo: 3, capitulos: 12, avance: 0.273, palabras: 500, visto: '', consultadas: 2,
    titulo_capitulo: 'CHAPTER IV', extracto: 'Down, down, down.',
  };
  const PERFIL: Perfil = {
    nivel: 1.2, banda: 'intermedio', origen: 'cuestionario', creado: '',
    nombre: '', objetivo: 1.2, rango_recomendado: [1, 1.4], cefr: 'B1',
  };
  const inicioBase = (over: Partial<InicioApi> = {}): InicioApi => ({
    perfil: null, seguir: null, libros: 0, cuaderno: { consultas: 0, palabras: 0, libros: 0 },
    entrada: { puerta: true, dentro: false, nombre: null, restantes: null, openai: true, mensaje: '' },
    ...over,
  });

  let apiFalladas: ReturnType<typeof vi.fn>;

  function proveer(inicio: ReturnType<typeof signal<InicioApi | null>>, perfil: Perfil | null = null) {
    apiFalladas = vi.fn(() => of({ palabras: [] }));
    return TestBed.configureTestingModule({
      imports: [Inicio],
      providers: [
        provideRouter([]),
        { provide: Api, useValue: { falladas: apiFalladas } },
        {
          provide: Sesion,
          useValue: {
            inicio, perfil: signal(perfil), bienvenida: signal(false), ajustesAbiertos: signal(false),
            entrada: signal(null), motor: signal('listo'), sesionFallida: signal(false),
            refrescar: vi.fn(async () => {}),
          },
        },
      ],
    }).compileComponents();
  }

  function montar() {
    const fixture = TestBed.createComponent(Inicio);
    fixture.detectChanges();
    return { fixture, raiz: fixture.nativeElement as HTMLElement };
  }

  describe('lector nuevo / sin historial: la puerta de siempre, nunca un dashboard vacío', () => {
    it('sin seguir, sin libros, sin consultas, sin perfil: presentación + puertas + cómo funciona', async () => {
      await proveer(signal(inicioBase()));
      const { raiz } = montar();
      expect(raiz.querySelector('.cabecera-espacio')).toBeNull();
      expect(raiz.querySelector('.rejilla-espacio')).toBeNull();
      expect(raiz.textContent).toContain('Libros de verdad en inglés');
      expect(raiz.textContent).toContain('Cómo funciona');
      const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.includes('Empezar a leer')) as HTMLAnchorElement;
      expect(enlace).toBeTruthy();
      expect(enlace.getAttribute('href')).toBe('/leer/PG11/auto');
    });

    it('inicio() todavía null (sesión no ha llegado): la puerta de siempre, sin CTA roto, sin excepción', async () => {
      await proveer(signal(null));
      const { raiz } = montar();
      expect(raiz.querySelector('.cabecera-espacio')).toBeNull();
      const enlace = [...raiz.querySelectorAll('a')].find(a => a.textContent?.includes('Empezar a leer')) as HTMLAnchorElement;
      expect(enlace).toBeTruthy();
    });
  });

  describe('lector recurrente: Mi espacio', () => {
    it('con libro en curso: cabecera «Mi espacio» y tarjeta «Donde lo dejaste» con datos reales', async () => {
      await proveer(signal(inicioBase({ seguir: SEGUIR, libros: 1, cuaderno: { consultas: 2, palabras: 2, libros: 1 } })));
      const { raiz } = montar();
      expect(raiz.querySelector('.cabecera-espacio')).toBeTruthy();
      const tarjeta = raiz.querySelector('.tarjeta.seguir') as HTMLElement;
      expect(tarjeta).toBeTruthy();
      expect(tarjeta.textContent).toContain('Alice in Wonderland');
      expect(tarjeta.textContent).toContain('Capítulo 4 de 12'); // capitulo es 0-index
      expect(tarjeta.textContent).toContain('27%'); // 0.273 → Math.round(27.3) = 27
      expect(tarjeta.getAttribute('href')).toBe('/leer/PG11/3'); // la tarjeta entera es el enlace
    });

    it('con libros/palabras: la rejilla muestra los conteos reales y enlaza a las pantallas correctas', async () => {
      await proveer(signal(inicioBase({
        libros: 3, cuaderno: { consultas: 12, palabras: 7, libros: 3 },
      })));
      const { raiz } = montar();
      const tarjetas = [...raiz.querySelectorAll<HTMLAnchorElement>('.tarjeta-mini')];
      const libros = tarjetas.find(t => t.textContent?.includes('3') && t.textContent.includes('libro'));
      expect(libros).toBeTruthy();
      expect(libros!.getAttribute('href')).toContain('/encontrar');
      const palabras = tarjetas.find(t => t.textContent?.includes('7') && t.textContent.includes('palabra'));
      expect(palabras).toBeTruthy();
      expect(palabras!.getAttribute('href')).toBe('/palabras');
    });

    it('el CTA «Repasar» de Mi espacio lleva directo a /repasar (D3.2), no a /palabras', async () => {
      await proveer(signal(inicioBase({ libros: 1, cuaderno: { consultas: 1, palabras: 1, libros: 1 } })));
      const { raiz } = montar();
      const tarjetas = [...raiz.querySelectorAll<HTMLAnchorElement>('.tarjeta-mini')];
      const repasar = tarjetas.find(t => t.textContent?.includes('Repasar'));
      expect(repasar).toBeTruthy();
      expect(repasar!.getAttribute('href')).toBe('/repasar');
    });

    it('solo con perfil medido (sin libros ni consultas): ya es Mi espacio, con CTA de empty state en cada tarjeta', async () => {
      await proveer(signal(inicioBase({ perfil: PERFIL })), PERFIL);
      const { raiz } = montar();
      expect(raiz.querySelector('.cabecera-espacio')).toBeTruthy(); // el perfil solo ya activa el modo
      expect(raiz.textContent).toContain('Encuentra tu primera lectura');
      expect(raiz.textContent).toContain('Consulta palabras mientras lees');
      expect(raiz.textContent).toContain('Aparece en cuanto consultes algo');
      const nivel = raiz.querySelector('.tarjeta-mini.ancho') as HTMLElement;
      expect(nivel.textContent).toContain('1,20'); // num(p.nivel), el mismo formato que ya usaba «puertas»
    });

    it('sin perfil medido: la tarjeta de nivel ofrece medir, no un dato vacío', async () => {
      await proveer(signal(inicioBase({ libros: 1, cuaderno: { consultas: 1, palabras: 1, libros: 1 } })));
      const { raiz } = montar();
      const nivel = raiz.querySelector('.tarjeta-mini.ancho') as HTMLElement;
      expect(nivel.textContent).toContain('Mi nivel');
      expect(nivel.textContent).toContain('Medir mi nivel');
    });

    it('pronunciación: pide /api/voz/falladas solo en modo Mi espacio, y muestra el conteo real', async () => {
      await proveer(signal(inicioBase({ libros: 1, cuaderno: { consultas: 1, palabras: 1, libros: 1 } })));
      apiFalladas.mockReturnValue(of({ palabras: [{ palabra: 'tired', fallos: 3, ultima_vez: null, frase: null }] }));
      const { fixture, raiz } = montar();
      await fixture.whenStable();
      fixture.detectChanges();
      expect(apiFalladas).toHaveBeenCalled();
      const tarjetas = [...raiz.querySelectorAll('.tarjeta-mini')];
      const pron = tarjetas.find(t => t.textContent?.includes('para practicar'));
      expect(pron?.textContent).toContain('1');
    });

    it('sin historial (modo puerta): no pide /api/voz/falladas — nada de llamadas innecesarias', async () => {
      await proveer(signal(inicioBase()));
      const { fixture } = montar();
      await fixture.whenStable();
      fixture.detectChanges();
      expect(apiFalladas).not.toHaveBeenCalled();
    });

    it('una fuente falla (falladas() con error): el resto de Mi espacio se muestra igual', async () => {
      await proveer(signal(inicioBase({ libros: 1, cuaderno: { consultas: 1, palabras: 1, libros: 1 } })));
      apiFalladas.mockReturnValue(throwError(() => new Error('sin red')));
      const { fixture, raiz } = montar();
      await fixture.whenStable();
      fixture.detectChanges();
      expect(raiz.querySelector('.cabecera-espacio')).toBeTruthy();
      expect(raiz.querySelectorAll('.tarjeta-mini').length).toBeGreaterThan(0);
    });
  });
});
