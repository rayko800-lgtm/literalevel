import { Injectable, computed, effect, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router } from '@angular/router';
import { filter } from 'rxjs';
import { Sesion } from './sesion';

/** Una opción dentro de un paso de elección (D1.2): sin índices, cada una
 *  sabe a qué paso lleva y qué hacer al elegirla.
 *  - `ruta`: navega ahí con el router antes de avanzar.
 *  - `accion`: efecto especial que no es una navegación simple:
 *    - `abrir-perfil`: abre Ajustes en «Tu perfil» (como «Entrar» de
 *      `bienvenida.ts`) y NO avanza todavía — el tutorial espera a que la
 *      sesión pase a autenticada (ver el `effect` de más abajo) en vez de
 *      forzar un paso que todavía no ha pasado de verdad.
 *    - `leer`: el destino depende de si ya hay nivel medido; se resuelve
 *      en `elegir()`, no aquí, porque es la única opción cuyo siguiente
 *      paso no es un dato fijo. */
export interface OpcionPaso {
  readonly etiqueta: string;
  readonly siguienteId?: string;
  readonly ruta?: string;
  readonly accion?: 'abrir-perfil' | 'leer';
}

/** Un paso del tutorial guiado v2. Tres formas, no una sola:
 *  - **de elección** (`opciones`): tarjeta con sus propios botones, sin
 *    «Siguiente» genérico.
 *  - **de objetivo real** (`objetivo`, selector estable tipo
 *    `[data-tutorial="..."]`, nunca `nth-child` ni una clase de estilo):
 *    apunta a un elemento de verdad; el avance lo dispara la acción real
 *    sobre ese elemento (ver el contrato de `spotlight.ts`), nunca un
 *    «Siguiente» además del clic real.
 *  - **silencioso** (`silencioso`): no muestra tarjeta ni le quita el foco
 *    a nada; solo un indicador pequeño, no modal, con «Salir». Lo usan los
 *    tramos largos (el cuestionario de nivel) y los puntos donde D1.2
 *    termina su parte y espera a que un incremento futuro construya lo que
 *    sigue («checkpoint»): mismo `pasoId`, mismo `estado: 'activo'`, para
 *    que D1.3 y D1.5 lo retomen tal cual. */
export interface PasoTutorial {
  readonly id: string;
  readonly titulo?: string;
  readonly texto?: string;
  readonly objetivo?: string;
  readonly opciones?: readonly OpcionPaso[];
  readonly silencioso?: boolean;
  /** Aunque haya historial, este paso no ofrece «Atrás» (p. ej. `nivel-final`:
   *  no tiene sentido deshacer un nivel ya medido). */
  readonly sinAtras?: boolean;
}

type EstadoProgreso = 'activo' | 'completado' | 'saltado';

/** Lo que se guarda en el navegador. `version` existe para poder cambiar la
 *  forma de este objeto en el futuro sin que un progreso viejo rompa nada:
 *  una versión que no coincide se trata igual que si no hubiera progreso.
 *  Solo tres estados posibles (D1.2, decisión explícita de Miguel: un
 *  checkpoint sigue siendo `activo`, no hace falta un cuarto valor). */
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

/** D1.2: entrada e intención, hasta el punto en que D1.3 (Encontrar/libro/
 *  lector/léxico/Pronunciar) y D1.5 (Mi espacio) tienen que continuar.
 *  `encontrar-inicio` y `practicar-inicio` son checkpoints: D1.2 llega ahí
 *  y se detiene sin completar el tutorial (decisión explícita de Miguel:
 *  `completado` queda reservado para el final real de D1.5). */
