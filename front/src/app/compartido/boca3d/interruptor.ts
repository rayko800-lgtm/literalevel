/** Interruptor de la boca 3D.
 *
 *  Encendido (Miguel, 14 sep, 02:55: «incorpóralo de una»). Pronunciar enseña
 *  «Boca en 3D» en la ficha del sonido y en la corrección, e importa el
 *  componente real DIRECTAMENTE desde `./boca3d`: el @defer solo lo separa en su
 *  propio chunk si el import es directo (con una reexportación desde aquí,
 *  three.js entraba entero en el chunk de Pronunciar). Así three.js solo baja
 *  al pulsar el botón.
 *
 *  Para APAGARLO otra vez y dejar three.js fuera del build (como en b05a4e6):
 *    1. aquí, `export const BOCA3D_ACTIVO = false;`
 *    2. en `pantallas/pronunciar.ts`, cambiar el import de `Boca3d` por un
 *       sustituto vacío con selector `app-boca3d` y las entradas sonido, acento,
 *       ipa, acentoIpa y svg2dUrl.
 */
export const BOCA3D_ACTIVO = true;
