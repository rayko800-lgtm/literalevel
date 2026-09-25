/** D5 · lectura guiada en vivo: seguir por dónde va el lector.
 *
 *  La transcripción en vivo de OpenAI llega como texto a trozos, sin tiempos
 *  por palabra ni confianza. El seguimiento se hace alineando esas palabras con
 *  las del texto del libro: un puntero avanza por el texto y cada palabra oída
 *  se busca en una ventana corta por delante. Lo que queda entre el puntero y
 *  la palabra encontrada se marca como saltado; lo que no se encuentra no
 *  mueve nada (una palabra mal oída o una repetición no hacen perder el sitio).
 *  Sin DOM ni red: se prueba solo. */

export type EstadoPalabra = 'pendiente' | 'leida' | 'saltada';

export interface PalabraTexto {
  /** Tal como está en el libro, con su puntuación («Well,»). */
  texto: string;
  /** Normalizada para comparar («well»). */
  clave: string;
  estado: EstadoPalabra;
}

/** Minúsculas, sin puntuación ni acentos, apóstrofos unificados. */
export function normalizar(palabra: string): string {
  return palabra.toLowerCase().normalize('NFD').replace(/\p{M}/gu, '')
    .replace(/[’‘`]/g, "'").replace(/[^a-z0-9']/g, '').replace(/^'+|'+$/g, '');
}

export function trocearTexto(texto: string): PalabraTexto[] {
  return texto.split(/\s+/).filter(Boolean)
    .map(t => ({ texto: t, clave: normalizar(t), estado: 'pendiente' as EstadoPalabra }))
    .filter(p => p.clave);
}

/** Distancia de edición, con tope (para no comparar palabras largas enteras). */
function distancia(a: string, b: string, tope: number): number {
  if (Math.abs(a.length - b.length) > tope) return tope + 1;
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    let minimo = i;
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      minimo = Math.min(minimo, cur[j]);
    }
    if (minimo > tope) return tope + 1;
    prev = cur;
  }
  return prev[b.length];
}

/** Si lo oído vale por la palabra del libro: igual, o casi igual en palabras
 *  de más de cuatro letras («colour»/«color», un plural perdido). */
export function coincide(oida: string, delLibro: string): boolean {
  if (!oida || !delLibro) return false;
  if (oida === delLibro) return true;
  if (delLibro.length <= 4 || oida.length <= 3) return false;
  return distancia(oida, delLibro, 1) <= 1;
}

export class Seguidor {
  /** Índice de la siguiente palabra que se espera oír. */
  puntero = 0;
  /** Palabras oídas que no casaron con el texto (para el resumen). */
  sueltas: string[] = [];

  constructor(readonly palabras: PalabraTexto[], private readonly ventana = 6) {}

  get terminado(): boolean {
    return this.puntero >= this.palabras.length;
  }

  /** Un salto hacia delante pendiente de confirmar: índice del libro donde
   *  casó la última palabra oída, lejos del puntero. */
  private candidato = -1;

  /** Mete lo que ha llegado de la transcripción (uno o varios fragmentos de
   *  texto). Devuelve cuántas palabras del libro avanzó el puntero.
   *
   *  La palabra que toca (o la unión de dos que el modelo juntó) avanza en el
   *  acto. Un salto hacia delante, no: una palabra corta y frecuente («the»,
   *  «his», «that») casa con cualquier cosa, y leyendo otro párrafo marcaba
   *  medio texto como saltado. El salto se da solo si la palabra oída
   *  siguiente casa con la que sigue en el libro (dos seguidas). */
  oir(fragmento: string): number {
    const antes = this.puntero;
    for (const bruta of fragmento.split(/\s+/)) {
      const oida = normalizar(bruta);
      if (!oida || this.terminado) continue;
      if (this.candidato >= 0) {
        const k = this.candidato;
        this.candidato = -1;
        if (k + 1 < this.palabras.length && coincide(oida, this.palabras[k + 1].clave)) {
          this.avanzar(k);
          this.avanzar(k + 1);
          continue;
        }
      }
      if (coincide(oida, this.palabras[this.puntero].clave)) { this.avanzar(this.puntero); continue; }
      if (this.puntero + 1 < this.palabras.length
          && coincide(oida, this.palabras[this.puntero].clave + this.palabras[this.puntero + 1].clave)) {
        this.palabras[this.puntero].estado = 'leida';
        this.avanzar(this.puntero + 1);
        continue;
      }
      const fin = Math.min(this.palabras.length, this.puntero + this.ventana);
      let encontrada = -1;
      for (let k = this.puntero + 1; k < fin; k++) if (coincide(oida, this.palabras[k].clave)) { encontrada = k; break; }
      if (encontrada < 0) { this.sueltas.push(oida); continue; }
      // La última palabra del párrafo no tiene siguiente que la confirme.
      if (encontrada === this.palabras.length - 1 && oida.length > 3) { this.avanzar(encontrada); continue; }
      this.candidato = encontrada;
    }
    return this.puntero - antes;
  }

  /** Marca leída la palabra `k` y saltadas las pendientes antes de ella. */
  private avanzar(k: number): void {
    for (let j = this.puntero; j < k; j++) if (this.palabras[j].estado === 'pendiente') this.palabras[j].estado = 'saltada';
    this.palabras[k].estado = 'leida';
    this.puntero = Math.max(this.puntero, k + 1);
  }

  get saltadas(): PalabraTexto[] {
    return this.palabras.filter(p => p.estado === 'saltada');
  }
}