const PASOS_D1_2: readonly PasoTutorial[] = [
  {
    id: 'cuenta-eleccion',
    titulo: '¿Ya tienes cuenta?',
    // Nada de lo que la app hace de verdad exige cuenta salvo lo que cuesta
    // dinero (explicar una palabra en contexto, resumir, corregir la
    // pronunciación con IA): grabarse y ver el sonido que falla no la piden.
    texto: 'Con cuenta guardamos tu progreso y puedes pedir explicaciones en contexto. Sin cuenta también puedes leer, buscar, medir tu nivel, grabarte y ver qué sonido falla.',
    opciones: [
      { etiqueta: 'Entrar', accion: 'abrir-perfil' },
      { etiqueta: 'Continuar sin cuenta', siguienteId: 'intencion' },
    ],
  },
  {
    id: 'intencion',
    titulo: '¿Qué quieres hacer?',
    texto: 'Puedes cambiar de idea después: esto solo te lleva a donde quieras empezar.',
    opciones: [
      { etiqueta: '📖 Leer', accion: 'leer' },
      { etiqueta: '🎯 Medir mi nivel', siguienteId: 'nivel-inicio', ruta: '/nivel' },
      { etiqueta: '🧠 Practicar', siguienteId: 'practicar-eleccion' },
    ],
  },
  {
    id: 'leer-eleccion',
    titulo: '¿Buscas ya o mides primero?',
    texto: 'Sin nivel también puedes buscar; solo ordenamos mejor los resultados si lo sabemos.',
    opciones: [
      { etiqueta: 'Buscar sin nivel', siguienteId: 'encontrar-inicio', ruta: '/encontrar' },
      { etiqueta: 'Medir mi nivel primero', siguienteId: 'nivel-inicio', ruta: '/nivel' },
    ],
  },
  {
    id: 'nivel-inicio',
    silencioso: true,
    texto: 'Midiendo tu nivel',
  },
  {
    id: 'nivel-final',
    titulo: 'Ya tenemos una referencia de tu nivel',
    texto: 'Ahora vamos a encontrar algo para leer.',
    objetivo: '[data-tutorial="nivel-ver-libros"]',
    sinAtras: true,
  },
  {
    id: 'practicar-eleccion',
    titulo: '¿Qué practicas hoy?',
    texto: 'Puedes repasar tus palabras o grabarte leyendo.',
    opciones: [
      { etiqueta: 'Mis palabras', siguienteId: 'practicar-inicio', ruta: '/palabras' },
      { etiqueta: 'Pronunciar', siguienteId: 'practicar-inicio', ruta: '/pronunciar' },
    ],
  },
  // Checkpoints: D1.3 y D1.5 los retoman con este mismo id, sin migrar nada.
  { id: 'encontrar-inicio', silencioso: true, texto: 'Buscando tu próxima lectura' },
  { id: 'practicar-inicio', silencioso: true, texto: 'Practicando' },
];

/** Motor del tutorial guiado v2. Detrás de un flag de desarrollo
 *  (`literalevel.tutorial-dev` en el navegador): mientras no esté activado,
 *  `habilitado()` es falso y nada de esto se muestra ni se activa solo,
 *  aunque haya progreso guardado de una sesión anterior. La bienvenida
 *  actual (`compartido/bienvenida.ts`) sigue siendo el onboarding real hasta
 *  que D1.5 esté terminado y se decida el corte. */
@Injectable({ providedIn: 'root' })
export class Tutorial {
  private readonly sesion = inject(Sesion);
  private readonly router = inject(Router);

  readonly pasos: readonly PasoTutorial[] = PASOS_D1_2;

  readonly habilitado = signal(leerFlagDesarrollo());
  readonly activo = signal(false);

  /** El id «en curso», incluso mientras `cuenta-eleccion` está a la espera
   *  de saber si hay sesión (ver `pasoActual`, que lo oculta hasta saberlo). */
  private readonly pasoIdActual = signal('cuenta-eleccion');
  /** Ids visitados, para «Atrás»; no es el historial de navegación del router.
   *  Signal y no un array plano: `puedeAtras` es un `computed`, y un `computed`
   *  solo se invalida cuando cambia una señal que de verdad leyó — un array
   *  mutado por fuera (`.push()`) no cuenta, y el cortocircuito de `&&` hace
   *  que a veces ni siquiera se llegue a leer `pasoActual()` en el mismo turno. */
  private readonly historial = signal<readonly string[]>([]);

  /** Mientras el paso «en curso» es `cuenta-eleccion` pero todavía no
   *  sabemos si hay sesión, no se muestra nada: ni la pregunta (podría
   *  sobrar) ni otra cosa (todavía no sabemos qué mostrar). En cuanto se
   *  sabe, el `effect` de abajo decide y este computed ya no lo oculta. */
  readonly pasoActual = computed<PasoTutorial | null>(() => {
    if (!this.activo()) return null;
    const id = this.pasoIdActual();
    if (id === 'cuenta-eleccion' && !this.sesion.sesionConocida()) return null;
    return this.pasos.find(p => p.id === id) ?? null;
  });

  readonly puedeAtras = computed(() => this.historial().length > 0 && !this.pasoActual()?.sinAtras);

