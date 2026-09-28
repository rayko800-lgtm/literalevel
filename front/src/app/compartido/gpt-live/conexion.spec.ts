import { afterEach, describe, expect, it, vi } from 'vitest';
import { ConexionLive } from './conexion';

function preparada() {
  const audio = { pause: vi.fn(), srcObject: null } as unknown as HTMLAudioElement;
  const eventos = { alEmpezar: vi.fn(), alDelta: vi.fn(), alCerrar: vi.fn(),
    alIncompleto: vi.fn(), alError: vi.fn() };
  const conexion = new ConexionLive(audio, eventos);
  const canal = { readyState: 'open', send: vi.fn(), close: vi.fn() };
  const pc = { close: vi.fn() };
  const pista = { stop: vi.fn() };
  Object.assign(conexion, { empezo: true, canal, pc, micro: { getTracks: () => [pista] } });
  const recibir = (evento: object) => (conexion as unknown as { recibir(s: string): void }).recibir(JSON.stringify(evento));
  return { conexion, canal, pc, pista, eventos, recibir };
}

describe('cierre GPT-Live', () => {
  afterEach(() => vi.useRealTimers());

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
});
