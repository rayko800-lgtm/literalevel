#!/usr/bin/env bash
# Lote de TalkingHead-1KH: bajar tramos con audio y medir expresión y prosodia.
# Uso: bash lote_1kh.sh <desde> <n_videos> [tubes_por_video]
# Datos fuera de Git, en D:/literalevel_cara (ver bajar_1kh.py).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
BASE=/d/literalevel_cara
PY=/d/literalevel_articulatorio/venv/Scripts/python
DESDE=${1:-0}; N=${2:-300}; TPV=${3:-6}
cd "$BASE"
"$PY" -u "$HERE/bajar_1kh.py" --tubes talkinghead1kh/data_list/train_video_tubes.txt \
  --salida 1kh/train --desde "$DESDE" --max "$N" --tubes-por-video "$TPV"
"$PY" "$HERE/medir_expresion.py" --modelo /d/literalevel_articulatorio/modelos/face_landmarker.task \
  --salida medidas/train 1kh/train/*.mp4 2>&1 | grep -v -E "^W0000|^I0000|inference_feedback|TfLite|InitGoogle|XNNPACK"
echo "lote terminado: $(ls 1kh/train/*.mp4 | wc -l) clips, $(ls medidas/train/*.npz | wc -l) medidas"