  constructor() {
    // Único punto que decide qué hacer con `cuenta-eleccion`: si la sesión
    // ya se sabe autenticada (porque ya lo estaba al llegar aquí, o porque
    // «Entrar» acaba de completarse mientras se esperaba), avanza sola sin
    // mostrar la pregunta. Si es anónima, no hace falta hacer nada más:
    // `pasoActual` ya deja de ocultarla en cuanto `sesionConocida()` es
    // verdad.
    effect(() => {
      if (!this.activo() || this.pasoIdActual() !== 'cuenta-eleccion') return;
      if (this.sesion.sesionConocida() && this.sesion.entrada()?.dentro) {
        this.irA('intencion', { registrar: false });
      }
    });

    // `nivel-final` no tiene botón propio: el botón real «Ver libros de mi
    // nivel» ya navega a /encontrar; el tutorial solo lo observa.
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd), takeUntilDestroyed())
      .subscribe(e => {
        if (this.activo() && this.pasoIdActual() === 'nivel-final' && e.urlAfterRedirects.startsWith('/encontrar')) {
          this.irA('encontrar-inicio');
        }
      });

    // El cuestionario de nivel guarda solo al contestar la última pregunta
    // (`nivel.ts`): en cuanto `perfil()` deja de ser null estando en
    // `nivel-inicio`, se avanza a `nivel-final`.
    effect(() => {
      if (this.activo() && this.pasoIdActual() === 'nivel-inicio' && this.sesion.perfil()) {
        this.irA('nivel-final');
      }
    });

    if (!this.habilitado()) return;
    const p = leerProgreso();
    // Progreso inválido, de otra versión, o de un pasoId que ya no existe:
    // se ignora sin más. Nunca arranca el tutorial solo si no hay nada que
    // retomar con sentido (criterio de D1.1: nunca romper la app).
    if (p?.estado === 'activo') {
      const existe = this.pasos.some(x => x.id === p.pasoId);
      if (existe) { this.pasoIdActual.set(p.pasoId); this.activo.set(true); }
    }
  }

  /** Solo para nosotros, en desarrollo: enciende el flag y lo deja guardado. */
  activarDesarrollo(): void {
    try { localStorage.setItem(CLAVE_DESARROLLO, 'on'); } catch { /* sin almacenamiento */ }
    this.habilitado.set(true);
  }

  iniciar(): void {
    if (!this.habilitado()) return;
    this.historial.set([]);
    // Si ya se sabe que hay cuenta, no hace falta pasar por `cuenta-eleccion`
    // ni un instante (se resuelve igual vía el `effect` de arriba, pero fijar
    // el id de partida aquí evita depender del orden de los efectos).
    const inicial = this.sesion.sesionConocida() && this.sesion.entrada()?.dentro ? 'intencion' : 'cuenta-eleccion';
    this.pasoIdActual.set(inicial);
    this.activo.set(true);
    this.persistir('activo');
  }

  /** Elegir una opción del paso actual (paso «de elección»). */
  elegir(opcion: OpcionPaso): void {
    if (!this.activo()) return;
    if (opcion.accion === 'abrir-perfil') {
      this.sesion.abrirPerfil();
      return; // avanza sola cuando la sesión pase a autenticada (ver el effect)
    }
    if (opcion.accion === 'leer') {
      if (this.sesion.perfil()) {
        void this.router.navigateByUrl('/encontrar');
        this.irA('encontrar-inicio');
      } else {
        this.irA('leer-eleccion');
      }
      return;
    }
    if (opcion.ruta) void this.router.navigateByUrl(opcion.ruta);
    if (opcion.siguienteId) this.irA(opcion.siguienteId);
  }

  atras(): void {
    if (!this.activo() || !this.puedeAtras()) return;
    const h = this.historial();
    const anterior = h[h.length - 1];
    this.historial.set(h.slice(0, -1));
    this.pasoIdActual.set(anterior);
    this.persistir('activo');
  }

  saltar(): void {
    if (!this.activo()) return;
    this.persistir('saltado');
    this.activo.set(false);
  }

  /** Reservado para el final real de D1.5: ningún paso de D1.2 lo llama. */
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

  private irA(id: string, opciones: { registrar?: boolean } = {}): void {
    const actual = this.pasoIdActual();
    if ((opciones.registrar ?? true) && actual !== id) this.historial.update(h => [...h, actual]);
    this.pasoIdActual.set(id);
    this.persistir('activo');
    // Resolución inmediata, sin esperar al `effect`: si la condición de avance
    // de este paso ya se cumple AHORA (p. ej. llega a `nivel-inicio` con un
    // perfil de una medición anterior), no hace falta esperar a que algo
    // cambie más tarde para saltarlo. Los `effect`s siguen haciendo falta
    // para cuando la condición se cumple DESPUÉS de mostrar el paso.
    if (id === 'nivel-inicio' && this.sesion.perfil()) { this.irA('nivel-final'); return; }
    if (id === 'cuenta-eleccion' && this.sesion.sesionConocida() && this.sesion.entrada()?.dentro) {
      this.irA('intencion', { registrar: false });
    }
  }

  private persistir(estado: EstadoProgreso): void {
    guardarProgreso({ version: VERSION_PROGRESO, pasoId: this.pasoIdActual(), estado });
  }
}
