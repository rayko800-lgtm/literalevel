"""Genera la continuación Willow por escenas; credenciales solo en memoria."""
import argparse
import asyncio
import base64
import collections
import json
import pathlib
import subprocess
import sys
import time
import wave

import edge_tts
import imageio_ffmpeg
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.vendor'))
sys.path.insert(0, r'C:/Users/laura/literalevel/app')
import config
from openai import AsyncOpenAI
RATE = 24000


def trim_pcm(pcm):
    samples = np.frombuffer(pcm, dtype='<i2')
    if len(samples) == 0:
        raise RuntimeError('Respuesta sin audio')
    step = RATE // 20
    energy = np.array([np.sqrt(np.mean(samples[i:i+step].astype(float)**2))
                       for i in range(0, len(samples), step)])
    active = np.flatnonzero(energy > max(190, energy.max() * .025))
    if len(active) == 0:
        raise RuntimeError('Audio sin voz detectable')
    start = max(0, int(active[0] * step - RATE * .15))
    end = min(len(samples), int((active[-1] + 1) * step + RATE * .55))
    return samples[start:end].tobytes()


async def render(client, scene, out_dir=HERE):
    name, text = scene['id'], scene['texto']
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    command_mp3 = out_dir / (name + '_comando.mp3')
    await edge_tts.Communicate('Lee el texto anterior.',
                               'es-MX-DaliaNeural').save(str(command_mp3))
    raw = subprocess.check_output([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(command_mp3),
                                   '-ac', '1', '-ar', str(RATE), '-f', 's16le', '-'])
    session = {
        'model': 'gpt-live-1',
        'instructions': scene.get('indicaciones') or (
            'Eres Eos, presentadora de Pléyade. Habla en español de México con la voz Willow, '
            'igual que la toma dulce aprobada: cálida, joven, tierna, natural y luminosa. '
            'Hablas a una sola persona; evita tono de locutora, falsete y cadencia mecánica. '
            'Lee literalmente el texto escrito en el mensaje previo cuando la persona te lo pida. '
            'No resumas, no añadas introducción, ni cierres con comentario. Respeta cifras y orden. '
            'Haz pausas naturales breves. Pronuncia Pléyade PLÉ-ya-de.'),
        'audio': {'format': {'type': 'audio/pcm', 'rate': RATE}, 'output': {'voice': 'willow'}},
        'delegation': {'type': 'client'},
        'input': [{'type': 'message', 'role': 'user', 'content': [
            {'type': 'input_text', 'text': 'TEXTO EXACTO PARA LEER: ' + text}]}],
    }
    pcm = bytearray(); transcript = []; errors = []; events = collections.Counter()
    async with client.live.connect(max_retries=0) as connection:
        await connection.session.start(session=session, event_id='inicio_' + name)
        while True:
            e = await asyncio.wait_for(connection.recv(), timeout=15)
            events[e.type] += 1
            if e.type == 'session.started':
                break
            if e.type == 'error':
                raise RuntimeError('Error al iniciar Live: ' + str(getattr(getattr(e, 'error', None), 'code', 'error')))
        async def receive():
            first = False; last = time.monotonic(); deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                try:
                    e = await asyncio.wait_for(connection.recv(), timeout=1)
                except asyncio.TimeoutError:
                    if first and time.monotonic() - last > 4:
                        break
                    continue
                events[e.type] += 1
                if e.type == 'session.output_audio.delta':
                    pcm.extend(base64.b64decode(e.delta)); last = time.monotonic(); first = True
                elif e.type == 'session.output_transcript.delta':
                    transcript.append(e.delta)
                elif e.type == 'error':
                    errors.append(str(getattr(getattr(e, 'error', None), 'code', 'error')))
                    break
        receiver = asyncio.create_task(receive())
        raw += bytes(RATE * 2 * 2)
        for i in range(0, len(raw), 960):
            part = raw[i:i+960]
            await connection.session.input_audio.append(audio=base64.b64encode(part).decode('ascii'))
            await asyncio.sleep(len(part) / (RATE * 2))
        while not receiver.done():
            await connection.session.input_audio.append(audio=base64.b64encode(bytes(960)).decode('ascii'))
            await asyncio.sleep(0.02)
        await receiver
        await connection.session.close(event_id='fin_' + name)
    if errors:
        raise RuntimeError('Error de Live: ' + ', '.join(errors))
    audio = trim_pcm(bytes(pcm))
    wav = out_dir / (name + '.wav')
    with wave.open(str(wav), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(RATE); f.writeframes(audio)
    mp3 = out_dir / (name + '.mp3')
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error',
                    '-i', str(wav), '-b:a', '160k', str(mp3)], check=True)
    meta = {'id': name, 'texto': text, 'transcripcion_live': ''.join(transcript),
            'duracion_s': round(len(audio)/(RATE*2), 3), 'eventos': dict(events),
            'modelo': 'gpt-live-1', 'voz': 'willow'}
    (out_dir / (name + '.json')).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(name, 'segundos', meta['duracion_s'], 'transcripcion', meta['transcripcion_live'][:200], flush=True)


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--scene', default=''); a = ap.parse_args()
    scenes = json.loads((HERE/'guion_demo.json').read_text(encoding='utf-8-sig'))['escenas']
    scenes = [s for s in scenes if not a.scene or s['id'] == a.scene]
    if not scenes:
        raise SystemExit('Escena desconocida')
    key = config.obtener('OPENAI_API_KEY')
    if not key:
        raise SystemExit('No hay clave disponible para la voz')
    client = AsyncOpenAI(api_key=key, timeout=30)
    for scene in scenes:
        await render(client, scene)


if __name__ == '__main__':
    asyncio.run(main())
