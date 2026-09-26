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
 *      paso no es un dato fijo.
 *    - `terminar` (D1.5): la ÚNICA acción de todo el tutorial que llama
 *      `completar()`. Nunca navega ni cambia de paso por su cuenta. */
export interface OpcionPaso {
  readonly etiqueta: string;
  readonly siguienteId?: string;
  readonly ruta?: string;
  readonly accion?: 'abrir-perfil' | 'leer' | 'terminar';
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
  /** Sin «Saltar» (D1.5, solo `tutorial-final`): en la última pantalla del
   *  tutorial no aporta nada, la acción real ya está ahí. Excepción trivial
   *  y localizada al contrato de `spotlight.ts`, no una regla general. */
  readonly sinSaltar?: boolean;
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

/** D1.2 (entrada e intención) + D1.3 (búsqueda y libro), hasta el punto en
 *  que D1.4 (léxico/Pronunciar/Continuar leyendo) y D1.5 (Mi espacio) tienen
 *  que continuar. `lector-inicio` y `practicar-inicio` son checkpoints:
 *  llegar ahí no completa el tutorial (decisión explícita de Miguel:
 *  `completado` queda reservado para el final real de D1.5). */
const PASOS_D1_2: readonly PasoTutorial[] = [
  {
    id: 'cuenta-eleccion',
    titulo: '¿Ya tienes cuenta?',
    // Nada de lo que la app hace de verdad exige cuenta salvo lo que cuesta
    // dinero (explicar una palabra en contexto, resumir, corregir la
    // pronunciación con IA): grabarse y ver el sonido que falla no la piden.
    texto: 'Con cuenta guardamos tu progreso. Sin cuenta también puedes leer, buscar y grabarte.',
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
  // Checkpoint de D1.2, con comportamiento real desde D1.3: en cuanto el
  // router confirma que se está de verdad en /encontrar, pasa a la pregunta.
  { id: 'encontrar-inicio', silencioso: true, texto: 'Buscando tu próxima lectura' },
  {
    id: 'encontrar-busqueda',
    titulo: 'Busca algo que te gustaría leer',
    texto: 'Escríbelo con tus palabras, en español o en inglés.',
    objetivo: '[data-tutorial="encontrar-buscador"]',
  },
  {
    id: 'encontrar-resultados',
    titulo: 'Estos son tus resultados',
    texto: 'Elige el libro que más te interese.',
    objetivo: '[data-tutorial="encontrar-resultados"]',
  },
  // Silencioso a propósito (Miguel, D1.3): la ficha tiene varios botones
  // «Leer» válidos según el libro (empezar, seguir, desde el principio, un
  // capítulo del índice) y ninguno es EL botón. Una tarjeta modal con velo
  // estorbaría probar cualquiera de ellos; la píldora no bloquea nada.
  { id: 'libro-ficha', silencioso: true, texto: 'Mira la ficha y abre el libro cuando estés listo' },
  // Checkpoint de D1.3, con comportamiento real desde D1.4.
  { id: 'lector-inicio', silencioso: true, texto: 'Leyendo' },
  {
    id: 'lector-palabra',
    titulo: 'Prueba manteniendo pulsada una palabra',
    texto: 'Cualquiera que quieras consultar mientras lees.',
    objetivo: '[data-tutorial="lector-texto"]',
  },
  {
    id: 'lexico-abierto',
    titulo: 'Aquí ves el significado y la pronunciación',
    texto: 'Cuando quieras, pasa a practicar cómo suena esa frase.',
    objetivo: '[data-tutorial="lexico-pronunciar"]',
  },
  // Copy y objetivo NO son estos de aquí en la práctica (D1.V, corrección de
  // UX confirmada por prueba humana): `pasoActual` los sustituye según si
  // «Corrígeme» está disponible y si ya hubo un error, para no mandar nunca
  // a un botón que va a fallar seguro. Esta entrada es solo el valor base
  // (caso disponible, recién llegado, sin error) — ver `pasoPronunciarGrabar`.
  {
    id: 'pronunciar-grabar',
    titulo: 'Grábate',
    texto: 'Pulsa el micrófono y lee la frase.',
    objetivo: '[data-tutorial="pronunciar-practica"]',
  },
  // Con objetivo hacia «Continuar leyendo» (D1.V): el resultado ya está a la
  // vista, así que la siguiente acción evidente deja de ser el micrófono.
  // «Escuchar y ver» sigue sin objetivo propio a propósito (Miguel, D1.4):
  // solo tiene sentido si hubo un sonido fallado que enseñar.
  {
    id: 'pronunciar-resultado',
    titulo: 'Aquí ves el resultado',
    texto: 'Si hay un sonido marcado, puedes escucharlo con «Escuchar y ver».',
    objetivo: '[data-tutorial="pronunciar-continuar"]',
  },
  { id: 'practicar-inicio', silencioso: true, texto: 'Practicando' },
  // Checkpoint de D1.4, con comportamiento real desde D1.5.
  { id: 'post-lectura-inicio', silencioso: true, texto: 'Después de leer' },
  {
    id: 'cierre-palabras',
    titulo: 'Vuelve a lo que vas aprendiendo',
    // Sin prometer una palabra concreta (Miguel, D1.5): no hay garantía de
    // que la última consultada ya se haya guardado (etapa completa, IA).
    texto: 'Tus palabras quedan aquí para repasarlas después.',
    // Sin `siguienteId`: no hay ningún enlace real y permanente a /palabras
    // que señalar (Miguel, D1.5 — motivo para D3/Mi espacio), así que el
    // tutorial ofrece su propio botón, pero el paso solo avanza cuando el
    // router CONFIRMA la llegada (ver el watcher más abajo), nunca al pulsar.
    opciones: [{ etiqueta: 'Ver mis palabras', ruta: '/palabras' }],
  },
  {
    id: 'tutorial-final',
    titulo: 'Ya conoces lo esencial de Pléyade',
    texto: 'Encuentra algo que quieras leer, consulta lo que no entiendas y practica tu pronunciación mientras avanzas.',
    opciones: [{ etiqueta: 'Terminar tutorial', accion: 'terminar' }],
    // Única pantalla sin «Saltar» (Miguel, D1.5): ya no aporta nada aquí.
    sinSaltar: true,
  },
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
    const base = this.pasos.find(p => p.id === id) ?? null;
    if (!base) return null;
    return id === 'pronunciar-grabar' ? this.pasoPronunciarGrabar(base) : base;
  });

