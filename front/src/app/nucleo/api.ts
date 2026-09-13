import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** Dónde vive el motor: la etiqueta <meta name="literalevel-api"> de index.html.
 *  Vacía = el mismo origen (el proxy de `ng serve`). */
function leerBase(): string {
  try {
    const meta = document.querySelector('meta[name="literalevel-api"]');
    return (meta?.getAttribute('content') ?? '').trim().replace(/\/+$/, '');
  } catch {
    return '';
  }
}

export const BASE_API = leerBase();

/** Un audio o recurso del motor: Wiktionary viene entero; lo nuestro, relativo. */
export function urlMotor(ruta: string | null | undefined): string | null {
  if (!ruta) return null;
  return /^https?:\/\//.test(ruta) ? ruta : BASE_API + ruta;
}

/** Lo que se le enseña al lector cuando algo falla: una frase, nunca un código. */
export function mensajeError(error: unknown, porDefecto = 'No he podido hablar con LiteraLevel.'): string {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) {
      return 'No hay conexión con el motor de LiteraLevel. Si llevaba rato sin usarse, tarda unos 30 segundos en despertar: vuelve a intentarlo.';
    }
    const detalle = error.error?.detail;
    if (typeof detalle === 'string' && detalle) return detalle;
    if (Array.isArray(detalle)) return 'Hay algún dato que no cuadra. Revísalo y vuelve a intentarlo.';
    if (error.status === 429) return 'Has llegado al límite de esta hora. Vuelve a probar en un rato.';
  }
  return porDefecto;
}

// --- Tipos: el contrato de app/api.py -----------------------------------------

export interface Perfil {
  nivel: number;
  banda: string;
  origen: 'cuestionario' | 'muestra';
  creado: string;
  nombre: string;
  objetivo: number;
  rango_recomendado: [number, number];
  cefr: string;
}

export interface Opcion { etiqueta: string; valor: number; }

export interface Pregunta {
  clave: string;
  pregunta: string;
  opciones: Opcion[];
  multiple: boolean;
}

export interface Fragmento extends Pregunta {
  texto: string;
  obra: string;
  autor: string;
  nivel_cefr: string;
  fuente: string;
}

export interface Cuestionario { preguntas: Pregunta[]; fragmentos: Fragmento[]; peso_fragmentos: number; }

export interface LibroTarjeta {
  id: string;
  titulo: string;
  autor: string;
  nivel: string;
  dificultad: number | null;
  gancho: string;
  descargas: number;
  similitud: number;
  afinidad: number;
  abrible: boolean;
  url: string;
}

export interface ResultadoBusqueda {
  resultados: LibroTarjeta[];
  aviso: string;
  ajustado: boolean;
  nivel: number | null;
  nota: string;
}

export interface Recomendacion {
  resultados: LibroTarjeta[];
  necesita_perfil: boolean;
  rango: [number, number] | null;
  rescate: boolean;
  nota?: string;
}

export interface CapituloIndice { indice: number; titulo: string; palabras: number; }

export interface Sugerido { indice: number; titulo: string; palabras: number; dificultad: number | null; }

export interface Sinopsis { de_que_trata?: string; temas?: string[]; para_quien?: string; aviso?: string; }

export interface Libro {
  id: string;
  titulo: string;
  autor: string;
  palabras: number;
  inicial: number;
  dificultad: number | null;
  cefr: string | null;
  fuente_dificultad: string | null;
  capitulos: CapituloIndice[];
  ficha: {
    frase_media: number;
    dialogo: number;
    forma_del_dialogo: string;
    riqueza: number;
    distintivas: string[];
    minutos_comodo: number;
    minutos_exigente: number;
    tiempo: string;
    exigente: boolean | null;
  } | null;
  sugeridos: Sugerido[];
  sinopsis: Sinopsis | null;
}

export interface Capitulo {
  libro_id: string;
  indice: number;
  total: number;
  titulo: string;
  palabras: number;
  parrafos: string[];
}

export interface FilaCurva {
  capitulo: number;
  indice: number | null;
  titulo: string;
  dificultad: number;
  ventanas: number | null;
  palabras: number | null;
}

export interface Curva {
  fuente: 'completo' | 'rapido' | 'catalogo' | null;
  filas: FilaCurva[];
  global?: number;
  cefr?: string;
  banda?: string;
  forma?: 'se_complica' | 'se_suelta' | 'pareja';
  ventanas?: number;
  capitulos_medidos?: number;
  capitulos_totales?: number;
  facil?: FilaCurva;
  dificil?: FilaCurva;
  trabajo?: string | null;
}

export interface Trabajo {
  id: string;
  modo: 'rapido' | 'completo';
  libro_id: string;
  estado: 'en_cola' | 'en_curso' | 'hecho' | 'error';
  hechos: number;
  total: number;
  filas: FilaCurva[];
  error: string | null;
  curva?: Curva;
}

export interface Medida { puntuacion: number; banda: string; cefr: string; bloques: number; confianza: string; }

