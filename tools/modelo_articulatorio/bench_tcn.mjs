// Coste en JavaScript puro de la TCN de `tcn.py` (misma forma: embedding 32,
// 3 rasgos, 64 canales, 4 bloques k=5 con dilatación 1-2-4-8, K salidas),
// con pesos al azar: mide el tiempo, no la calidad. Sin dependencias.
//
//   node bench_tcn.mjs [fotogramas=75] [K=12]
const T = Number(process.argv[2] ?? 75), K = Number(process.argv[3] ?? 12);
const C = 64, E = 32, KER = 5, DIL = [1, 2, 4, 8];
const r = n => Float32Array.from({ length: n }, () => Math.random() * 0.1 - 0.05);

const wIn = r(C * (E + 3)), bIn = r(C);
const bloques = DIL.map(d => ({ d, w: r(C * C * KER), b: r(C) }));
const wOut = r(K * C), bOut = r(K);

function gelu(x) { return 0.5 * x * (1 + Math.tanh(0.7978845608 * (x + 0.044715 * x * x * x))); }

function adelante(x /* [T][E+3] plano */) {
  let h = new Float32Array(C * T);
  for (let t = 0; t < T; t++) for (let c = 0; c < C; c++) {
    let s = bIn[c];
    for (let i = 0; i < E + 3; i++) s += wIn[c * (E + 3) + i] * x[t * (E + 3) + i];
    h[c * T + t] = s;
  }
  for (const { d, w, b } of bloques) {
    const o = new Float32Array(C * T), pad = d * (KER - 1) / 2;
    for (let c = 0; c < C; c++) for (let t = 0; t < T; t++) {
      let s = b[c];
      for (let ci = 0; ci < C; ci++) for (let k = 0; k < KER; k++) {
        const tt = t + k * d - pad;
        if (tt >= 0 && tt < T) s += w[(c * C + ci) * KER + k] * h[ci * T + tt];
      }
      o[c * T + t] = h[c * T + t] + gelu(s);
    }
    h = o;
  }
  const y = new Float32Array(T * K);
  for (let t = 0; t < T; t++) for (let k = 0; k < K; k++) {
    let s = bOut[k];
    for (let c = 0; c < C; c++) s += wOut[k * C + c] * h[c * T + t];
    y[t * K + k] = s;
  }
  return y;
}

const x = r(T * (E + 3));
for (let i = 0; i < 5; i++) adelante(x);
const n = 30, t0 = performance.now();
for (let i = 0; i < n; i++) adelante(x);
const ms = (performance.now() - t0) / n;
const params = C * (E + 3) + C + DIL.length * (C * C * KER + C) + K * C + K;
console.log(JSON.stringify({ fotogramas: T, K, ms_por_frase: +ms.toFixed(2), ms_por_fotograma: +(ms / T).toFixed(4), parametros_sin_embedding: params }));
