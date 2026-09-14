import { TestBed } from '@angular/core/testing';
import { Portada } from './portada';

/** Punto 3: si la API trae `portada_ia`, se enseña la ilustración con su aviso;
 *  si no, o si la imagen no carga, la portada tipográfica. */
describe('Portada por IA', () => {
  async function montar(ia: string | null, compacta: boolean) {
    await TestBed.configureTestingModule({ imports: [Portada] }).compileComponents();
    const f = TestBed.createComponent(Portada);
    f.componentRef.setInput('id', 'PG1661');
    f.componentRef.setInput('titulo', 'The Adventures of Sherlock Holmes');
    f.componentRef.setInput('temas', ['Detective and mystery stories']);
    f.componentRef.setInput('ia', ia);
    f.componentRef.setInput('compacta', compacta);
    f.detectChanges();
    await f.whenStable();
    return f;
  }

  it('sin portada por IA, la tipográfica y ningún aviso', async () => {
    const f = await montar(null, false);
    const raiz = f.nativeElement as HTMLElement;
    expect(raiz.querySelector('img')).toBeNull();
    expect(raiz.querySelector('svg.motivo')).not.toBeNull();
    expect(raiz.textContent).not.toContain('IA');
  });

  it('con portada por IA, la imagen y «Portada generada por IA, no oficial», también en la tarjeta', async () => {
    const f = await montar('/api/portadas/PG1661.webp?v=1-2', false);
    const raiz = f.nativeElement as HTMLElement;
    expect(raiz.querySelector('img.ilustracion')?.getAttribute('src')).toContain('/api/portadas/PG1661.webp?v=1-2');
    expect(raiz.querySelector('svg.motivo')).toBeNull();
    expect(raiz.querySelector('.aviso-ia')?.textContent?.trim()).toBe('Portada generada por IA, no oficial');

    f.componentRef.setInput('compacta', true);
    f.detectChanges();
    expect(raiz.querySelector('.aviso-ia')?.textContent).toContain('portada generada por IA, no oficial');

    // Si la imagen no carga, vuelve la tipográfica.
    raiz.querySelector('img.ilustracion')!.dispatchEvent(new Event('error'));
    f.detectChanges();
    expect(raiz.querySelector('img')).toBeNull();
    expect(raiz.querySelector('svg.motivo')).not.toBeNull();
  });
});