  /** Si «Corrígeme» está disponible en esta visita (sesión/perfil/OpenAI):
   *  lo notifica `pronunciar.ts` desde su propio `bloqueada()`, el tutorial
   *  no decide nada de la disponibilidad, solo la recuerda (D1.V). */
  private readonly correccionDisponible = signal(true);
  /** Si ya hay una grabación lista para corregir (refleja `estado()` de
   *  Pronunciar): decide si el paso dice «Grábate» o «Pide tu corrección». */
  private readonly grabacionLista = signal(false);
  /** Un intento de corrección (o de grabación) acaba de fallar: micrófono,
   *  backend, 429 o bloqueo pulsado a mano. Se olvida en cuanto se arranca
   *  un intento nuevo (`notificarPronunciar('inicio')`). */
  private readonly errorPronunciar = signal(false);

  /** `pronunciar-grabar` es el único paso cuyo copy y objetivo dependen de
   *  algo que el tutorial no decide (D1.V, corrección de UX confirmada por
   *  prueba humana): nunca instruye a pulsar «Corrígeme» si ya se sabe que
   *  va a fallar, y en cuanto hay un resultado, un error, o una corrección
   *  no disponible, señala la acción real evidente: «Continuar leyendo». */
  private pasoPronunciarGrabar(base: PasoTutorial): PasoTutorial {
    if (this.errorPronunciar()) {
      return {
        ...base,
        titulo: 'Vuelve al punto donde estabas',
        texto: 'Puedes intentarlo de nuevo, o seguir leyendo.',
        objetivo: '[data-tutorial="pronunciar-continuar"]',
      };
    }
    if (!this.correccionDisponible()) {
      return this.grabacionLista()
        ? {
            ...base,
            titulo: 'Puedes escucharte y explorar los sonidos',
            texto: 'La corrección automática está disponible con perfil.',
            objetivo: '[data-tutorial="pronunciar-continuar"]',
          }
        : { ...base, titulo: 'Grábate para escucharte', texto: undefined };
    }
    return this.grabacionLista()
      ? { ...base, titulo: 'Pide tu corrección', texto: 'Toca «Corrígeme» para ver el resultado.' }
      : base;
  }

