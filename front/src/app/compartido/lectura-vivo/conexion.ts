/** D5 · la conexión con la transcripción en vivo de OpenAI.
 *
 *  El navegador manda el micrófono por WebRTC a una sesión de solo
 *  transcripción (`gpt-live-transcribe`) abierta con una clave EFÍMERA que da
 *  `POST /api/lectura/vivo`; la clave de la cuenta nunca llega aquí. El texto
 *  vuelve por el canal de datos `oai-events` a trozos (`…transcription.delta`).
 *  Sin detección de turnos en el modelo: cada `COMMIT_S` segundos se cierra el
 *  tramo con `input_audio_buffer.commit`, que es lo que da el texto final. */

export const URL_LLAMADAS = 'https://api.openai.com/v1/realtime/calls';
const COMMIT_S = 6;

export interface EventosLectura {
  /** Texto nuevo oído (parcial). */
  alOir(texto: string): void;
  /** Texto final de un tramo (para el registro; el seguimiento usa los parciales). */
  alCerrarTramo?(texto: string): void;
  alError(mensaje: string): void;
}

export class ConexionLectura {
  private pc: RTCPeerConnection | null = null;
  private canal: RTCDataChannel | null = null;
  private micro: MediaStream | null = null;
  private temporizador = 0;
  private cerrada = false;
  /** El tramo del último trozo: cada tramo empieza sin espacio delante y se
   *  pegaría a la última palabra del anterior («man» + «in» = «manin»). */
  private ultimoTramo = '';

  constructor(private readonly eventos: EventosLectura) {}

  /** Pide el micrófono: llamarlo dentro del clic (Safari). */
  async microfono(): Promise<void> {
    this.micro = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    });
  }

  async abrir(claveEfimera: string): Promise<void> {
    if (!this.micro) await this.microfono();
    const pc = new RTCPeerConnection();
    this.pc = pc;
    for (const pista of this.micro!.getAudioTracks()) pc.addTrack(pista, this.micro!);
    const canal = pc.createDataChannel('oai-events');
    this.canal = canal;
    canal.addEventListener('message', e => this.recibir(e.data));
    canal.addEventListener('open', () => {
      this.temporizador = window.setInterval(() => this.enviar({ type: 'input_audio_buffer.commit' }), COMMIT_S * 1000);
    });
    pc.addEventListener('connectionstatechange', () => {
      if (!this.cerrada && (pc.connectionState === 'failed' || pc.connectionState === 'disconnected')) {
        this.eventos.alError('Se cortó la conexión con el servicio de transcripción.');
      }
    });
    const oferta = await pc.createOffer();
    await pc.setLocalDescription(oferta);
    const r = await fetch(URL_LLAMADAS, {
      method: 'POST', body: oferta.sdp,
      headers: { Authorization: `Bearer ${claveEfimera}`, 'Content-Type': 'application/sdp' },
    });
    if (!r.ok) throw new Error(`OpenAI respondió ${r.status}`);
    await pc.setRemoteDescription({ type: 'answer', sdp: await r.text() });
  }

  private enviar(evento: object): void {
    if (this.canal?.readyState === 'open') this.canal.send(JSON.stringify(evento));
  }

  private recibir(bruto: string): void {
    let e: { type?: string; item_id?: string; delta?: string; transcript?: string; error?: { message?: string } };
    try { e = JSON.parse(bruto); } catch { return; }
    if (e.type === 'conversation.item.input_audio_transcription.delta' && e.delta) {
      const nuevo = e.item_id !== this.ultimoTramo;
      this.ultimoTramo = e.item_id ?? '';
      this.eventos.alOir(nuevo ? ' ' + e.delta : e.delta);
    }
    else if (e.type === 'conversation.item.input_audio_transcription.completed' && e.transcript) this.eventos.alCerrarTramo?.(e.transcript);
    else if (e.type === 'error' && e.error?.message && !/buffer too small|empty/i.test(e.error.message)) {
      // Un commit con el búfer vacío (silencio) no es un fallo del lector.
      this.eventos.alError(e.error.message);
    }
  }

  cerrar(): void {
    this.cerrada = true;
    window.clearInterval(this.temporizador);
    this.enviar({ type: 'input_audio_buffer.commit' });
    this.canal?.close();
    this.pc?.close();
    this.micro?.getTracks().forEach(t => t.stop());
    this.pc = null; this.canal = null; this.micro = null;
  }
}
