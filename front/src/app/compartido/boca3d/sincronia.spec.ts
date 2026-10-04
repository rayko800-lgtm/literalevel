import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import posesCompletas from './poses.ejemplo.json';
import ajustes3d from './poses.ajustes3d.json';
import { AjustesPoses3d, CatalogoPoses, conAjustes3d, ipaPorLetras, poseDe, trocearIpa } from './poses';
import palabrasAudio from './palabras_audio.json';
import { ADELANTO, aVelocidad, alAudio, alCompasDeTramos, cicloSonido, lineaFrase, retrasoAudio } from './animacion';
import { finSonoro, tramosSonoros } from './audio';
import { CadenciaSombreado, EscenaBoca } from './escena';

const catalogo = conAjustes3d(posesCompletas as unknown as CatalogoPoses, ajustes3d as unknown as AjustesPoses3d);
const ciclo = (s: string) => cicloSonido(poseDe(catalogo, s)!, catalogo);

describe('24 sep: la boca al compás del audio medido', () => {
  it('una fricativa sostiene la pose exactamente lo que suena su audio', () => {
    const base = ciclo('f');
    const l = alAudio(base, 'fricativa', 1.4);
    expect(l.sonidoEn).toBeCloseTo(base.claves[2].t);
    expect(l.claves[3].t - l.claves[2].t).toBeCloseTo(1.4);
    // Lo de después se desplaza sin cambiar su duración.
    expect(l.claves[4].t - l.claves[3].t).toBeCloseTo(base.claves[4].t - base.claves[3].t);
    expect(l.total).toBeCloseTo(base.total + 1.4 - (base.claves[3].t - base.claves[2].t));
  });

  it('una oclusiva suena en la explosión (fin del cierre), no al cerrar', () => {
    const base = ciclo('p');
    const l = alAudio(base, 'oclusiva', 0.3);
    expect(l.sonidoEn).toBeCloseTo(base.claves[3].t);
    expect(l.sonidoEn).toBeGreaterThan(base.sonidoEn);
    expect(l.claves[5].t - l.claves[3].t).toBeCloseTo(0.3);
    // El soplo de la sorda sigue dentro del tramo que suena.
    const soplo = l.aspiracion![0].en;
    expect(soplo).toBeGreaterThanOrEqual(l.claves[3].t);
    expect(soplo).toBeLessThanOrEqual(l.claves[5].t);
  });

  it('un diptongo reparte lo que suena entre sus dos objetivos', () => {
    const base = ciclo('aɪ');
    const l = alAudio(base, 'diptongo', 1.0);
    expect(l.sonidoEn).toBeCloseTo(base.claves[2].t);
    expect(l.claves[5].t - l.claves[2].t).toBeCloseTo(1.0);
  });

  it('sin audio medido (0) la línea no cambia', () => {
    const base = ciclo('s');
    expect(alAudio(base, 'fricativa', 0)).toBe(base);
  });

  it('finSonoro no cuenta el silencio del final', () => {
    const f = 1000, canal = new Float32Array(f);        // 1 s
    for (let i = 100; i < 600; i++) canal[i] = 0.3;       // suena de 0,1 a 0,6 s
    expect(finSonoro([canal], f)).toBeCloseTo(0.6, 3);
  });
});

describe('24 sep: la boca en cada tramo que suena del audio de Miguel', () => {
  it('tramosSonoros separa sonido largo, sonido corto y ejemplo, y no cuenta el ruido de fondo', () => {
    const f = 1000, canal = new Float32Array(5 * f);
    for (let i = 0; i < canal.length; i++) canal[i] = 0.004 * Math.sin(i);        // ruido de fondo
    const suena = (a: number, b: number) => { for (let i = a * f; i < b * f; i++) canal[i] = 0.3 * Math.sin(i / 3); };
    suena(0.1, 2.2); suena(3.3, 3.7); suena(4.5, 5.0);
    const t = tramosSonoros([canal], f);
    expect(t.length).toBe(3);
    expect(t[0].inicio).toBeCloseTo(0.1, 1); expect(t[0].fin).toBeCloseTo(2.2, 1);
    expect(t[2].inicio).toBeCloseTo(4.5, 1);
  });

  it('una fricativa llega a la pose al empezar cada tramo y la sostiene hasta que acaba', () => {
    const tramos = [{ inicio: 0.1, fin: 2.2 }, { inicio: 3.3, fin: 3.7 }];
    const l = alCompasDeTramos(poseDe(catalogo, 'f')!, catalogo, tramos, 0.1, 5)!;
    const pa = l.quieta;
    for (const { inicio, fin } of tramos) {
      const llega = l.claves.find(k => Math.abs(k.t - (ADELANTO + inicio)) < 1e-6);
      const sale = l.claves.find(k => Math.abs(k.t - (ADELANTO + fin)) < 1e-6);
      expect(llega?.pose).toBe(pa);
      expect(sale?.pose).toBe(pa);
    }
    // El audio arranca (archivo en 0) cuando la línea va por ADELANTO.
    expect(l.sonidoEn - 0.1).toBeCloseTo(ADELANTO);
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThan(l.claves[i - 1].t);
  });

  it('una oclusiva cierra antes de cada tramo y explota al empezar; la sorda lleva soplo en cada una', () => {
    const tramos = [{ inicio: 0.1, fin: 0.2 }, { inicio: 0.8, fin: 1.0 }, { inicio: 1.7, fin: 1.9 }];
    const l = alCompasDeTramos(poseDe(catalogo, 'p')!, catalogo, tramos, 0.1, 5)!;
    expect(l.aspiracion?.length).toBe(3);
    for (const { inicio } of tramos) {
      const explosion = l.claves.find(k => Math.abs(k.t - (ADELANTO + inicio)) < 1e-6);
      expect(explosion?.pose).toBe(l.quieta);
    }
  });

  it('sin tramos medidos no hay línea (se usa el ciclo de siempre)', () => {
    expect(alCompasDeTramos(poseDe(catalogo, 'f')!, catalogo, [], 0.1, 5)).toBeNull();
  });
});

