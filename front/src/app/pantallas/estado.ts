import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { Api, mensajeError } from '../nucleo/api';
import { miles } from '../nucleo/formato';

interface EstadoMotor {
  api: string;
  modelo: { disponible: boolean; cargado: boolean };
  diccionario: { disponible: boolean; megas: number; cargado: boolean };
  catalogo: { disponible: boolean; libros?: number; medido_con_v4?: boolean; resumen?: string; detalle?: string };
  funciones_openai: { disponibles: boolean };
  perfiles: { puerta: boolean; validos: number; declarados: number; avisos: string[] };
}

/** Diagnóstico para la demo: fuera de la navegación, con su propio enlace. */
@Component({
  selector: 'app-estado',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pagina estrecha">
      <header class="cabecera-pagina">
        <span class="antetitulo">Diagnóstico</span>
        <h1>Estado del sistema</h1>
        <p>Qué está disponible en este servidor y qué está ya cargado en memoria.</p>
      </header>
      @if (error()) { <div class="aviso error"><p>{{ error() }}</p></div> }
      @if (estado(); as e) {
        <ul class="lista">
          <li class="tarjeta plana">
            <span class="luz" [class.ok]="e.modelo.disponible"></span>
            <div><strong>Modelo v4</strong><span class="suave">{{ e.modelo.disponible ? 'Disponible' : 'No encontrado' }} · {{ e.modelo.cargado ? 'cargado' : 'se carga al usarlo' }}</span></div>
          </li>
          <li class="tarjeta plana">
            <span class="luz" [class.ok]="e.diccionario.disponible"></span>
            <div><strong>Diccionario (Wiktionary)</strong><span class="suave">{{ e.diccionario.disponible ? miles(e.diccionario.megas) + ' MB' : 'No encontrado' }} · {{ e.diccionario.cargado ? 'cargado' : 'se carga al usarlo' }}</span></div>
          </li>
          <li class="tarjeta plana">
            <span class="luz" [class.ok]="e.catalogo.disponible"></span>
            <div><strong>Catálogo</strong><span class="suave">{{ e.catalogo.disponible ? miles(e.catalogo.libros) + ' libros' + (e.catalogo.medido_con_v4 ? ', medidos con el v4' : '') : 'No disponible' }}</span>
              @if (e.catalogo.resumen) { <span class="tenue pequeno">{{ e.catalogo.resumen }}</span> }</div>
          </li>
          <li class="tarjeta plana">
            <span class="luz" [class.ok]="e.funciones_openai.disponibles" [class.aviso-luz]="!e.funciones_openai.disponibles"></span>
            <div><strong>Explicaciones y voz (OpenAI)</strong><span class="suave">{{ e.funciones_openai.disponibles ? 'Clave configurada' : 'Sin clave: el resto de la app funciona igual' }}</span></div>
          </li>
          <li class="tarjeta plana">
            <span class="luz ok"></span>
            <div><strong>Perfiles</strong><span class="suave">
              {{ e.perfiles.puerta ? e.perfiles.validos + ' válidos de ' + e.perfiles.declarados + ' declarados' : 'Ninguno declarado: todo abierto' }}</span>
              @for (a of e.perfiles.avisos; track a) { <span class="tenue pequeno">⚠ {{ a }}</span> }</div>
          </li>
        </ul>
        <p class="tenue pequeno">API {{ e.api }}</p>
      } @else if (!error()) {
        <div class="espera"><span class="giro"></span>Preguntando al servidor…</div>
      }
    </div>
  `,
  styles: `
    .lista { list-style: none; padding: 0; margin: 0; display: grid; gap: .6rem; }
    li { display: flex; gap: .9rem; align-items: flex-start; }
    li div { display: grid; gap: .1rem; }
    .luz { flex: none; width: 12px; height: 12px; margin-top: .4rem; border-radius: 50%; background: var(--rojo); }
    .luz.ok { background: var(--verde); }
    .luz.aviso-luz { background: var(--ambar); }
  `,
})
export class Estado implements OnInit {
  private readonly api = inject(Api);
  protected readonly estado = signal<EstadoMotor | null>(null);
  protected readonly error = signal('');
  protected readonly miles = miles;

  async ngOnInit(): Promise<void> {
    try {
      this.estado.set((await firstValueFrom(this.api.estado())) as unknown as EstadoMotor);
    } catch (e) {
      this.error.set(mensajeError(e, 'El motor de Pléyade no está respondiendo.'));
    }
  }
}
