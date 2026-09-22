# Divergencias entre el 3D y el 2D congelado

Las poses del 3D salen de `app/animacion_articulatoria.PARAMETROS` (2D congelado) por
`tools/exportar_poses_boca3d.py` → `front/src/app/compartido/boca3d/poses.ejemplo.json`. El 2D no se toca y,
desde el lote fase 1, **ese JSON tampoco se edita a mano**: lo que el 3D cambia vive en
`front/src/app/compartido/boca3d/poses.ajustes3d.json` (campos sueltos por símbolo) y se mezcla encima al
cargar (`conAjustes3d` en `poses.ts`, y la misma regla en `tools/boca3d_blender/lengua.py` y
`tools/boca3d_demo/medir_lengua.mjs`). Regenerar el JSON con el exportador no pierde nada del 3D.

Aviso previo (medido el 22 sep): el exportador da hoy `factor_lento` 1,143 y el JSON commiteado lleva 1,6
(es el que usa el front); todo lo demás coincide. El factor de «Despacio» es un timing del ciclo (congelado):
**no regenerar el JSON sin resolver antes esa diferencia**.

## Poses (por símbolo)

| Fecha | Fonema | Parámetro | Valor 2D | Valor 3D | Motivo | Dónde |
|---|---|---|---|---|---|---|
| 22 sep (cierre de cara) | /θ/, /ð/ | `mandibula` | 0,36 | 0,6 | Con `MAND_MAX` 0,21 rad el hueco entre bordes incisales a 0,36 es 0,54 u (12 mm) y la punta interdental aprobada (roma, v4) mide 0,64 u: no cabe. Decisión de e6/Miguel (dato, no excepción). | `poses.ajustes3d.json` `sonidos.θ/ð`; `auditoria/d4_4b_cierre_cara_2026-09-22.md` §3 |
| 22 sep (lote fase 1) | /ɹ/ GA | `punta` | `retrofleja` | `reposo` | Variante **abombada** (bunched), la más frecuente en GA (Delattre & Freeman 1968; Zhou et al. 2008, RM): el dorso se abomba hacia el paladar medio y la punta queda recogida y baja, no curvada. La retrofleja sigue siendo una realización válida (mismas fuentes) y se conserva como alternativa: basta quitar esta fila. | `sonidos.ɹ` |
| 22 sep (lote fase 1) | /ɹ/ GA | `cuerpo` · `dorso_alto` · `raiz` | [0,55; 0,35] · 0 · 0,8 | [0,85; 0,35] · 0,3 · 0,9 | La joroba (cúspide en x 0,62, y 1,05, medido) y la constricción faríngea: la raíz queda a 0,04 u de la pared (hueco medido a y −0,8). | `sonidos.ɹ` |
| 22 sep (lote fase 1) | /ɝ/ GA | `punta` · `cuerpo` · `dorso_alto` · `raiz` | `retrofleja` · [0,58; 0,35] · 0,2 · 0,8 | `reposo` · [0,82; 0,38] · 0,3 · 0,85 | Vocal rótica abombada, mismo criterio que /ɹ/ (§9.2 de la investigación: la constricción se sostiene en /ɝ ɚ/). | `sonidos.ɝ` |
| 22 sep (lote fase 1) | /ɚ/ GA | `punta` · `cuerpo` · `dorso_alto` · `raiz` | `retrofleja` · [0,52; 0,40] · 0,1 · 0,6 | `reposo` · [0,7; 0,42] · 0,2 · 0,65 | Ídem, átona: menos joroba y menos raíz. | `sonidos.ɚ` |
| 22 sep (lote fase 1) | /r/ RP (`rp.ɹ`) | pose entera | (no existe en `PARAMETROS_RP`: RP usaba la pose GA de /ɹ/) | `punta` `postalveolar` sin toque, `cuerpo` [0,55; 0,45], `dorso_alto` 0, `raiz` 0 | /r/ de RP es postalveolar y **sin** constricción faríngea ni joroba (§9.3). La no-roticidad en coda no es de la pose: viene de las transcripciones RP del catálogo (sin /r/ en coda), que el visor recibe ya hechas. | `rp.ɹ` |
| 22 sep (lote fase 1) | /ɑ/ GA | `raiz` · `cuerpo` | 0,8 · [0,05; 0,05] | 0 · [0,05; 0,4] | Con la pared faríngea modelada (cara.glb, x 2,84–3,0) la raíz entraba 0,57 u (13 mm) en ella: el giro de la mandíbula (0,21 rad sobre el pivote 2,6; 0,9) ya lleva la raíz 0,44 u hacia atrás con la boca abierta, y `cuerpo_atras` + `raiz` la empujaban más. El 2D no tenía pared. Queda «baja y atrás» por la mandíbula; holgura −0,05. | `sonidos.ɑ` |
| 22 sep (lote fase 1) | /ɒ/ RP | `raiz` · `cuerpo` | 0,8 · [0,02; 0,02] | 0 · [0,02; 0,42] | Ídem /ɑ/ (entraba 0,62 u). Holgura −0,02. | `sonidos.ɒ` |
| 22 sep (lote fase 1) | /ɔ/ GA | `raiz` · `cuerpo` | 0,6 · [0,3; 0,05] | 0,15 · [0,3; 0,35] | Ídem (entraba 0,35 u). Holgura −0,07. | `sonidos.ɔ` |
| 22 sep (lote fase 1) | /ɔː/ RP (`rp.ɔː`) | `raiz` · `cuerpo` | 0,4 · [0,55; 0,05] | 0,15 · [0,55; 0,25] | Ídem (entraba 0,14 u); y RP no enciende la constricción faríngea. | `rp.ɔː` |

