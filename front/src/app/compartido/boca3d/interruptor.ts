import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { Acento } from '../../nucleo/api';

/** Interruptor de compilación de la boca 3D.
 *
 *  Decisión de Miguel (14 sep): publicar el front SIN el 3D y decidir otro día
 *  si se enciende. Apagado, Pronunciar no enseña «Boca en 3D» y no importa el
 *  componente real, así que three.js, sus cargadores y las poses no entran en
 *  el build (ni siquiera como chunk diferido). El componente, sus pruebas y los
 *  glb de `public/boca3d` se quedan donde están.
 *
 *  Para ENCENDERLO, dos cambios en este archivo:
 *    1. `export const BOCA3D_ACTIVO = true;`
 *    2. borrar la clase de abajo y poner `export { Boca3d as Boca3dVisor } from './boca3d';`
 */
export const BOCA3D_ACTIVO = false;

/** Sustituto sin nada dentro, con las mismas entradas que usa Pronunciar. */
@Component({
  selector: 'app-boca3d',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '',
})
export class Boca3dVisor {
  readonly sonido = input<string>('');
  readonly acento = input<Acento>('ga');
  readonly ipa = input<string>('');
  readonly acentoIpa = input<Acento | null>(null);
  readonly svg2dUrl = input<string | null>(null);
}