export interface Palabra {
  etapa: 'diccionario' | 'completa';
  palabra: string;
  lema: string;
  categoria: string | null;
  ipa_uk: string | null;
  ipa_us: string | null;
  /** La palabra no está en el diccionario y la IPA la escribió la IA. */
  ipa_generada_por_ia: boolean;
  audio_uk: string | null;
  audio_us: string | null;
  audio_generado: boolean;
  sentido: string | null;
  etiquetas: string[];
  similitud: number | null;
  sentidos_candidatos: number;
  dudoso: boolean;
  definicion_contextual: string | null;
  explicacion_gramatical: string | null;
  explicacion_adaptada: string | null;
  ejemplo: string | null;
  banda: string;
  zipf: number | null;
  rareza: 'muy_comun' | 'frecuente' | 'poco_frecuente' | 'rara' | null;
  desde_cache: boolean;
  oracion: string;
  origen_oracion: 'capitulo' | 'escrita' | 'sin_contexto';
  explicacion_pendiente: boolean;
  motivo_sin_explicacion: string | null;
  avisos: string[];
  /** Traducción al español en esa oración (con OpenAI). */
  traduccion: string | null;
  /** Definición escrita por la IA cuando el diccionario no trae la palabra. */
  definicion_ia: string | null;
  generado_por_ia: boolean;
  /** La IA eligió otra acepción del diccionario porque la primera era dudosa. */
  acepcion_elegida_por_ia: boolean;
}

/** Cómo se produce un sonido, en palabras de manual y para un hispanohablante. */
export interface FichaSonido {
  rasgos: string;
  labios: string;
  lengua: string;
  boca: string;
  cuerdas: string;
  aire: string;
  trampa: string;
  ga: string;
  rp: string;
}

export interface Fonema {
  simbolo: string;
  nombre: string;
  ejemplos: string[];
  tipo?: string;
  grupo?: string;
  audio: string | null;
  ficha?: FichaSonido;
}

export type Acento = 'ga' | 'rp';

export interface InventarioSonidos {
  acento: Acento;
  acentos: Record<Acento, string>;
  fonemas: Fonema[];
  grupos: { clave: string; titulo: string; sonidos: Fonema[] }[];
}

export interface CorreccionVoz {
  puntuacion: number;
  transcripcion_ok: boolean;
  transcripcion: string;
  palabras: { palabra: string; bien: boolean }[];
  entendidas: [string, string][];
  resumen: string | null;
  detalles: {
    palabra: string;
    ipa: string | null;
    variante: string | null;
    fonema: Fonema | null;
    /** La palabra sola, bien dicha (mp3). */
    audio: string | null;
    sonido_que_falla: string;
    como_colocar_la_boca: string;
  }[];
  audio_correcto: string | null;
  restantes: number | null;
}

export interface PalabraFallada { palabra: string; fallos: number; ultima_vez: string | null; frase: string | null; }

export interface Anotacion {
  palabra: string;
  lema: string;
  categoria: string | null;
  sentido: string | null;
  oracion: string;
  libro: string | null;
  capitulo: number | null;
  rareza: string | null;
  creado: string;
}

export interface Cuaderno { consultas: number; palabras: number; libros: number; entradas: Anotacion[]; }

export interface Repaso { palabras: Anotacion[]; voz: { palabra: string; fallos: number }[]; }

export interface EntradaBiblioteca {
  id: string;
  titulo: string;
  autor: string;
  capitulo: number;
  capitulos: number;
  avance: number;
  palabras: number;
  visto: string;
  consultadas: number;
  titulo_capitulo?: string;
  extracto?: string | null;
}

export interface Entrada {
  puerta: boolean;
  dentro: boolean;
  nombre: string | null;
  restantes: number | null;
  openai: boolean;
  mensaje: string;
}

export interface Inicio {
  perfil: Perfil | null;
  seguir: EntradaBiblioteca | null;
  libros: number;
  cuaderno: { consultas: number; palabras: number; libros: number };
  entrada: Entrada;
}

export interface Salud { estado: string; api: string; cargado: { puntuador: boolean; catalogo: boolean; consultor: boolean }; }

// --- El cliente ------------------------------------------------------------------

@Injectable({ providedIn: 'root' })
export class Api {
  private readonly http = inject(HttpClient);
  private readonly base = BASE_API + '/api';

  salud(): Observable<Salud> { return this.http.get<Salud>(`${this.base}/salud`); }
  estado(): Observable<Record<string, any>> { return this.http.get<Record<string, any>>(`${this.base}/estado`); }
  inicio(): Observable<Inicio> { return this.http.get<Inicio>(`${this.base}/inicio`); }

  entrada(): Observable<Entrada> { return this.http.get<Entrada>(`${this.base}/entrada`); }
  entrar(usuario: string, clave: string): Observable<Entrada> {
    return this.http.post<Entrada>(`${this.base}/entrar`, { usuario, clave });
  }
  salir(): Observable<Entrada> { return this.http.post<Entrada>(`${this.base}/salir`, {}); }

