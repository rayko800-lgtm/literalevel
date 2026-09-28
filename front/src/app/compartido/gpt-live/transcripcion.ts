export type Hablante = 'lector' | 'pleyade';

export interface DeltaLive {
  hablante: Hablante;
  delta: string;
  start_ms: number;
  end_ms: number;
}

export interface GrupoLive {
  hablante: Hablante;
  inicio: number;
  fin: number;
  partes: DeltaLive[];
  texto: string;
}

/** Agrupa intervalos cercanos por hablante; no inventa turnos ni espacios. */
export function agregarDelta(grupos: GrupoLive[], parte: DeltaLive): GrupoLive[] {
  const copia = grupos.map(g => ({ ...g, partes: [...g.partes] }));
  const ultimo = [...copia].reverse().find(g => g.hablante === parte.hablante);
  if (ultimo && parte.start_ms >= ultimo.inicio && parte.start_ms <= ultimo.fin + 1200) {
    ultimo.partes.push(parte);
    ultimo.fin = Math.max(ultimo.fin, parte.end_ms);
    ultimo.texto += parte.delta;
  } else {
    copia.push({ hablante: parte.hablante, inicio: parte.start_ms, fin: parte.end_ms,
      partes: [parte], texto: parte.delta });
  }
  return copia.sort((a, b) => a.inicio - b.inicio);
}
