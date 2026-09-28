"""Genera curvas por escena: boca Blender y v3 solo no verbal, sin A2F."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

GENERATOR = Path('C:/Users/laura/literalevel/.claude/worktrees/cara-parlante/tools/cara_parlante/eos_demo/generar.py')
NONVERBAL = Path('D:/literalevel_cara/v3_solo_noverbal')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', type=Path, required=True)
    args = parser.parse_args()
    scenes = json.loads((args.workdir / 'guion_revision.json').read_text(encoding='utf-8-sig'))['escenas']
    if not (NONVERBAL / 'noverbal').exists() or (NONVERBAL / 'boca').exists():
        raise RuntimeError('La carpeta v3 debe contener solo noverbal/')
    for index, scene in enumerate(scenes):
        scene_id = scene['id']
        audio = args.workdir / f'{scene_id}.mp3'
        output = args.workdir / f'curvas_{scene_id}'
        if (output / 'curvas.json').exists():
            print('EXISTENTE', scene_id, flush=True)
            continue
        if not audio.exists():
            raise FileNotFoundError(audio)
        command = [sys.executable, str(GENERATOR), '--audio', str(audio),
                   '--idioma', scene.get('idioma', 'es'), '--salida', str(output),
                   '--boca', 'modelo', '--gestos', 'v3', '--modelo_v3', str(NONVERBAL),
                   '--estilo_v3', 'real', '--semilla', str(500 + index)]
        env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
        print('GENERANDO', scene_id, flush=True)
        subprocess.run(command, check=True, env=env)
        if not (output / 'curvas.json').exists():
            raise RuntimeError(f'No se produjo curvas.json para {scene_id}')
        print('LISTO', scene_id, flush=True)


if __name__ == '__main__':
    main()