  cuestionario(): Observable<Cuestionario> { return this.http.get<Cuestionario>(`${this.base}/cuestionario`); }
  perfil(): Observable<{ perfil: Perfil | null }> { return this.http.get<{ perfil: Perfil | null }>(`${this.base}/perfil`); }
  perfilDesdeCuestionario(respuestas: Record<string, number | number[] | null>, guardar: boolean, nombre = ''): Observable<Perfil> {
    return this.http.post<Perfil>(`${this.base}/perfil/cuestionario`, { respuestas, guardar, nombre });
  }
  perfilDesdeMuestra(texto: string, nombre = ''): Observable<Perfil> {
    return this.http.post<Perfil>(`${this.base}/perfil/muestra`, { texto, nombre });
  }

  buscar(consulta: string, ajustar = true, n = 12): Observable<ResultadoBusqueda> {
    return this.http.post<ResultadoBusqueda>(`${this.base}/buscar`, { consulta, ajustar, n });
  }
  recomendar(n = 12): Observable<Recomendacion> {
    return this.http.get<Recomendacion>(`${this.base}/recomendar`, { params: { n } });
  }

  libro(id: string): Observable<Libro> { return this.http.get<Libro>(`${this.base}/libros/${encodeURIComponent(id)}`); }
  subirLibro(archivo: File): Observable<Libro> {
    const datos = new FormData();
    datos.append('archivo', archivo, archivo.name);
    return this.http.post<Libro>(`${this.base}/libros`, datos);
  }
  capitulo(id: string, n: number): Observable<Capitulo> {
    return this.http.get<Capitulo>(`${this.base}/libros/${encodeURIComponent(id)}/capitulos/${n}`);
  }
  progreso(id: string, capitulo: number): Observable<{ ok: boolean }> {
    return this.http.put<{ ok: boolean }>(`${this.base}/libros/${encodeURIComponent(id)}/progreso`, { capitulo });
  }
  medirCapitulo(id: string, n: number): Observable<Medida> {
    return this.http.post<Medida>(`${this.base}/libros/${encodeURIComponent(id)}/capitulos/${n}/medir`, {});
  }
  frase(id: string, n: number): Observable<{ frase: string | null }> {
    return this.http.get<{ frase: string | null }>(`${this.base}/libros/${encodeURIComponent(id)}/capitulos/${n}/frase`);
  }
  curva(id: string): Observable<Curva> { return this.http.get<Curva>(`${this.base}/libros/${encodeURIComponent(id)}/curva`); }
  medirCurva(id: string, modo: 'rapido' | 'completo'): Observable<{ trabajo: string | null; ya_medido: boolean }> {
    return this.http.post<{ trabajo: string | null; ya_medido: boolean }>(`${this.base}/libros/${encodeURIComponent(id)}/curva`, { modo });
  }
  trabajo(id: string): Observable<Trabajo> { return this.http.get<Trabajo>(`${this.base}/trabajos/${id}`); }
  sinopsis(id: string): Observable<{ sinopsis: Sinopsis }> {
    return this.http.post<{ sinopsis: Sinopsis }>(`${this.base}/libros/${encodeURIComponent(id)}/sinopsis`, {});
  }

  palabra(cuerpo: { palabra: string; libro_id?: string | null; capitulo?: number | null; oracion?: string | null; idioma: 'es' | 'en'; etapa: 'diccionario' | 'completa' }): Observable<Palabra> {
    return this.http.post<Palabra>(`${this.base}/palabra`, cuerpo);
  }

  fonemas(acento: Acento = 'ga'): Observable<InventarioSonidos> {
    return this.http.get<InventarioSonidos>(`${this.base}/fonemas`, { params: { acento } });
  }
  practicar(frase: string, audio: Blob, nombre: string): Observable<CorreccionVoz> {
    const datos = new FormData();
    datos.append('frase', frase);
    datos.append('audio', audio, nombre);
    return this.http.post<CorreccionVoz>(`${this.base}/voz`, datos);
  }
  debiles(): Observable<{ palabras: { palabra: string; fallos: number }[] }> {
    return this.http.get<{ palabras: { palabra: string; fallos: number }[] }>(`${this.base}/voz/debiles`);
  }
  /** Las que peor pronuncias, con la frase donde fallaste. */
  falladas(n = 15): Observable<{ palabras: PalabraFallada[] }> {
    return this.http.get<{ palabras: PalabraFallada[] }>(`${this.base}/voz/falladas`, { params: { n } });
  }

  cuaderno(n = 60): Observable<Cuaderno> { return this.http.get<Cuaderno>(`${this.base}/cuaderno`, { params: { n } }); }
  repaso(): Observable<Repaso> { return this.http.get<Repaso>(`${this.base}/repaso`); }
  biblioteca(): Observable<{ libros: EntradaBiblioteca[] }> {
    return this.http.get<{ libros: EntradaBiblioteca[] }>(`${this.base}/biblioteca`);
  }
  olvidar(id: string): Observable<{ ok: boolean }> {
    return this.http.delete<{ ok: boolean }>(`${this.base}/biblioteca/${encodeURIComponent(id)}`);
  }
}
