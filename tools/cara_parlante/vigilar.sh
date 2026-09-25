#!/usr/bin/env bash
# Reescribe D:/literalevel_cara/ESTADO.md cada minuto (abrirlo en VS Code para ver el progreso).
cd "$(dirname "$0")"
while true; do
  { echo "# Estado de los lotes de la cara"; echo; echo "Actualizado: $(date '+%H:%M:%S') · se refresca solo cada minuto"; echo; echo '```';
    PYTHONIOENCODING=utf8 python estado.py; echo '```';
    echo; echo "> «Obama · índice» es solo la lista de qué vídeos existen en el archivo. La **descarga** de Obama corre en Colab: su avance está en la celda 2 del cuaderno y en la carpeta de Drive literalevel_cara/casa_blanca/videos.";
    echo; echo "## Últimas líneas"; echo; echo '```';
    echo "— YouTube CC BY (medir):"; tail -n 3 /d/literalevel_cara/medir_2.log 2>/dev/null;
    echo "— Miralles:"; tail -n 3 /d/literalevel_cara/miralles/lote.log 2>/dev/null; echo '```'; } > /d/literalevel_cara/ESTADO.md.tmp
  mv /d/literalevel_cara/ESTADO.md.tmp /d/literalevel_cara/ESTADO.md
  sleep 60
done
