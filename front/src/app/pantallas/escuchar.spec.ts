import { TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { HttpErrorResponse } from '@angular/common/http';
import { vi } from 'vitest';
import { Api, AudioLectura, Entrada } from '../nucleo/api';
import { Sesion } from '../nucleo/sesion';
import { Escuchar } from './escuchar';

describe('Escuchar libros', () => {
  const fragmento: AudioLectura = {
    libro_id: 'PG11', capitulo: 0, titulo: 'Chapter I', parte: 0, total: 2,
    texto: 'Hello world.', clave: 'a'.repeat(64), guardado: false,
    tope_caracteres: 2400, aproximado: false,
    palabras: [{ texto: 'Hello ', inicio: 0, fin: 1 }, { texto: 'world.', inicio: 1, fin: 2 }],
  };
  let api: any;
  let sesion: any;
  let fixture: ReturnType<typeof TestBed.createComponent<Escuchar>>;
  let componente: Escuchar;

  beforeEach(async () => {
    api = {
      biblioteca: vi.fn(() => of({ libros: [{ id: 'PG11', titulo: 'Alice', capitulo: 0 }] })),
      libro: vi.fn(() => of({ id: 'PG11', titulo: 'Alice', inicial: 0, capitulos: [{ indice: 0, titulo: 'Chapter I' }, { indice: 1, titulo: 'Chapter II' }] })),
      audioLectura: vi.fn((_id, _cap, _parte, generar) => of({ ...fragmento, guardado: !!generar })),
      audioLecturaArchivo: vi.fn(() => of(new Blob(['audio'], { type: 'audio/mpeg' }))),
    };
    sesion = {
      entrada: signal<Entrada>({ puerta: true, dentro: true, openai: true, restantes: 3, nombre: 'lectora', mensaje: '' }),
      inicio: signal(null), abrirPerfil: vi.fn(), refrescar: vi.fn(async () => {}),
    };
    vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:lectura'), revokeObjectURL: vi.fn() }));
    vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
    await TestBed.configureTestingModule({
      imports: [Escuchar], providers: [provideRouter([]), { provide: Api, useValue: api }, { provide: Sesion, useValue: sesion }],
    }).compileComponents();
    fixture = TestBed.createComponent(Escuchar);
    componente = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();
    await vi.waitFor(() => { fixture.detectChanges(); expect(componente.ocupado()).toBe(false); });
  });
  afterEach(() => { fixture.destroy(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

  it('abre la biblioteca y carga texto sin generar audio', () => {
    expect(componente.fragmento()?.texto).toBe('Hello world.');
    expect(api.audioLectura).toHaveBeenCalledWith('PG11', 0, 0);
    expect(api.audioLecturaArchivo).not.toHaveBeenCalled();
    expect(fixture.nativeElement.textContent).toContain('Preparar este fragmento');
  });

  it('solo genera el fragmento pedido y actualiza el cupo', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    expect(api.audioLectura).toHaveBeenLastCalledWith('PG11', 0, 0, true);
    expect(api.audioLecturaArchivo).toHaveBeenCalledWith(fragmento.clave);
    expect(componente.audioUrl()).toBe('blob:lectura');
    expect(sesion.refrescar).toHaveBeenCalledOnce();
  });

  it('el audio guardado funciona incluso sin clave o cupo', async () => {
    componente.fragmento.set({ ...fragmento, guardado: true });
    sesion.entrada.update((e: Entrada) => ({ ...e, openai: false, restantes: 0 }));
    const llamadas = api.audioLectura.mock.calls.length;
    await componente.escuchar();
    expect(api.audioLectura.mock.calls).toHaveLength(llamadas);
    expect(componente.audioUrl()).toBe('blob:lectura');
    expect(sesion.refrescar).not.toHaveBeenCalled();
  });

  it('al avanzar libera el audio y no prepara el siguiente automáticamente', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    await componente.mover(1);
    expect(api.audioLectura).toHaveBeenLastCalledWith('PG11', 0, 1);
    expect(componente.audioUrl()).toBe('');
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:lectura');
  });

  it('sigue tiempos, retrocesos y velocidad del reproductor', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    const audio = componente.reproductor()!.nativeElement;
    audio.currentTime = 1.4;
    componente.sincronizar();
    fixture.detectChanges();
    expect(componente.activa()).toBe(1);
    expect(fixture.nativeElement.querySelector('.actual').textContent).toBe('world.');
    audio.currentTime = .4;
    componente.cambiarVelocidad(.75);
    fixture.detectChanges();
    expect(componente.activa()).toBe(0);
    expect(audio.playbackRate).toBe(.75);
    componente.terminar();
    expect(componente.activa()).toBe(2);
    expect(componente.finalizado()).toBe(true);
  });

  it('sin marcas utiliza la duración real y no pide más audio', async () => {
    componente.fragmento.set({ ...fragmento, guardado: true, palabras: [], aproximado: true });
    await componente.escuchar();
    fixture.detectChanges();
    const audio = componente.reproductor()!.nativeElement;
    Object.defineProperty(audio, 'duration', { configurable: true, value: 2 });
    audio.currentTime = 1.5;
    componente.sincronizar();
    expect(componente.activa()).toBe(1);
    expect(fixture.nativeElement.textContent).toContain('resaltado es aproximado');
  });

  it('el reproductor propio permite reproducir, pausar y repetir el audio terminado', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    const audio = componente.reproductor()!.nativeElement;
    let pausado = true;
    Object.defineProperty(audio, 'paused', { configurable: true, get: () => pausado });
    Object.defineProperty(audio, 'duration', { configurable: true, value: 144 });
    const play = vi.spyOn(audio, 'play').mockImplementation(async () => { pausado = false; audio.dispatchEvent(new Event('play')); });
    const pause = vi.spyOn(audio, 'pause').mockImplementation(() => { pausado = true; audio.dispatchEvent(new Event('pause')); });
    audio.dispatchEvent(new Event('loadedmetadata'));
    fixture.detectChanges();
    expect(audio.controls).toBe(false);
    expect(fixture.nativeElement.textContent).toContain('2:24');
    fixture.nativeElement.querySelector('[aria-label="Reproducir audio"]').click();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(play).toHaveBeenCalledOnce();
    expect(componente.reproduciendo()).toBe(true);
    fixture.nativeElement.querySelector('[aria-label="Pausar audio"]').click();
    expect(pause).toHaveBeenCalledOnce();
    expect(componente.reproduciendo()).toBe(false);
    audio.currentTime = 144;
    audio.dispatchEvent(new Event('ended'));
    await componente.alternar();
    expect(audio.currentTime).toBe(0);
    expect(componente.finalizado()).toBe(false);
    expect(play).toHaveBeenCalledTimes(2);
    expect(api.audioLecturaArchivo).toHaveBeenCalledOnce();
  });

  it('la barra de progreso y los saltos actualizan la guía sin pedir más audio', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    const audio = componente.reproductor()!.nativeElement;
    Object.defineProperty(audio, 'duration', { configurable: true, value: 2 });
    audio.dispatchEvent(new Event('loadedmetadata'));
    fixture.detectChanges();
    const progreso = fixture.nativeElement.querySelector('[aria-label="Posición del audio"]');
    progreso.value = '1.4';
    progreso.dispatchEvent(new Event('input'));
    expect(audio.currentTime).toBe(1.4);
    expect(componente.activa()).toBe(1);
    fixture.nativeElement.querySelector('[aria-label="Retroceder 10 segundos"]').click();
    expect(audio.currentTime).toBe(0);
    expect(componente.activa()).toBe(0);
    fixture.nativeElement.querySelector('[aria-label="Avanzar 10 segundos"]').click();
    expect(audio.currentTime).toBe(2);
    expect(api.audioLecturaArchivo).toHaveBeenCalledOnce();
    expect(api.audioLectura.mock.calls.filter((llamada: any[]) => llamada[3])).toHaveLength(1);
  });

  it('si el navegador rechaza reproducir permite reintentar sin regenerar', async () => {
    await componente.escuchar();
    fixture.detectChanges();
    const audio = componente.reproductor()!.nativeElement;
    vi.spyOn(audio, 'play').mockRejectedValueOnce(new DOMException('Bloqueado', 'NotAllowedError'));
    await componente.alternar();
    expect(componente.aviso()).toContain('Pulsa reproducir');
    expect(componente.iniciando()).toBe(false);
    expect(componente.audioUrl()).toBe('blob:lectura');
    expect(api.audioLecturaArchivo).toHaveBeenCalledOnce();
    await componente.mover(1);
    expect(componente.tiempo()).toBe(0);
    expect(componente.duracion()).toBe(0);
    expect(componente.reproduciendo()).toBe(false);
  });

  it('si falla la generación muestra el motivo y refresca el cupo', async () => {
    api.audioLectura.mockReturnValue(throwError(() => new HttpErrorResponse({ status: 403, error: { detail: 'Sin cupo' } })));
    await componente.escuchar();
    expect(componente.aviso()).toBe('Sin cupo');
    expect(api.audioLecturaArchivo).not.toHaveBeenCalled();
    expect(sesion.refrescar).toHaveBeenCalled();
  });

  it('descarta una respuesta de generación cuando se cierra la pantalla', async () => {
    const pendiente = new Subject<AudioLectura>();
    api.audioLectura.mockReturnValue(pendiente);
    const trabajo = componente.escuchar();
    componente.ngOnDestroy();
    pendiente.next({ ...fragmento, guardado: true });
    await trabajo;
    expect(api.audioLecturaArchivo).not.toHaveBeenCalled();
  });

  it('sin cuenta ofrece entrar y no ofrece preparar audio', async () => {
    sesion.entrada.set({ puerta: true, dentro: false, openai: true, restantes: null, nombre: null, mensaje: '' });
    fixture.detectChanges();
    await fixture.whenStable();
    await vi.waitFor(() => { fixture.detectChanges(); expect(componente.ocupado()).toBe(false); });
    expect(fixture.nativeElement.textContent).toContain('Entra con tu cuenta');
    expect(fixture.nativeElement.textContent).not.toContain('Preparar este fragmento');
    expect(componente.puedeGenerar()).toBe(false);
  });
});
