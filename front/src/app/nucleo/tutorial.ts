import { Injectable, computed, signal } from '@angular/core';

/** Un paso del tutorial guiado v2. `objetivo` es un selector CSS estable
 *  (pensado para `[data-tutorial="..."]`, no `nth-child` ni clases de estilo)
 *  que D1.2-D1.5 rellenan sobre elementos reales. En D1.1 todos los pasos son
 *  de relleno y ninguno lleva `objetivo`: sin él, el spotlight muestra una
 *  tarjeta centrada, sin intentar buscar nada en el DOM. */
export interface PasoTutorial {
  readonly id: string;
  readonly titulo: string;
  readonly texto: string;
  readonly objetivo?: string;
}

type EstadoProgreso = 'activo' | 'completado' | 'saltado';

/** Lo que se guarda en el navegador. `version` existe para poder cambiar la
 *  forma de este objeto en el futuro sin que un progreso viejo rompa nada:
 *  una versión que no coincide se trata igual que si no hubiera progreso. */
interface Progreso {
  readonly version: number;
  readonly pasoId: string;
  readonly estado: EstadoProgreso;
}

const CLAVE_PROGRESO = 'literalevel.tutorial';
const CLAVE_DESARROLLO = 'literalevel.tutorial-dev';
const VERSION_PROGRESO = 1;

function leerProgreso(): Progreso | null {
  try {
    const bruto = localStorage.getItem(CLAVE_PROGRESO);
    if (!bruto) return null;
    const p = JSON.parse(bruto) as Partial<Progreso>;
    if (
      p.version !== VERSION_PROGRESO ||
      typeof p.pasoId !== 'string' ||
      (p.estado !== 'activo' && p.estado !== 'completado' && p.estado !== 'saltado')
    ) {
      return null;
    }
    return { version: p.version, pasoId: p.pasoId, estado: p.estado };
  } catch {
    return null;
  }
}

function guardarProgreso(p: Progreso): void {
  try { localStorage.setItem(CLAVE_PROGRESO, JSON.stringify(p)); } catch { /* sin almacenamiento */ }
}

function leerFlagDesarrollo(): boolean {
  try { return localStorage.getItem(CLAVE_DESARROLLO) === 'on'; } catch { return false; }
}

/** Pasos de relleno para D1.1: demuestran la máquina de estados sin apuntar
 *  todavía a ningún elemento real de la aplicación (eso es D1.2-D1.5). */
const PASOS_PLACEHOLDER: readonly PasoTutorial[] = [
  { id: 'placeholder-1', titulo: 'Paso de prueba 1', texto: 'Paso de relleno para probar el motor del tutorial, sin apuntar a nada todavía.' },
  { id: 'placeholder-2', titulo: 'Paso de prueba 2', texto: 'Segundo paso de relleno.' },
  { id: 'placeholder-3', titulo: 'Paso de prueba 3', texto: 'Último paso de relleno antes de terminar el tutorial.' },
];

/** Motor del tutorial guiado v2 (D1.1). Detrás de un flag de desarrollo
 *  (`literalevel.tutorial-dev` en el navegador): mientras no esté activado,
 *  `habilitado()` es falso y nada de esto se muestra ni se activa solo,
 *  aunque haya progreso guardado de una sesión anterior. La bienvenida
 *  actual (`compartido/bienvenida.ts`) sigue siendo el onboarding real hasta
 *  que D1.5 esté terminado y se decida el corte. */
@Injectable({ providedIn: 'root' })
export class Tutorial {
  /** D1.1 usa pasos de relleno; D1.2-D1.5 sustituirán esta lista. */
  readonly pasos: readonly PasoTutorial[] = PASOS_PLACEHOLDER;

  readonly habilitado = signal(leerFlagDesarrollo());
  readonly activo = signal(false);

  private readonly indice = signal(0);
  /** Índices visitados, para «Atrás»; no es el historial de navegación del router. */
  private readonly historial: number[] = [];

  readonly pasoActual = computed<PasoTutorial | null>(() => (this.activo() ? this.pasos[this.indice()] ?? null : null));
  readonly esPrimero = computed(() => this.indice() === 0);
  readonly esUltimo = computed(() => this.indice() === this.pasos.length - 1);

  constructor() {
    if (!this.habilitado()) return;
    const p = leerProgreso();
    // Progreso inválido, de otra versión, o de un pasoId que ya no existe:
    // se ignora sin más. Nunca arranca el tutorial solo si no hay nada que
    // retomar con sentido (criterio de D1.1: nunca romper la app).
    if (p?.estado === 'activo') {
      const i = this.pasos.findIndex(x => x.id === p.pasoId);
      if (i >= 0) { this.indice.set(i); this.activo.set(true); }
    }
  }

  /** Solo para nosotros, en desarrollo: enciende el flag y lo deja guardado. */
  activarDesarrollo(): void {
    try { localStorage.setItem(CLAVE_DESARROLLO, 'on'); } catch { /* sin almacenamiento */ }
    this.habilitado.set(true);
  }

  iniciar(): void {
    if (!this.habilitado()) return;
    this.historial.length = 0;
    this.indice.set(0);
    this.activo.set(true);
    this.persistir('activo');
  }

  siguiente(): void {
    if (!this.activo()) return;
    if (this.esUltimo()) { this.completar(); return; }
    this.historial.push(this.indice());
    this.indice.update(i => i + 1);
    this.persistir('activo');
  }

  atras(): void {
    if (!this.activo() || !this.historial.length) return;
    this.indice.set(this.historial.pop()!);
    this.persistir('activo');
  }

  saltar(): void {
    if (!this.activo()) return;
    this.persistir('saltado');
    this.activo.set(false);
  }

  completar(): void {
    this.persistir('completado');
    this.activo.set(false);
  }

  /** «Repetir tutorial» desde Ajustes: solo hace algo si el flag de
   *  desarrollo ya está activado (nunca para un usuario normal). */
  repetir(): void {
    if (!this.habilitado()) return;
    this.iniciar();
  }

  private persistir(estado: EstadoProgreso): void {
    const paso = this.pasos[this.indice()] ?? this.pasos[0];
    guardarProgreso({ version: VERSION_PROGRESO, pasoId: paso.id, estado });
  }
}
