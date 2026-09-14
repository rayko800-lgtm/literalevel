import { ChangeDetectionStrategy, Component, OnInit, computed, effect, inject, input, signal, untracked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Icono } from '../compartido/icono';
import { Api, Cuestionario, Fragmento, LibroTarjeta, Perfil, Pregunta, mensajeError } from '../nucleo/api';
import { BANDAS, cefr, num } from '../nucleo/formato';
import { Sesion } from '../nucleo/sesion';

type Vista = 'resultado' | 'preguntas' | 'listo' | 'muestra' | 'libro';

/** El orden sube de nivel poco a poco: la primera pregunta se entiende sin
 *  saber qué es el MCER, y los textos en inglés van de Alicia a Frankenstein.
 *  Seis pasos; tres más para quien quiera afinar. */
const PASOS = ['frecuencia', 'fragmento_facil', 'libro_completo', 'fragmento_medio', 'comprension', 'fragmento_dificil'];
const EXTRA = ['diccionario', 'series', 'lecturas'];
const CLAVE_BORRADOR = 'literalevel.cuestionario';

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
  /** «Mídeme con un libro que ya leí» (paridad con Gradio). */
  protected consultaLibro = '';
  protected readonly librosEncontrados = signal<LibroTarjeta[] | null>(null);
  protected readonly buscandoLibro = signal(false);
  protected readonly midiendoLibro = signal<string | null>(null);
  /** Título del libro con que se midió, para decirlo en el resultado. */
  protected readonly libroMedido = signal<string | null>(null);
  /** Más de 3 s midiendo: casi seguro que el servidor está cargando el modelo. */
  protected readonly medidorLento = signal(false);

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

  /** La pregunta actual ya tiene respuesta: «Siguiente» de la barra de abajo se puede pulsar. */
  protected readonly respondida = computed(() => {
    const a = this.actual();
    return !!a && this.respuestas()[a.clave] !== undefined;
  });

  /** Si el lector pulsa «Volver a medirme», que el perfil guardado no le saque. */
  private quiereMedirse = false;

  constructor() {
    // Miguel rellenó el cuestionario, recargó y volvió a «1 de 6». Al recargar,
    // el perfil llega DESPUÉS de montar la pantalla (lo trae `Sesion` por red),
    // así que en `ngOnInit` aún no había perfil. Cuando llega, se enseña el
    // resultado, salvo que ya se esté contestando.
    effect(() => {
      const p = this.perfil();
      untracked(() => {
        if (p && !this.empezar() && !this.quiereMedirse && this.respondidas() === 0
            && this.vista() === 'preguntas') {
          this.vista.set('resultado');
        }
      });
    });
    // Y lo contestado a medias sobrevive a recargar.
    effect(() => {
      const estado = { respuestas: this.respuestas(), paso: this.paso(), afinando: this.afinando() };
      untracked(() => {
        try {
          if (Object.keys(estado.respuestas).length) localStorage.setItem(CLAVE_BORRADOR, JSON.stringify(estado));
          else localStorage.removeItem(CLAVE_BORRADOR);
        } catch { /* sin almacenamiento */ }
      });
    });
  }

  ngOnInit(): void {
    this.recuperarBorrador();
    if (this.perfil() && !this.empezar() && this.respondidas() === 0) this.vista.set('resultado');
    this.api.cuestionario().subscribe({
      next: c => this.cuestionario.set(c),
      error: e => this.error.set(mensajeError(e)),
    });
  }

  private recuperarBorrador(): void {
    try {
      const crudo = localStorage.getItem(CLAVE_BORRADOR);
      if (!crudo) return;
      const b = JSON.parse(crudo);
      const validas = [...PASOS, ...EXTRA];
      const respuestas: Record<string, number | number[]> = {};
      for (const [k, v] of Object.entries(b?.respuestas ?? {})) {
        const ok = (x: unknown) => typeof x === 'number' && x >= 0 && x <= 2;
        if (validas.includes(k) && (ok(v) || (Array.isArray(v) && v.every(ok)))) respuestas[k] = v as number | number[];
      }
      if (!Object.keys(respuestas).length) return;
      this.respuestas.set(respuestas);
      this.afinando.set(!!b.afinando);
      const total = b.afinando ? PASOS.length + EXTRA.length : PASOS.length;
      this.paso.set(Math.min(Math.max(0, Number(b.paso) || 0), total - 1));
      this.vista.set('preguntas');
      void this.estimar();
    } catch { /* borrador roto: se empieza de cero */ }
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
    this.quiereMedirse = true;
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
      // Guardado: el borrador ya no hace falta.
      this.quiereMedirse = false;
      this.respuestas.set({});
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
      const p = await this.conAvisoLento(firstValueFrom(this.api.perfilDesdeMuestra(this.muestra)));
      this.sesion.fijarPerfil(p);
      this.muestra = '';
      this.vista.set('resultado');
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.guardando.set(false);
    }
  }

  protected async buscarLibro(): Promise<void> {
    const q = this.consultaLibro.trim();
    if (!q) return;
    this.buscandoLibro.set(true);
    this.error.set('');
    try {
      // Sin ajustar al nivel: el libro que busca es uno que ya leyó, sea cual sea.
      const r = await firstValueFrom(this.api.buscar(q, false, 8));
      this.librosEncontrados.set(r.resultados.filter(l => l.abrible));
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.buscandoLibro.set(false);
    }
  }

  /** Como en Gradio: sube su .epub, .pdf o .txt y se miden ocho partes de toda la obra. */
  protected async subirYMedir(ev: Event): Promise<void> {
    const entrada = ev.target as HTMLInputElement;
    const archivo = entrada.files?.[0];
    entrada.value = '';
    if (!archivo) return;
    if (archivo.size > 20 * 1024 * 1024) { this.error.set('El archivo pasa de 20 MB.'); return; }
    this.midiendoLibro.set('subido');
    this.error.set('');
    try {
      const libro = await firstValueFrom(this.api.subirLibro(archivo));
      const p = await this.conAvisoLento(firstValueFrom(this.api.perfilDesdeLibro(libro.id)));
      this.sesion.fijarPerfil(p);
      this.libroMedido.set(libro.titulo || archivo.name);
      this.vista.set('resultado');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      this.error.set(mensajeError(e, 'No he podido medir ese libro.'));
    } finally {
      this.midiendoLibro.set(null);
    }
  }

  protected async medirConLibro(libro: LibroTarjeta): Promise<void> {
    this.midiendoLibro.set(libro.id);
    this.error.set('');
    try {
      const p = await this.conAvisoLento(firstValueFrom(this.api.perfilDesdeLibro(libro.id)));
      this.sesion.fijarPerfil(p);
      this.libroMedido.set(libro.titulo);
      this.librosEncontrados.set(null);
      this.consultaLibro = '';
      this.vista.set('resultado');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      this.error.set(mensajeError(e));
    } finally {
      this.midiendoLibro.set(null);
    }
  }

  /** La primera medición tras despertar el servidor carga el modelo: si pasan
   *  3 s, se dice, para que no parezca colgado. */
  private async conAvisoLento<T>(promesa: Promise<T>): Promise<T> {
    const reloj = setTimeout(() => this.medidorLento.set(true), 3000);
    try {
      return await promesa;
    } finally {
      clearTimeout(reloj);
      this.medidorLento.set(false);
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
