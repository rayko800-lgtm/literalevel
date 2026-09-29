import { DeltaLive } from './transcripcion';

export interface RespuestaLive { session: { id: string }; transport: { sdp: string } }

export interface EventosLive {
  alEmpezar(id: string): void;
  alDelta(delta: DeltaLive): void;
  alCerrar(uso: number | null, razon: string | null): void;
  alIncompleto(motivo: string): void;
  alError(mensaje: string): void;
}

/** El HTTP inicia la sesión. El canal solo lleva eventos y session.close. */
export class ConexionLive {
  private static activa: ConexionLive | null = null;
  private pc: RTCPeerConnection | null = null;
  private canal: RTCDataChannel | null = null;
  private micro: MediaStream | null = null;
  private inicio = 0;
  private cierre = 0;
  private desconexion = 0;
  private empezo = false;
  private cerrando = false;
  private termino = false;
  private cerrarAlEmpezar = false;
  private solicitudEnCurso = false;
  private avisoTranscripcion = false;
  private sesionId = '';
  private resolverInicio: (() => void) | null = null;
  private rechazarInicio: ((e: Error) => void) | null = null;

  constructor(private readonly audio: HTMLAudioElement, private readonly eventos: EventosLive) {}

  async abrir(crear: (sdp: string) => Promise<RespuestaLive>): Promise<void> {
    if (this.termino) throw new Error('Esta conexión ya terminó.');
    if (ConexionLive.activa) throw new Error('La conversación anterior sigue cerrándose. Espera un momento.');
    ConexionLive.activa = this;
    // getUserMedia se llama dentro del clic que inicia la conversación.
    try {
      this.micro = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      this.asegurarActivo();
      const pc = new RTCPeerConnection();
      this.pc = pc;
      for (const pista of this.micro.getAudioTracks()) pc.addTrack(pista, this.micro);
      pc.addEventListener('track', e => {
        this.audio.srcObject = e.streams[0] ?? new MediaStream([e.track]);
        void this.audio.play().catch(() => this.eventos.alError('Pulsa reproducir para oír la respuesta.'));
      });
      pc.addEventListener('connectionstatechange', () => this.revisarConexion(pc));
      const canal = pc.createDataChannel('oai-events');
      this.canal = canal;
      canal.addEventListener('message', e => this.recibir(e.data));
      canal.addEventListener('close', () => {
        if (!this.termino) this.incompleto('Se cerró el canal antes de session.closed.');
      });

      const oferta = await pc.createOffer();
      await pc.setLocalDescription(oferta);
      await this.esperarIce(pc);
      this.asegurarActivo();
      const sdp = pc.localDescription?.sdp;
      if (!sdp) throw new Error('No se pudo preparar la conexión de audio.');
      this.solicitudEnCurso = true;
      const respuesta = await crear(sdp);
      this.solicitudEnCurso = false;
      if (!respuesta.session?.id || !respuesta.transport?.sdp) throw new Error('La sesión llegó incompleta.');
      this.sesionId = respuesta.session.id;
      await pc.setRemoteDescription({ type: 'answer', sdp: respuesta.transport.sdp });
      await new Promise<void>((resolve, reject) => {
        if (this.empezo) { resolve(); return; }
        this.resolverInicio = resolve;
        this.rechazarInicio = reject;
        this.inicio = window.setTimeout(() => {
          this.incompleto('La sesión no confirmó session.started a tiempo.');
        }, 20_000);
      });
    } catch (e) {
      this.solicitudEnCurso = false;
      this.liberar();
      throw e;
    }
  }

  private asegurarActivo(): void {
    if (this.termino) throw new Error('Conexión cancelada.');
  }

  private revisarConexion(pc: RTCPeerConnection): void {
    if (this.termino) return;
    if (pc.connectionState === 'connected') {
      window.clearTimeout(this.desconexion);
    } else if (pc.connectionState === 'disconnected') {
      window.clearTimeout(this.desconexion);
      this.desconexion = window.setTimeout(() => {
        if (pc.connectionState === 'disconnected') {
          this.incompleto('Se interrumpió la conexión antes de confirmar el cierre.');
        }
      }, 8_000);
    } else if (pc.connectionState === 'failed' || pc.connectionState === 'closed') {
      this.incompleto('Se interrumpió la conexión antes de confirmar el cierre.');
    }
  }

