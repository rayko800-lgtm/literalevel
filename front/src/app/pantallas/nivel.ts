import { ChangeDetectionStrategy, Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { Api, Cuestionario, Fragmento, Perfil, Pregunta, mensajeError } from '../nucleo/api';
import { BANDAS, cefr, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

type Vista = 'resultado' | 'preguntas' | 'listo' | 'muestra';

/** El orden sube de nivel poco a poco: la primera pregunta se entiende sin
 *  saber qué es el MCER, y los textos en inglés van de Alicia a Frankenstein.
 *  Seis pasos; tres más para quien quiera afinar. */
const PASOS = ['frecuencia', 'fragmento_facil', 'libro_completo', 'fragmento_medio', 'comprension', 'fragmento_dificil'];
const EXTRA = ['diccionario', 'series', 'lecturas'];

/** «Mídeme»: una pregunta por pantalla (PLAN_3_OCTUBRE.md §3.2).
 *  Nunca dos a la vez; se puede salir en cualquier momento con lo respondido;
 *  y cada respuesta enseña algo: la estimación se mueve desde la primera. */
@Component({
  selector: 'app-nivel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, RouterLink, Icono],
  templateUrl: './nivel.html',
  styleUrl: './nivel.css',
})
export class Nivel implements OnInit {
  readonly empezar = input<string>();

  private readonly api = inject(Api);
  private readonly sesion = inject(Sesion);

  protected readonly perfil = this.sesion.perfil;
  protected readonly inicio = this.sesion.inicio;
  protected readonly cuestionario = signal<Cuestionario | null>(null);
  protected readonly vista = signal<Vista>('preguntas');
  protected readonly paso = signal(0);
  protected readonly afinando = signal(false);
  protected readonly respuestas = signal<Record<string, number | number[]>>({});
  protected readonly estimacion = signal<Perfil | null>(null);
  protected readonly guardando = signal(false);
  protected readonly error = signal('');
  protected muestra = '';

  protected readonly num = num;
  protected readonly cefr = cefr;
  protected readonly bandas = BANDAS;
  protected readonly anclas = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  protected readonly orden = computed(() => (this.afinando() ? [...PASOS, ...EXTRA] : PASOS));

  protected readonly actual = computed<(Pregunta | Fragmento) | null>(() => {
    const c = this.cuestionario();
    if (!c) return null;
    const clave = this.orden()[this.paso()];
    return c.fragmentos.find(f => f.clave === clave) ?? c.preguntas.find(p => p.clave === clave) ?? null;
  });

  protected readonly esFragmento = computed(() => {
    const a = this.actual();
    return !!a && 'texto' in a;
  });

  protected readonly respondidas = computed(() => Object.keys(this.respuestas()).length);

  ngOnInit(): void {
    if (this.perfil() && !this.empezar()) this.vista.set('resultado');
    this.api.cuestionario().subscribe({
      next: c => this.cuestionario.set(c),
      error: e => this.error.set(mensajeError(e)),
    });
  }

  protected fragmento(): Fragmento { return this.actual() as Fragmento; }

  protected elegida(valor: number): boolean {
    const a = this.actual();
    if (!a) return false;
    const r = this.respuestas()[a.clave];
    return Array.isArray(r) ? r.includes(valor) : r === valor;
  }

  protected elegir(valor: number): void {
    const a = this.actual();
    if (!a) return;
    if (a.multiple) {
      const previas = this.respuestas()[a.clave];
      const lista = Array.isArray(previas) ? previas : [];
      const nueva = lista.includes(valor) ? lista.filter(v => v !== valor) : [...lista, valor];
      const r = { ...this.respuestas() };
      if (nueva.length) r[a.clave] = nueva; else delete r[a.clave];
      this.respuestas.set(r);
      void this.estimar();
      return;
    }
    this.respuestas.set({ ...this.respuestas(), [a.clave]: valor });
    void this.estimar();
    // Avanza solo, con un respiro para que se vea la opción marcada.
    setTimeout(() => this.avanzar(), 260);
  }

  protected avanzar(): void {
    if (this.paso() + 1 < this.orden().length) this.paso.set(this.paso() + 1);
    else this.vista.set('listo');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  protected atras(): void {
    if (this.vista() === 'listo') { this.vista.set('preguntas'); return; }
    if (this.paso() > 0) this.paso.set(this.paso() - 1);
  }

  protected afinar(): void {
    this.afinando.set(true);
    this.paso.set(PASOS.length);
    this.vista.set('preguntas');
  }

  protected reiniciar(): void {
    this.respuestas.set({});
    this.estimacion.set(null);
    this.paso.set(0);
    this.afinando.set(false);
    this.error.set('');
    this.vista.set('preguntas');
  }

  private async estimar(): Promise<void> {
    if (!this.respondidas()) { this.estimacion.set(null); return; }
    try {
      this.estimacion.set(await firstValueFrom(this.api.perfilDesdeCuestionario(this.respuestas(), false)));
    } catch {
      /* la estimación provisional es un adorno; guardar dará el error si lo hay */
    }
  }

  protected async guardar(): Promise<void> {
    this.guardando.set(true);
    this.error.set('');
    try {
      const p = await firstValueFrom(this.api.perfilDesdeCuestionario(this.respuestas(), true));
      this.sesion.fijarPerfil(p);
      this.vista.set('resultado');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.guardando.set(false);
    }
  }

  protected async medirMuestra(): Promise<void> {
    this.guardando.set(true);
    this.error.set('');
    try {
      const p = await firstValueFrom(this.api.perfilDesdeMuestra(this.muestra));
      this.sesion.fijarPerfil(p);
      this.muestra = '';
      this.vista.set('resultado');
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.guardando.set(false);
    }
  }

  /** Posición en la barra 0..2, en %. */
  protected pos(v: number | null | undefined): number {
    return Math.max(0, Math.min(100, ((v ?? 0) / 2) * 100));
  }

  protected palabrasMuestra(): number {
    return this.muestra.trim() ? this.muestra.trim().split(/\s+/).length : 0;
  }
}
