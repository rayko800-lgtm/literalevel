import { Injectable, inject, signal } from '@angular/core';
import { Api, CorreccionVoz, EstadoEos, PalabraLeida } from '../nucleo/api';

export type Grabacion = 'lista' | 'grabando' | 'grabada';

/** Sondeos de 4 s antes de rendirse («tarda demasiado»). En la demo grabada del 4 oct la frase
 *  tardó 2 min 50 s (el PC genera en 100-190 s, el trabajador pregunta cada 15 s y sube el mp4):
 *  con 45 (tres minutos) se quedaba al borde. 90 = seis minutos. */
export const ESPERAS_EOS_MAX = 90;

/** Lo que Pronunciar deja al salir de la pantalla y encuentra al volver.
 *
 *  Miguel (4 oct, tras grabar la demo): pidió el vídeo de Eos de su frase, tardó,
 *  se fue a leer y al volver a Pronunciar la frase, la grabación y el vídeo habían
 *  desaparecido: el componente se destruía con la pestaña y se llevaba todo. Ahora
 *  la frase, la grabación, la corrección y el estado de Eos viven aquí, en la raíz;
 *  el sondeo de Eos sigue aunque la pantalla no esté montada y, si el vídeo queda
 *  listo mientras el usuario está en otra pestaña, `avisoEos` enciende la franja de
 *  arriba de la app («Eos ya tiene lista tu frase»).
 *
 *  Este servicio es el dueño de la URL `blob:` de la grabación: se revoca al
 *  descartar o al cambiar de frase, nunca al destruir el componente. */
@Injectable({ providedIn: 'root' })
export class EstadoPronunciar {
  private readonly api = inject(Api);

  readonly frase = signal('');
  readonly estado = signal<Grabacion>('lista');
  readonly audioUrl = signal<string | null>(null);
  readonly resultado = signal<CorreccionVoz | null>(null);
  /** La grabación de ahora ya tiene su corrección (Central, 15 sep). */
  readonly corregida = signal(false);
  readonly eosFrase = signal<EstadoEos | null>(null);
  /** El vídeo de Eos quedó listo mientras Pronunciar no estaba montada. */
  readonly avisoEos = signal(false);
  /** La IPA de cada palabra de las frases que lee el 3D, por texto. */
  readonly ipaLectura = new Map<string, PalabraLeida[]>();
  blob: Blob | null = null;
  /** Con qué `libro|cap` de la URL se hizo este estado: otro contexto lo sustituye. */
  contexto = '';

  private montada = false;
  private relojEos: ReturnType<typeof setTimeout> | undefined;
  private esperasEos = 0;
  /** Cuenta las peticiones a Eos: una respuesta de una frase ya descartada se ignora. */
  private turnoEos = 0;

  /** Pronunciar se monta: cualquier aviso pendiente ya se está viendo. */
  entrar(): void {
    this.montada = true;
    this.avisoEos.set(false);
  }

  /** Pronunciar se destruye. Grabando no se queda: el micrófono se soltó con ella. */
  salir(): void {
    this.montada = false;
    if (this.estado() === 'grabando') this.estado.set('lista');
  }

  /** La grabación recién terminada: su `blob:` sustituye al anterior. */
  guardarGrabacion(blob: Blob): void {
    this.revocar();
    this.blob = blob;
    this.audioUrl.set(URL.createObjectURL(blob));
    this.corregida.set(false);
    this.estado.set('grabada');
  }

  /** Sin grabación ni corrección; la frase se queda. */
  descartar(): void {
    this.revocar();
    this.blob = null;
    this.audioUrl.set(null);
    this.estado.set('lista');
    this.resultado.set(null);
    this.corregida.set(false);
  }

  /** «Otra frase» o una frase nueva desde la URL: no queda nada de la anterior. */
  limpiar(): void {
    this.descartar();
    this.cancelarEos();
    this.avisoEos.set(false);
    this.ipaLectura.clear();
    this.frase.set('');
  }

  /** «Ver a Eos leerla»: pide el vídeo del mp3 de la frase y, mientras un PC con
   *  Eos lo hace, pregunta cada 4 s (seis minutos como mucho), esté o no la
   *  pantalla montada. */
  pedirEos(audio: string, texto: string): void {
    const turno = ++this.turnoEos;
    this.esperasEos = 0;
    this.api.eosPedir(audio, texto).subscribe({
      next: r => this.seguirEos(r, turno),
      error: () => { if (turno === this.turnoEos) this.eosFrase.set({ estado: 'fallo', clave: '', video: null }); },
    });
  }

  /** Olvida el vídeo y corta el sondeo; lo que llegue de él ya no cuenta. */
  cancelarEos(): void {
    ++this.turnoEos;
    clearTimeout(this.relojEos);
    this.eosFrase.set(null);
  }

  private seguirEos(r: EstadoEos, turno: number): void {
    if (turno !== this.turnoEos) return;
    this.eosFrase.set(r);
    clearTimeout(this.relojEos);
    if (r.estado === 'listo' && !this.montada) this.avisoEos.set(true);
    if (r.estado !== 'pendiente') return;
    if (++this.esperasEos > ESPERAS_EOS_MAX) { this.eosFrase.set({ ...r, estado: 'fallo', motivo: 'tarda demasiado' }); return; }
    this.relojEos = setTimeout(() => this.api.eosEstado(r.clave).subscribe({
      next: s => this.seguirEos(s, turno),
      error: () => { if (turno === this.turnoEos) this.eosFrase.set({ ...r, estado: 'fallo' }); },
    }), 4000);
  }

  private revocar(): void {
    const u = this.audioUrl();
    if (u) URL.revokeObjectURL(u);
  }
}