  private esperarIce(pc: RTCPeerConnection): Promise<void> {
    if (pc.iceGatheringState === 'complete') return Promise.resolve();
    return new Promise((resolve, reject) => {
      const reloj = window.setTimeout(() => { pc.removeEventListener('icegatheringstatechange', revisar); reject(new Error('El audio tardó demasiado en conectarse.')); }, 10_000);
      const revisar = () => {
        if (pc.iceGatheringState !== 'complete') return;
        window.clearTimeout(reloj);
        pc.removeEventListener('icegatheringstatechange', revisar);
        resolve();
      };
      pc.addEventListener('icegatheringstatechange', revisar);
      revisar();
    });
  }

  private recibir(bruto: string): void {
    let e: Record<string, unknown>;
    try { e = JSON.parse(bruto); } catch { return; }
    if (e['type'] === 'session.started') {
      this.empezo = true;
      window.clearTimeout(this.inicio);
      this.eventos.alEmpezar(this.sesionId);
      this.resolverInicio?.();
      this.resolverInicio = null; this.rechazarInicio = null;
      if (this.cerrarAlEmpezar) this.cerrar();
    } else if (e['type'] === 'session.closed') {
      this.termino = true;
      const uso = e['usage'] as { seconds?: unknown } | undefined;
      this.eventos.alCerrar(typeof uso?.seconds === 'number' ? uso.seconds : null,
        typeof e['reason'] === 'string' ? e['reason'] : null);
      this.liberar();
    } else if (e['type'] === 'session.input_transcript.delta' || e['type'] === 'session.output_transcript.delta') {
      if (typeof e['delta'] === 'string' && typeof e['start_ms'] === 'number' && typeof e['end_ms'] === 'number') {
        this.eventos.alDelta({ hablante: e['type'] === 'session.input_transcript.delta' ? 'lector' : 'pleyade',
          delta: e['delta'], start_ms: e['start_ms'], end_ms: e['end_ms'] });
      } else if (!this.avisoTranscripcion) {
        this.avisoTranscripcion = true;
        this.eventos.alError('Llegó un fragmento de transcripción sin tiempos; no se pudo mostrar.');
      }
    } else if (e['type'] === 'error') {
      const error = e['error'] as { message?: unknown } | undefined;
      this.eventos.alError(typeof error?.message === 'string' ? error.message : 'Error de la conversación en vivo.');
    }
  }

  cerrar(): void {
    if (this.termino || this.cerrando) return;
    this.micro?.getAudioTracks().forEach(t => { t.enabled = false; });
    this.audio.pause();
    if (!this.empezo) {
      this.cerrarAlEmpezar = true;
      if (!this.solicitudEnCurso && !this.sesionId) this.incompleto('Conexión cancelada.');
      return;
    }
    if (this.canal?.readyState !== 'open') {
      this.incompleto('El canal se desconectó antes de enviar session.close.');
      return;
    }
    this.cerrando = true;
    try {
      this.canal.send(JSON.stringify({ type: 'session.close' }));
    } catch {
      this.incompleto('No se pudo enviar session.close.');
      return;
    }
    // Audio, canal y micrófono siguen activos para recibir session.closed.
    this.cierre = window.setTimeout(() => this.incompleto('No llegó session.closed: finalización incompleta.'), 15_000);
  }

  private incompleto(motivo: string): void {
    if (this.termino) return;
    this.termino = true;
    if (this.empezo && !this.cerrando && this.canal?.readyState === 'open') {
      try { this.canal.send(JSON.stringify({ type: 'session.close' })); } catch { /* conexión rota */ }
    }
    this.rechazarInicio?.(new Error(motivo));
    this.rechazarInicio = null; this.resolverInicio = null;
    this.eventos.alIncompleto(motivo);
    this.liberar();
  }

  private liberar(): void {
    window.clearTimeout(this.inicio);
    window.clearTimeout(this.cierre);
    window.clearTimeout(this.desconexion);
    this.canal?.close();
    this.pc?.close();
    this.micro?.getTracks().forEach(t => t.stop());
    this.audio.pause();
    this.audio.srcObject = null;
    this.canal = null; this.pc = null; this.micro = null;
    if (ConexionLive.activa === this) ConexionLive.activa = null;
  }
}
