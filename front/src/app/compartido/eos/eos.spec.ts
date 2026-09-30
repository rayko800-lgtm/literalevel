import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { Eos } from './eos';

describe('Velocidad de Eos', () => {
  afterEach(() => vi.restoreAllMocks());
  it('cambia la velocidad de un vídeo sin reiniciarlo ni volver a cargarlo', async () => {
    const load = vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => {});
    vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
    await TestBed.configureTestingModule({ imports: [Eos] }).compileComponents();
    const fixture = TestBed.createComponent(Eos);
    fixture.componentRef.setInput('src', 'eos/ga/0061.mp4'); fixture.componentRef.setInput('velocidad', .83);
    fixture.detectChanges(); await fixture.whenStable();
    const video = fixture.nativeElement.querySelector('video') as HTMLVideoElement;
    expect(video.playbackRate).toBe(.83); video.currentTime = 1.2;
    const cargas = load.mock.calls.length;
    fixture.nativeElement.querySelector('.disparador-velocidad').click(); fixture.detectChanges();
    const barra = fixture.nativeElement.querySelector('input') as HTMLInputElement;
    barra.value = '1.37'; barra.dispatchEvent(new Event('input')); fixture.detectChanges();
    expect(video.playbackRate).toBe(1.37); expect(video.currentTime).toBe(1.2);
    expect(video.preservesPitch).toBe(true); expect(load.mock.calls.length).toBe(cargas);
    fixture.componentRef.setInput('velocidad', 2); fixture.detectChanges();
    expect(video.playbackRate).toBe(2); expect(load.mock.calls.length).toBe(cargas);
    fixture.destroy();
  });
});