describe('24 sep: la palabra de ejemplo del audio también se articula', () => {
  it('en /ʒ/ el último tramo es «vision»: sus poses caen dentro del tramo, antes y después reposo', () => {
    const tramos = [{ inicio: 0.06, fin: 2.0 }, { inicio: 2.7, fin: 3.15 }, { inicio: 3.85, fin: 4.95 }];
    const vision = trocearIpa('/ˈvɪʒən/', catalogo, 'ga').segmentos;
    expect(vision.length).toBe(5);
    const l = alCompasDeTramos(poseDe(catalogo, 'ʒ')!, catalogo, tramos, 0.06, 5.2, vision)!;
    const a = ADELANTO + 3.85, b = ADELANTO + 4.95;
    const dentro = l.claves.filter(k => k.t >= a - 0.06 && k.t <= b + 0.5);
    // Varias poses distintas (v, ɪ, ʒ, ə, n), no una sola sostenida.
    expect(new Set(dentro.map(k => k.pose)).size).toBeGreaterThanOrEqual(4);
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThan(l.claves[i - 1].t);
  });

  it('la tabla de palabras grabadas trae IPA para cada audio', () => {
    const tabla = palabrasAudio as Record<string, Record<string, { palabra: string; ipa: string | null }>>;
    expect(Object.keys(tabla).length).toBeGreaterThanOrEqual(50);
    for (const entrada of Object.values(tabla)) for (const d of Object.values(entrada)) expect(d.ipa).toBeTruthy();
    expect(tabla['0292.mp3']['ga'].palabra).toBe('vision');
  });
});

describe('24 sep: la boca 3D lee una frase entera al compás del audio', () => {
  const seg = (ipa: string) => trocearIpa(ipa, catalogo, 'ga').segmentos;
  const frase = ['/ðeɪ/', '/ɑɹ/', '/ˈjuʒəli/', '/kwaɪt/', '/wɛl/', '/səˈplaɪd/'].map(seg);

  it('las poses caen dentro de los tramos que suenan y en la pausa la boca descansa', () => {
    const tramos = [{ inicio: 0.1, fin: 1.2 }, { inicio: 1.8, fin: 2.6 }];
    const l = lineaFrase(frase, catalogo, tramos, 0.1, 2.9)!;
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThan(l.claves[i - 1].t);
    const habladas = l.claves.filter(k => k.pose !== catalogo.reposo);
    for (const k of habladas) {
      const f = k.t - ADELANTO;
      expect(tramos.some(t => f >= t.inicio - 0.25 && f <= t.fin + 0.05)).toBe(true);
    }
    // En medio de la pausa (1,2 a 1,8 s del archivo), reposo.
    const pausa = l.claves.filter(k => k.t - ADELANTO > 1.4 && k.t - ADELANTO < 1.6);
    for (const k of pausa) expect(k.pose).toBe(catalogo.reposo);
    expect(l.sonidoEn - 0.1).toBeCloseTo(ADELANTO);
    expect(new Set(habladas.map(k => k.pose)).size).toBeGreaterThan(8);
  });

  it('sin tramos medidos usa todo lo que suena; sin sonidos, null', () => {
    const l = lineaFrase(frase, catalogo, [], 0.12, 2.5)!;
    expect(l.claves.some(k => k.pose !== catalogo.reposo)).toBe(true);
    expect(lineaFrase([[], []], catalogo, [], 0.1, 1)).toBeNull();
  });

  it('una palabra sin diccionario se aproxima por letras y la boca la articula', () => {
    expect(ipaPorLetras('doncha')).toBe('dɑntʃæ');
    expect(ipaPorLetras('Sheena')).toBe('ʃinæ');
    expect(seg(ipaPorLetras('subaltern')).length).toBeGreaterThanOrEqual(8);
  });
});