## Campos que solo existen en el 3D

| Fecha | Campo | Dónde se pone | Para qué |
|---|---|---|---|
| 22 sep (lote fase 1) | `rotica: true` | `sonidos.ɹ/ɝ/ɚ`, `rp.ɹ` | `familiaDe` manda la pose a la familia `rotico` (antes el criterio era «punta retrofleja», que la /ɹ/ abombada ya no cumple; `raiz ≥ 0,5` no vale porque /ɑ ɒ ɔ/ la llevaban). La familia `rotico` encuadra desde el lote la joroba, la punta y la pared faríngea (target [−0,3; 0,4], zoom 1). Ningún otro fonema cambia de familia (comprobado sobre todo el catálogo). |

## Mapeos pose → morfos que se apartan del 1:1 (no son poses, pero conviene verlos aquí)

| Fecha | Mapeo | Antes | Ahora | Motivo | Dónde |
|---|---|---|---|---|---|
| 22 sep (cierre) | `punta_arriba` con toque en postalveolar (/tʃ dʒ/) | 1,0 | 0,85 | Con la mandíbula de 0,21 rad la suma punta_arriba + cuerpo_alto entraba 0,155 en el paladar (toque permitido 0,08). | `lengua.py` `morfos_de`, `escena.ts` `morfosDe`, `medir_lengua.mjs` |
| 22 sep (cierre) | `dorso_velo` sin toque (`dorso_alto` de /w l ɝ ɚ/) | 1,0 × dorso_alto | 0,9 × dorso_alto | /w/ entraba 0,013 en el velo. /ɝ ɚ/ ya revisadas en el lote fase 1 (abombadas); /l/ y /w/ pendientes de su fase. | mismos tres archivos |
| 22 sep (lote fase 1) | comprobación nueva: raíz contra la pared faríngea | — | perfil medido de la pared (`PARED_FARINGE`), tolerancia 0,08 si `rotica` (roce a propósito) y 0,06 (grosor de la banda) para el resto | Entra en las comprobaciones de siempre de `lengua.py` (COLISION si falla). | `lengua.py` |
