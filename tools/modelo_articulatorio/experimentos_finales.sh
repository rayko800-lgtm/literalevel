#!/usr/bin/env bash
# Experimentos con todos los datos, en orden y reanudables (cada paso se salta
# si su JSON ya existe). Hablantes de prueba fijos, nunca vistos:
#   GRID s31-s34, Lombard ls50-ls55, EMA f5.
#
# Uso: bash experimentos_finales.sh D:/literalevel_articulatorio
set -u
BASE="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"
C="$BASE/conjunto"; R="$BASE/resultados/final"
mkdir -p "$R"
cd "$HERE"
PG="s31 s32 s33 s34"; PL="ls50 ls51 ls52 ls53 ls54 ls55"
paso() { echo "$(date +%T) $1"; }

[ -f "$R/grid_base.json" ] || { paso "dominancia GRID"; python base_dominancia.py --datos "$C/grid" --salida "$R/grid_base.json" --prueba $PG; }
[ -f "$R/grid_tcn.json" ] || { paso "TCN GRID"; python tcn.py --datos "$C/grid" --salida "$R/grid_tcn.json" --prueba $PG; }
[ -f "$R/grid_pruebas.json" ] || { paso "pruebas duras GRID"; python pruebas_duras.py --datos "$C/grid" --modelos "$R" --prueba $PG --salida "$R/grid_pruebas.json"; }
# (el TCN con tiempos de la app se lanza aparte: ver tiempos_app.log)
[ -f "$R/conjunta.json" ] || { paso "TCN conjunta"; python tcn_conjunto.py --grupo video "$C/grid" --grupo video "$C/lombard" --grupo ema "$C/ema" --prueba $PG $PL f5 --epocas 12 --salida "$R/conjunta.json"; }
[ -f "$R/conjunta_solo_video.json" ] || { paso "TCN conjunta solo vídeo"; python tcn_conjunto.py --grupo video "$C/grid" --grupo video "$C/lombard" --grupo ema "$C/ema" --prueba $PG $PL f5 --solo video --epocas 12 --salida "$R/conjunta_solo_video.json"; }
[ -f "$R/calibracion.json" ] || { paso "calibración"; PYTHONIOENCODING=utf8 python calibrar_rig.py --conjuntos "$C/grid" --poses "$HERE/../../front/src/app/compartido/boca3d" --salida "$R/calibracion.json"; }
[ -f "$R/hoja_s33.mp4" ] || { paso "hoja lado a lado"; python hoja_lado_a_lado.py --conjunto "$C/grid/s33.npz" --otros $(ls "$C"/grid/s*.npz | grep -v -E 's3[1-4]\.npz') --videos "$BASE/datos/grid/s33" --dominancia "$R/dominancia_sin_s31+s32+s33+s34.pt" --tcn "$R/tcn_sin_s31+s32+s33+s34.pt" --frases 10 --salida "$R/hoja_s33.mp4"; }
paso "fin"