describe('25 sep: la frase del TTS alineada por palabras', () => {
  const segs = (ipa: string) => trocearIpa(ipa, catalogo, 'ga').segmentos;
  const palabras = [segs('ðə'), segs('kæt'), segs('sæt')];

  it('cada palabra se articula dentro de su marca (con el adelanto de 40 ms)', () => {
    const marcas = [{ inicio: 0.1, fin: 0.2 }, { inicio: 0.2, fin: 0.55 }, { inicio: 1.2, fin: 1.6 }];
    const l = lineaFrase(palabras, catalogo, [], 0.1, 1.8, marcas)!;
    const reposo = catalogo.reposo;
    const gestos = l.claves.filter(c => c.pose !== reposo);
    expect(gestos[0].t).toBeGreaterThanOrEqual(ADELANTO + 0.1 - 0.05);
    // «sat» empieza tras la pausa, no antes de su marca.
    const sat = l.claves.filter(c => c.t > ADELANTO + 0.9 && c.pose !== reposo);
    expect(sat.length).toBeGreaterThan(0);
    expect(sat[0].t).toBeGreaterThanOrEqual(ADELANTO + 1.2 - 0.05);
    // Pausa de 0,65 s entre «cat» y «sat»: la boca pasa por el reposo.
    expect(l.claves.some(c => c.pose === reposo && c.t > ADELANTO + 0.55 && c.t < ADELANTO + 1.2)).toBe(true);
    for (let i = 1; i < l.claves.length; i++) expect(l.claves[i].t).toBeGreaterThan(l.claves[i - 1].t);
  });

  it('una palabra sin marca se coloca entre sus vecinas; con menos de la mitad marcadas, reparto por tramos', () => {
    const marcas = [{ inicio: 0.1, fin: 0.2 }, null, { inicio: 0.6, fin: 0.9 }];
    const l = lineaFrase(palabras, catalogo, [], 0.1, 1.2, marcas)!;
    const cat = l.claves.filter(c => c.t > ADELANTO + 0.15 && c.t < ADELANTO + 0.6 && c.pose !== catalogo.reposo);
    expect(cat.length).toBeGreaterThan(0);
    const tramos = [{ inicio: 0.1, fin: 0.9 }];
    const pocas = lineaFrase(palabras, catalogo, tramos, 0.1, 1.2, [{ inicio: 0.1, fin: 0.2 }, null, null]);
    expect(pocas).toEqual(lineaFrase(palabras, catalogo, tramos, 0.1, 1.2));
  });
});

/** 4 oct 2026 (Miguel, tras grabar la demo en el móvil: la boca «desfasada
 *  completamente respecto al audio», también al cambiar la velocidad). */