  readonly puedeAtras = computed(() => this.historial().length > 0 && !this.pasoActual()?.sinAtras);

  /** Mensaje de "cero resultados"/"error" de `encontrar-busqueda` (D1.3):
   *  no forma parte de `PasoTutorial` porque es transitorio y depende de un
   *  intento concreto, no del paso en sí. Se limpia en cualquier transición
   *  de paso (`irA`) y explícitamente al empezar una búsqueda nueva. */
  readonly avisoTransitorio = signal<string | null>(null);

  /** De dónde vino la visita actual a Pronunciar (D1.4), si vino de un libro
   *  concreto: para reconocer que «Continuar leyendo» volvió al mismo sitio
   *  y no a otro libro cualquiera. No es una signal: no dibuja nada por sí
   *  sola, solo la lee el watcher de router de abajo. */
  private origenPronunciar: { id: string; cap: number } | null = null;

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

    // Ninguno de estos pasos tiene botón propio: la acción real (un enlace
    // de verdad de la pantalla, no del tutorial) ya navega; el tutorial solo
    // observa a dónde llegó el router. `encontrar-inicio` solo resuelve
    // cuando el router está REALMENTE en /encontrar (Miguel, D1.3): si el
    // checkpoint se restaura en otra ruta, se queda tal cual —silencioso,
    // sin bloquear nada— hasta que una navegación real lo confirme.
    const ENCONTRAR_O_ANTES = ['encontrar-inicio', 'encontrar-busqueda', 'encontrar-resultados'];
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd), takeUntilDestroyed())
      .subscribe(e => {
        if (!this.activo()) return;
        const url = e.urlAfterRedirects;
        // Cada `if` vuelve a leer `pasoIdActual()` (no una copia de antes de
        // este evento): un único NavigationEnd puede resolver más de un paso
        // en cadena (nivel-final → encontrar-inicio → encontrar-busqueda son
        // la misma navegación real), igual que la resolución síncrona de
        // `irA`. Sin esto, `encontrar-inicio` se quedaría esperando una
        // segunda navegación que nunca llega.
        if (this.pasoIdActual() === 'nivel-final' && url.startsWith('/encontrar')) this.irA('encontrar-inicio');
        if (this.pasoIdActual() === 'encontrar-inicio' && url.startsWith('/encontrar')) this.irA('encontrar-busqueda');
        // Cualquier tarjeta lleva a /libro/:id; no importa cuál, ni si se llegó
        // buscando o saltándose un paso (una ruta escrita a mano, por ejemplo).
        if (ENCONTRAR_O_ANTES.includes(this.pasoIdActual()) && url.startsWith('/libro/')) this.irA('libro-ficha');
        // Cualquiera de los «Leer» de la ficha lleva a /leer/:id/:cap.
        if ([...ENCONTRAR_O_ANTES, 'libro-ficha'].includes(this.pasoIdActual()) && url.startsWith('/leer/')) this.irA('lector-inicio');
        // D1.4: mismo patrón, otro tramo. `lector-inicio` solo resuelve
        // cuando el router está REALMENTE en /leer/ (igual que `encontrar-inicio`).
        if (this.pasoIdActual() === 'lector-inicio' && url.startsWith('/leer/')) this.irA('lector-palabra');
        // La hoja de la palabra ya lleva a /pronunciar con libro/cap (lector.html).
        if (this.pasoIdActual() === 'lexico-abierto' && url.startsWith('/pronunciar')) this.irA('pronunciar-grabar');
        // «Continuar leyendo» (o «Volver al libro» sin contexto) vuelve a /leer/.
        // Solo cuenta como el regreso válido del flujo si el libro/capítulo
        // coincide con el origen registrado (Miguel, D1.4): volver a OTRO
        // libro no es evidencia de que «Continuar leyendo» funcionó, pero
        // tampoco se bloquea esa navegación, simplemente el tutorial no
        // avanza. Sin origen registrado (Pronunciar sin contexto), cualquier
        // vuelta a /leer/ vale, como en D1.3.
        if (['pronunciar-grabar', 'pronunciar-resultado'].includes(this.pasoIdActual()) && url.startsWith('/leer/')) {
          const o = this.origenPronunciar;
          if (!o || url.startsWith(`/leer/${o.id}/${o.cap}`)) this.irA('post-lectura-inicio');
        }
        // D1.5: mismo patrón otra vez. `post-lectura-inicio` solo resuelve
        // cuando el router está REALMENTE en /leer/ (la misma navegación de
        // «Continuar leyendo» que ya lo trajo aquí, en cadena con la línea de
        // arriba — o una posterior, si el checkpoint se restauró aparte).
        if (this.pasoIdActual() === 'post-lectura-inicio' && url.startsWith('/leer/')) this.irA('cierre-palabras');
        // «Ver mis palabras» (cierre-palabras) navega sin `siguienteId`
        // (Miguel, D1.5): el paso solo avanza cuando el router CONFIRMA la
        // llegada a /palabras, nunca al pulsar el botón — clic → navegación
        // → NavigationEnd → tutorial-final, sin maquinaria nueva.
        if (this.pasoIdActual() === 'cierre-palabras' && url.startsWith('/palabras')) this.irA('tutorial-final');
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

  /** Solo para nosotros, en desarrollo: enciende el flag y decide qué hacer
   *  con el progreso guardado (D1.V intento 2, Miguel: antes esto solo
   *  encendía el flag y dejaba `activo` en falso hasta un «Repetir tutorial»
   *  manual, así que `?tutorialv2=on` nunca llegó a mostrar Tutorial v2 en
   *  la prueba humana — solo se vio Bienvenida v1). Si ya estaba activo
   *  (llamada repetida en la misma sesión), no lo reinicia. */
  activarDesarrollo(): void {
    try { localStorage.setItem(CLAVE_DESARROLLO, 'on'); } catch { /* sin almacenamiento */ }
    this.habilitado.set(true);
    if (this.activo()) return;
    this.retomarOArrancar();
  }

  /** Sin progreso, o con uno corrupto/de otra versión/de un paso que ya no
   *  existe (`leerProgreso()` ya degrada todo eso a `null`, o el `pasoId`
   *  puede apuntar a un paso retirado): arranca una vuelta limpia. Con
   *  `activo`, retoma ese `pasoId`. Con `completado`/`saltado` no toca
   *  nada — «Repetir tutorial» (Ajustes) sigue siendo la única vía
   *  explícita para volver a empezarlo. */
  private retomarOArrancar(): void {
    const p = leerProgreso();
    const existe = !!p && this.pasos.some(x => x.id === p.pasoId);
    if (p && existe && p.estado === 'activo') {
      this.pasoIdActual.set(p.pasoId);
      this.activo.set(true);
      return;
    }
    if (p && existe) return; // completado o saltado.
    this.iniciar();
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
    // Única acción de todo el tutorial que completa (D1.5): nunca navega,
    // nunca cambia de paso por su cuenta — «Terminar tutorial» se queda en
    // /palabras, como pidió Miguel.
    if (opcion.accion === 'terminar') {
      this.completar();
      return;
    }
    if (opcion.ruta) void this.router.navigateByUrl(opcion.ruta);
    if (opcion.siguienteId) this.irA(opcion.siguienteId);
  }

  /** Lo que llama `encontrar.ts` al empezar/terminar una búsqueda (D1.3).
   *  Encontrar no sabe nada del tutorial más allá de avisarle; decidir qué
   *  hacer con eso es cosa de aquí, nunca al revés. Solo hace algo si el
   *  tutorial está activo y el paso actual es `encontrar-busqueda`: una
   *  búsqueda fuera del tutorial (flag apagado, u otro paso) no toca nada. */
  notificarBusqueda(resultado: 'inicio' | 'con-resultados' | 'sin-resultados' | 'error'): void {
    if (!this.activo() || this.pasoIdActual() !== 'encontrar-busqueda') return;
    if (resultado === 'inicio') { this.avisoTransitorio.set(null); return; }
    if (resultado === 'con-resultados') { this.avisoTransitorio.set(null); this.irA('encontrar-resultados'); return; }
    this.avisoTransitorio.set(resultado === 'sin-resultados'
      ? 'No encontré resultados. Prueba con otra búsqueda.'
      : 'Hubo un problema con la búsqueda. Puedes intentarlo de nuevo, o seguir sin el tutorial.');
  }

  /** Lo que llama `lector.ts` cuando la hoja de la palabra tiene contenido
   *  LOCAL utilizable (D1.4) — nunca espera a la explicación de contexto
   *  (IA). Mismo guardado que `notificarBusqueda`: sin efecto si el tutorial
   *  está inactivo o en otro paso. */
  notificarLector(evento: 'palabra'): void {
    if (!this.activo() || this.pasoIdActual() !== 'lector-palabra') return;
    if (evento === 'palabra') this.irA('lexico-abierto');
  }

  /** De dónde vino esta visita a Pronunciar (D1.4): `null` si no hay un
   *  libro/capítulo de origen (se abrió desde otro sitio, como siempre). Lo
   *  llama `pronunciar.ts` en `ngOnInit`, con su propio `contexto()` —
   *  Tutorial no calcula ni duplica ese dato, solo lo recuerda para
   *  reconocer el regreso. */
  registrarContextoPronunciar(contexto: { id: string; cap: number } | null): void {
    if (!this.activo()) return;
    this.origenPronunciar = contexto;
  }

  /** Lo que llama `pronunciar.ts` al empezar una grabación o una corrección,
   *  al tener resultado, o al fallar (micrófono, backend, 429, o un bloqueo
   *  pulsado a mano) — D1.4/D1.V. Mismo contrato que `notificarBusqueda`:
   *  solo actúa en `pronunciar-grabar`. El mensaje de error ya no se guarda
   *  aparte en `avisoTransitorio`: lo dice el propio paso (`pasoPronunciarGrabar`),
   *  que también señala «Continuar leyendo» en vez del micrófono. */
  notificarPronunciar(resultado: 'inicio' | 'resultado' | 'error'): void {
    if (!this.activo() || this.pasoIdActual() !== 'pronunciar-grabar') return;
    if (resultado === 'inicio') { this.avisoTransitorio.set(null); this.errorPronunciar.set(false); return; }
    if (resultado === 'resultado') { this.avisoTransitorio.set(null); this.errorPronunciar.set(false); this.irA('pronunciar-resultado'); return; }
    this.errorPronunciar.set(true);
  }

  /** Si «Corrígeme» está disponible en esta visita: lo notifica `pronunciar.ts`
   *  desde su propio `bloqueada()`, reactivamente, en cuanto se sabe (antes de
   *  cualquier intento) — D1.V. El tutorial nunca decide la disponibilidad,
   *  solo la recuerda para no instruir a pulsar un botón que va a fallar. */
  notificarDisponibilidadCorregir(disponible: boolean): void {
    if (!this.activo()) return;
    this.correccionDisponible.set(disponible);
  }

  /** Si ya hay una grabación lista para corregir, reflejando `estado()` de
   *  Pronunciar (D1.V): decide si el paso dice «Grábate» o «Pide tu
   *  corrección», y si la corrección no está disponible, cuándo mostrar el
   *  aviso completo en vez del genérico. */
  notificarGrabacionLista(lista: boolean): void {
    if (!this.activo()) return;
    this.grabacionLista.set(lista);
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
    // Un aviso de `encontrar-busqueda` nunca sobrevive a salir de ese paso;
    // igual el error de `pronunciar-grabar` (D1.V), por si «Atrás» vuelve.
    this.avisoTransitorio.set(null);
    this.errorPronunciar.set(false);
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
