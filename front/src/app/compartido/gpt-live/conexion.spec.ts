import { afterEach, describe, expect, it, vi } from 'vitest';
import { ConexionLive } from './conexion';

function preparada() {
  const audio = { pause: vi.fn(), srcObject: null } as unknown as HTMLAudioElement;
  const eventos = { alEmpezar: vi.fn(), alDelta: vi.fn(), alCerrar: vi.fn(),
    alIncompleto: vi.fn(), alError: vi.fn() };
  const conexion = new ConexionLive(audio, eventos);
  const canal = { readyState: 'open', send: vi.fn(), close: vi.fn() };
  const pc = { close: vi.fn() };
  const pista = { enabled: true, stop: vi.fn() };
  Object.assign(conexion, { empezo: true, canal, pc, micro: { getTracks: () => [pista], getAudioTracks: () => [pista] } });
  const recibir = (evento: object) => (conexion as unknown as { recibir(s: string): void }).recibir(JSON.stringify(evento));
  return { conexion, canal, pc, pista, eventos, recibir };
}

describe('cierre GPT-Live', () => {
  afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

  it('espera session.closed con audio y canal abiertos, y conserva los deltas exactos', () => {
    vi.useFakeTimers();
    vi.stubGlobal('window', globalThis);
    const { conexion, canal, pc, pista, eventos, recibir } = preparada();
    recibir({ type: 'session.input_transcript.delta', delta: 'I  I', start_ms: 10, end_ms: 35 });
    recibir({ type: 'session.output_transcript.delta', delta: ' yes', start_ms: 20, end_ms: 45 });
    expect(eventos.alDelta.mock.calls.map(c => c[0])).toEqual([
      { hablante: 'lector', delta: 'I  I', start_ms: 10, end_ms: 35 },
      { hablante: 'pleyade', delta: ' yes', start_ms: 20, end_ms: 45 },
    ]);
    conexion.cerrar();
    expect(canal.send).toHaveBeenCalledExactlyOnceWith('{"type":"session.close"}');
    expect(pc.close).not.toHaveBeenCalled();
    expect(pista.stop).not.toHaveBeenCalled();
    expect(pista.enabled).toBe(false);
    recibir({ type: 'session.closed', reason: 'close_requested', usage: { seconds: 12 } });
    expect(eventos.alCerrar).toHaveBeenCalledWith(12, 'close_requested');
    expect(pc.close).toHaveBeenCalledOnce();
    expect(pista.stop).toHaveBeenCalledOnce();
    expect(eventos.alIncompleto).not.toHaveBeenCalled();
  });

  it('informa finalización incompleta si vence el plazo', () => {
    vi.useFakeTimers();
    vi.stubGlobal('window', globalThis);
    const { conexion, pista, eventos } = preparada();
    conexion.cerrar();
    vi.advanceTimersByTime(15_000);
    expect(eventos.alIncompleto).toHaveBeenCalledOnce();
    expect(pista.stop).toHaveBeenCalledOnce();
  });

  it('tolera una desconexión transitoria y cierra si no se recupera', () => {
    vi.useFakeTimers();
    vi.stubGlobal('window', globalThis);
    const { conexion, pc, eventos } = preparada();
    const enlace = pc as unknown as RTCPeerConnection;
    const revisar = (conexion as unknown as { revisarConexion(pc: RTCPeerConnection): void }).revisarConexion.bind(conexion);
    Object.assign(enlace, { connectionState: 'disconnected' });
    revisar(enlace);
    vi.advanceTimersByTime(4_000);
    Object.assign(enlace, { connectionState: 'connected' });
    revisar(enlace);
    vi.advanceTimersByTime(8_000);
    expect(eventos.alIncompleto).not.toHaveBeenCalled();
    Object.assign(enlace, { connectionState: 'disconnected' });
    revisar(enlace);
    vi.advanceTimersByTime(8_000);
    expect(eventos.alIncompleto).toHaveBeenCalledOnce();
  });

  it('cancela antes del alta sin crear una sesión facturable', async () => {
    vi.stubGlobal('window', globalThis);
    let entregar!: (micro: MediaStream) => void;
    const pendiente = new Promise<MediaStream>(resolve => { entregar = resolve; });
    vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: () => pendiente } });
    const pista = { stop: vi.fn() };
    const audio = { pause: vi.fn(), srcObject: null } as unknown as HTMLAudioElement;
    const eventos = { alEmpezar: vi.fn(), alDelta: vi.fn(), alCerrar: vi.fn(),
      alIncompleto: vi.fn(), alError: vi.fn() };
    const conexion = new ConexionLive(audio, eventos);
    const crear = vi.fn();
    const apertura = conexion.abrir(crear);
    const segunda = new ConexionLive(audio, eventos);
    await expect(segunda.abrir(crear)).rejects.toThrow('La conversación anterior sigue cerrándose.');
    conexion.cerrar();
    entregar({ getTracks: () => [pista] } as unknown as MediaStream);
    await expect(apertura).rejects.toThrow('Conexión cancelada.');
    expect(crear).not.toHaveBeenCalled();
    expect(pista.stop).toHaveBeenCalledOnce();
  });

  it('avisa una vez si un delta llega sin sus tiempos', () => {
    const { eventos, recibir } = preparada();
    recibir({ type: 'session.input_transcript.delta', delta: 'hola' });
    recibir({ type: 'session.output_transcript.delta', delta: 'sí' });
    expect(eventos.alDelta).not.toHaveBeenCalled();
    expect(eventos.alError).toHaveBeenCalledOnce();
  });
});