describe('4 oct: la línea del visor se ancla al audio real', () => {
  let reloj = 0;
  beforeEach(() => { vi.spyOn(performance, 'now').mockImplementation(() => reloj); });
  afterEach(() => vi.restoreAllMocks());

  /** Una escena sin three: solo lo que usan `reproducir` y la línea. */
  function escenaMinima(): EscenaBoca {
    return Object.assign(Object.create(EscenaBoca.prototype), {
      exploracionDidactica: false, corteDidactico: false, reducirMovimiento: false,
      linea: null, desde: null, hacia: null, giroLinea: 0, arrastrando: false, libre: false, sucio: false,
    }) as EscenaBoca;
  }
  /** La pose de la línea en el segundo `t` (método privado de la escena). */
  const poseEn = (e: EscenaBoca, t: number): Float64Array =>
    (e as unknown as { poseDeLinea(t: number): Float64Array }).poseDeLinea(t);

  it('al llegar «playing» 300 ms tarde, la línea se desplaza 0,3 s', () => {
    const e = escenaMinima();
    reloj = 1000;
    e.reproducir(ciclo('f'));
    reloj = 1500;
    expect(e.tiempoLinea).toBeCloseTo(0.5, 6);
    e.desplazarLinea(0.3);
    expect(e.tiempoLinea).toBeCloseTo(0.2, 6);
    // La pose que se enseña es la de 0,2 s de la línea, no la de 0,5.
    expect(Array.from(poseEn(e, e.tiempoLinea!))).toEqual(Array.from(poseEn(e, 0.2)));
    e.desplazarLinea(Number.NaN);
    expect(e.tiempoLinea).toBeCloseTo(0.2, 6);
    e.detener();
    expect(e.tiempoLinea).toBeNull();
    e.desplazarLinea(1);                                 // sin línea, nada
    expect(e.tiempoLinea).toBeNull();
  });

  it('al cambiar la velocidad en marcha, la nueva línea sigue por el mismo punto del gesto', () => {
    const base = ciclo('s');
    const a1 = escenaMinima(), a05 = escenaMinima();
    reloj = 0;
    a1.reproducir(aVelocidad(base, 1));
    reloj = 1200;                                        // a 1× va por 1,2 s
    const t = a1.tiempoLinea!;
    // A 0,5× ese punto del gesto está en 2,4 s de la línea (el doble de larga).
    a05.reproducir(aVelocidad(base, 0.5), {}, t * 1 / 0.5);
    expect(a05.tiempoLinea).toBeCloseTo(2.4, 6);
    const p1 = poseEn(a1, 1.2), p05 = poseEn(a05, 2.4);
    expect(p05.length).toBe(p1.length);
    for (let i = 0; i < p1.length; i++) expect(p05[i]).toBeCloseTo(p1[i], 9);
    // Un `desde` fuera de rango no adelanta la línea.
    a05.reproducir(aVelocidad(base, 0.5), {}, -3);
    expect(a05.tiempoLinea).toBeCloseTo(0, 6);
  });

  it('a cualquier velocidad, y siguiendo por donde iba, la primera energía del audio cae en sonidoEn', () => {
    const base = alAudio(ciclo('f'), 'fricativa', 1.4), silencio = 0.35;
    // Instante de la línea en que el archivo llega a `silencio` si `tocar(retraso, v)`
    // se llamó cuando la línea iba por `desde`: con retraso positivo espera y
    // arranca en 0; con negativo arranca ya en `-retraso * v` del archivo.
    const llega = (retraso: number, v: number, desde: number) =>
      desde + (retraso >= 0 ? retraso + silencio / v : (silencio - (-retraso * v)) / v);
    for (const v of [0.25, 0.5, 1, 1.5, 2]) {
      const l = aVelocidad(base, v);
      const retraso = retrasoAudio(l.sonidoEn, silencio, v);
      expect(llega(retraso, v, 0)).toBeCloseTo(l.sonidoEn, 9);
      for (const desde of [0.2, l.sonidoEn, l.sonidoEn + 0.5]) expect(llega(retraso - desde, v, desde)).toBeCloseTo(l.sonidoEn, 9);
    }
  });
});

describe('4 oct: la cadencia del sombreado del gesto en la cabeza didáctica', () => {
  const pose = (x: number) => Float64Array.from([x, 0, 0]);

  it('la primera vez y sin movimiento recalcula al momento; una pose igual no repite', () => {
    const c = new CadenciaSombreado();
    expect(c.toca(pose(0), 0, false)).toBe(true);
    c.anotar(pose(0), 0, 20);
    expect(c.toca(pose(0), 5, false)).toBe(false);
    expect(c.toca(pose(0), 5, true)).toBe(false);
    expect(c.toca(pose(0.5), 5, false)).toBe(true);      // parada y distinta: ya
    expect(c.pendiente).toBe(false);
  });

  it('en movimiento espera tres veces lo que costó (tope 100 ms); lo aplazado se hace en cuanto la pose se sostiene', () => {
    const c = new CadenciaSombreado();
    c.anotar(pose(0), 0, 20);                            // costó 20 ms: cada 60
    expect(c.toca(pose(0.1), 30, true)).toBe(false);
    expect(c.pendiente).toBe(true);
    expect(c.toca(pose(0.2), 59, true)).toBe(false);
    expect(c.toca(pose(0.3), 60, true)).toBe(true);
    c.anotar(pose(0.3), 60, 20);
    expect(c.pendiente).toBe(false);
    // La pose se sostiene (un cierre, una vocal larga) con un cambio aplazado:
    // se recalcula una vez y ya no se repite.
    expect(c.toca(pose(0.35), 70, true)).toBe(false);
    expect(c.toca(pose(0.35), 80, true)).toBe(true);
    c.anotar(pose(0.35), 80, 20);
    expect(c.toca(pose(0.35), 90, true)).toBe(false);
    // Tope: aunque costara 200 ms no se espera más de 100 (poses distintas en
    // cada cuadro: la boca sigue moviéndose).
    c.anotar(pose(1), 100, 200);
    expect(c.toca(pose(1.1), 150, true)).toBe(false);
    expect(c.toca(pose(1.15), 199, true)).toBe(false);
    expect(c.toca(pose(1.2), 200, true)).toBe(true);
    // Barato (2 ms, un escritorio): cada 6 ms, es decir, cada cuadro.
    c.anotar(pose(2), 300, 2);
    expect(c.toca(pose(2.1), 316, true)).toBe(true);
    // Un coste sin medida válida no bloquea nada.
    c.anotar(pose(3), 400, Number.NaN);
    expect(c.toca(pose(3.1), 401, true)).toBe(true);
  });
});
