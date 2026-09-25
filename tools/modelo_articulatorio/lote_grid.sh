#!/usr/bin/env bash
# Lote de GRID: por cada hablante cuyo .zip ya bajó entero, descomprime, mide
# (6 procesos), prepara el corpus de MFA, alinea y deja su conjunto. Reanudable:
# cada paso se salta si su salida ya existe.
#
# Uso: bash lote_grid.sh D:/literalevel_articulatorio s4 s5 ...
set -u
BASE="$1"; shift
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$BASE/venv/Scripts/python"
FF="$($PY -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')"
export MAMBA_ROOT_PREFIX="$BASE/mamba/root" MFA_ROOT_DIR="$BASE/mfa_root"
cd "$BASE"
for s in "$@"; do
  until unzip -tq "datos/grid/$s.zip" >/dev/null 2>&1; do sleep 30; done
  [ -d "datos/grid/$s" ] || unzip -q -o "datos/grid/$s.zip" "$s/*" -d datos/grid
  if [ "$(ls medidas/grid/$s 2>/dev/null | wc -l)" -lt 990 ]; then
    ls datos/grid/$s/*.mpg > "lista_$s.txt"
    split -n l/6 -d "lista_$s.txt" "lista_${s}_parte"
    for f in lista_${s}_parte0*; do
      "$PY" "$HERE/medir_video.py" --modelo modelos/face_landmarker.task --salida "medidas/grid/$s" --lista "$f" > "$f.log" 2>&1 &
    done
    wait
  fi
  [ -d "corpus_mfa/$s" ] || "$PY" "$HERE/corpus_mfa_grid.py" --videos "datos/grid/$s" --align "datos/grid/alignments/$s" --salida "corpus_mfa/$s" --ffmpeg "$FF"
  [ -d "alineado/$s" ] || ./mamba/micromamba.exe run -p "$BASE/mfa_mm" mfa align --clean -j 4 --single_speaker "corpus_mfa/$s" english_us_arpa english_us_arpa "alineado/$s" > "mfa_$s.log" 2>&1
  [ -f "conjunto/grid/$s.npz" ] || python "$HERE/datos_fonemas.py" --medidas "medidas/grid/$s" --alineacion "alineado/$s" --salida conjunto/grid --hablante "$s"
  echo "$(date +%T) $s listo"
done
