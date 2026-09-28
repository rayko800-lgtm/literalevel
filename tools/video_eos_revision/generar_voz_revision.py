"""Voz Willow con dirección por escena; un bloque a la vez."""
import asyncio
import json
import shutil
from pathlib import Path

import sys
sys.path.insert(0,'D:/literalevel_video/comercial_completo_20260928')
from generar_willow_demo import AsyncOpenAI, config, render

HERE=Path(__file__).resolve().parent
SCENES=json.loads((HERE/'guion_revision.json').read_text(encoding='utf-8'))['escenas']
BASE=(
    'Eres Eos y hablas a una sola persona en español de México. Tu voz es Willow: '
    'joven, tierna, clara y natural, sin falsete ni voz de locutora. '
    'Da agudos y graves conversacionales, cambia el ritmo con el sentido. '
    'Lee exactamente el texto escrito en el mensaje anterior, sin añadir palabras. '
    'No digas indicaciones escénicas. Pronuncia Pléyade PLÉ-ya-de. '
)

async def main():
    key=config.obtener('OPENAI_API_KEY')
    if not key: raise RuntimeError('No hay clave para voz')
    client=AsyncOpenAI(api_key=key,timeout=30)
    for scene in SCENES:
        name=scene['id']
        if (HERE/(name+'.wav')).exists() and (HERE/(name+'.wav')).stat().st_size>1000:
            print(name,'ya existe',flush=True)
            continue
        if scene.get('audio_existente'):
            shutil.copyfile(scene['audio_existente'], HERE/(name+'.wav'))
            print(name,'voz existente de Eos',flush=True)
            continue
        prompt=BASE+scene['direccion']
        item={**scene,'indicaciones':prompt}
        for attempt in range(3):
            try:
                await render(client,item,HERE)
                break
            except Exception as exc:
                if attempt==2: raise
                print(name,'reintento',attempt+1,type(exc).__name__,flush=True)
                await asyncio.sleep(2)

if __name__=='__main__':asyncio.run(main())
