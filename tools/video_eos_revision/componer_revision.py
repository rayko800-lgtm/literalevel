"""Monta la revisión 720p de Eos con pantallas oscuras fundidas al cielo.

Uso: python componer_revision.py --workdir D:/literalevel_video/comercial_revision_20260928
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import math
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from playwright.sync_api import sync_playwright

BG_SOURCE = Path('D:/literalevel_video/piloto_20260927/gptlive_piloto_20260927/fondo_formas_willow2.py')
APP_IMAGES = Path('D:/literalevel_video/comercial_completo_20260928/app_oscura')
FONT_PATH = 'C:/Windows/Fonts/segoeui.ttf'
BOLD_PATH = 'C:/Windows/Fonts/segoeuib.ttf'
W, H, FPS = 1280, 720, 24
SCREEN_X = 600
SCREEN_W = 700
FADE_SECONDS = 0.32
AVATAR_BRIGHTNESS = 0.82
# Segundos desde el inicio de cada escena. Cada cambio acompaña un gesto
# narrado; durante el resto de la frase, la interfaz permanece inmóvil.
SCREEN_CUES = {
    'buscar': [(0, '02_busqueda_inicio.png'),
               (1.82, '02_encontrar.png'),
               (6.14, '03_ficha.png')],
    'practica': [(0, '06_pronunciar_antes.png')],
    'eos_ingles': [(float(second), f'07_grabando_{second:02d}.png')
                   for second in range(8)] + [(8.05, '08_grabado.png')],
    'correccion': [(1.05, '09_corregido.png'), (6.6, '10_boca.png')],
}
_cache = {}
_mask_cache = {}


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def load_bg():
    spec = importlib.util.spec_from_file_location('eos_fondo', BG_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_screen(name):
    if name not in _cache:
        image = Image.open(APP_IMAGES / name).convert('RGBA')
        if image.size != (SCREEN_W, H):
            image = image.resize((SCREEN_W, H), Image.Resampling.LANCZOS)
        _cache[name] = image
    return _cache[name]


def screen_schedule(timeline):
    cues = []
    for scene in timeline:
        names = scene['pantallas']
        if not names:
            continue
        scene_cues = SCREEN_CUES.get(scene['id'], [(0, names[0])])
        for offset, name in scene_cues:
            if not 0 <= offset < scene['end'] - scene['start']:
                raise ValueError(f'Cue fuera de escena: {scene["id"]} {offset}')
            if name not in names and not (scene['id'] == 'eos_ingles' and
                                          name.startswith('07_grabando_')):
                raise ValueError(f'Pantalla inesperada: {scene["id"]} {name}')
            if not (APP_IMAGES / name).is_file():
                raise FileNotFoundError(APP_IMAGES / name)
            cues.append((scene['start'] + offset, name))
    shots = []
    for index, (start, name) in enumerate(cues):
        end = cues[index + 1][0] if index + 1 < len(cues) else timeline[-1]['start']
        shots.append((start, end, name))
    return shots


def visible_screen(t, shots):
    if not shots:
        return None, None, 0.0, 0.0
    for index, (start, end, name) in enumerate(shots):
        if start <= t < end:
            before = shots[index - 1][2] if index > 0 else None
            if t - start < FADE_SECONDS and before:
                elapsed = t - start
                # El contador de grabación cambia en la misma pantalla.
                if before.startswith('07_grabando_') and name.startswith('07_grabando_'):
                    return before, name, ease(elapsed / 0.15), 1.0
                # Entre vistas completas evitamos superponer textos y controles.
                half = FADE_SECONDS / 2
                if elapsed < half:
                    return before, None, 0.0, 1 - ease(elapsed / half)
                return name, None, 0.0, ease((elapsed - half) / half)
            opacity = 1.0
            if index == 0:
                opacity = min(opacity, ease((t - start) / FADE_SECONDS))
            if index == len(shots) - 1:
                opacity = min(opacity, ease((end - t) / FADE_SECONDS))
            return name, None, 0.0, opacity
    return None, None, 0.0, 0.0


def screen_mask(opacity):
    key = round(opacity * 100)
    if key not in _mask_cache:
        xx = np.arange(SCREEN_W, dtype=float)
        yy = np.arange(H, dtype=float)
        smooth = lambda value: np.clip(value, 0, 1) ** 2 * (3 - 2 * np.clip(value, 0, 1))
        horizontal = np.minimum(smooth(xx / 28), smooth((SCREEN_W - xx) / 18))
        vertical = np.minimum(smooth(yy / 12), smooth((H - yy) / 16))
        mask = np.rint(255 * key / 100 * vertical[:, None] * horizontal[None, :]).astype('uint8')
        _mask_cache[key] = Image.fromarray(mask, mode='L')
    return _mask_cache[key]


def overlay_screen(canvas, t, shots):
    first, second, mix, opacity = visible_screen(t, shots)
    if first is None or opacity <= 0:
        return
    app = get_screen(first)
    if second:
        app = Image.blend(app, get_screen(second), mix)
    canvas.paste(app, (SCREEN_X, 0), screen_mask(opacity))


def subtitles_at(t, events):
    for start, end, text in events:
        if start <= t < end:
            return text
    return ''


def load_subtitles(path):
    events = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.startswith('Dialogue: '):
            continue
        fields = line[len('Dialogue: '):].split(',', 9)
        def seconds(value):
            h, m, s = value.split(':')
            return 3600 * int(h) + 60 * int(m) + float(s)
        events.append((seconds(fields[1]), seconds(fields[2]), fields[-1]))
    return events


def add_subtitle(canvas, text, font):
    if not text:
        return
    layer = Image.new('RGBA', (W, H))
    draw = ImageDraw.Draw(layer)
    box = draw.textbbox((0, 0), text, font=font, stroke_width=1)
    width = box[2] - box[0]
    x = max(25, (W - width) // 2)
    y = 659
    draw.rounded_rectangle((x - 18, y - 8, x + width + 18, y + 41), radius=13,
                           fill=(5, 13, 35, 160))
    draw.text((x, y), text, font=font, fill=(255, 250, 247, 255),
              stroke_width=1, stroke_fill=(5, 13, 35, 255))
    canvas.alpha_composite(layer)


def qr_image():
    raw = cv2.QRCodeEncoder_create().encode('https://pleyade-app.vercel.app/')
    return Image.fromarray(raw).convert('RGB').resize((176, 176), Image.Resampling.NEAREST)


def add_close(canvas, t, timeline, qr, font):
    closing = timeline[-1]
    fade = ease((t - closing['start']) / 0.9)
    if fade <= 0:
        return
    layer = Image.new('RGBA', (W, H))
    icon = Image.open('D:/literalevel_cara/marca/pleyade_icono.png').convert('RGBA')
    icon.thumbnail((84, 84), Image.Resampling.LANCZOS)
    layer.alpha_composite(icon, (920, 150))
    draw = ImageDraw.Draw(layer)
    draw.text((792, 251), 'Abre tu próxima historia', font=font,
              fill=(255, 244, 235, 255))
    # El QR conserva un fondo claro para poder escanearse; no hay tarjeta alrededor.
    layer.paste(qr, (845, 338))
    draw.text((800, 534), 'pleyade-app.vercel.app', font=ImageFont.truetype(FONT_PATH, 24),
              fill=(255, 250, 246, 255))
    layer.putalpha(layer.getchannel('A').point(lambda a: round(a * fade)))
    canvas.alpha_composite(layer)


def make_frame(t, avatar, timeline, shots, subtitles, bg, qr, font, title_font):
    canvas = bg.frame(50 + t).convert('RGBA')
    overlay_screen(canvas, t, shots)
    if timeline[-1]['start'] <= t:
        add_close(canvas, t, timeline, qr, title_font)
    if avatar is not None:
        face = avatar.crop((230, 0, 1050, 720)).resize((650, 571), Image.Resampling.LANCZOS)
        face = ImageEnhance.Brightness(face).enhance(AVATAR_BRIGHTNESS)
        canvas.alpha_composite(face, (0, 110))
    add_subtitle(canvas, subtitles_at(t, subtitles), font)
    return canvas.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workdir', type=Path, required=True)
    parser.add_argument('--preview', type=float, nargs='+')
    parser.add_argument('--viewer-url', default='http://127.0.0.1:8772')
    parser.add_argument('--clip-start', type=float, default=0)
    parser.add_argument('--clip-duration', type=float)
    args = parser.parse_args()
    workdir = args.workdir
    timeline = json.loads((workdir / 'timeline.json').read_text(encoding='utf-8'))['escenas']
    shots = screen_schedule(timeline)
    subtitles = load_subtitles(workdir / 'subtitulos_revision.ass')
    duration = timeline[-1]['end']
    if duration > 300:
        raise RuntimeError(f'Excede los cinco minutos: {duration:.2f}s')
    clip_duration = args.clip_duration if args.clip_duration is not None else duration
    if args.clip_start < 0 or clip_duration <= 0 or args.clip_start + clip_duration > duration:
        raise ValueError('El intervalo de prueba debe estar dentro del comercial')
    bg = load_bg()
    qr = qr_image()
    font = ImageFont.truetype(FONT_PATH, 27)
    title_font = ImageFont.truetype(BOLD_PATH, 30)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    output = (workdir / f'piloto_{args.clip_start:g}_{clip_duration:g}_720p.mp4'
              if args.clip_duration is not None else workdir / 'eos_pleyade_revision_v3_720p.mp4')
    command = [ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
               '-ss', str(args.clip_start), '-i', str(workdir / 'audio_revision.wav'),
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
               '-profile:v', 'baseline', '-level:v', '3.1', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart',
               '-t', str(clip_duration), str(output)]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True,
                                     args=['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'])
        page = browser.new_page(viewport={'width': W, 'height': H})
        page.goto(f'{args.viewer_url}/index.html?grabar=.', wait_until='domcontentloaded')
        page.wait_for_function('window.listo === true', timeout=120000)
        page.add_style_tag(content='html,body{background:transparent!important} #titulo,#subt,#barra,#estado{display:none!important}')
        if args.preview is not None:
            for t in args.preview:
                page.evaluate('(t)=>window.pintar(t)', t)
                avatar = Image.open(io.BytesIO(page.screenshot(type='png', omit_background=True))).convert('RGBA')
                preview = workdir / f'preview_{t:.1f}.jpg'
                make_frame(t, avatar, timeline, shots, subtitles, bg, qr, font, title_font).save(preview, quality=90)
                print('PREVIEW', preview, flush=True)
        else:
            total = math.ceil(clip_duration * FPS)
            with subprocess.Popen(command, stdin=subprocess.PIPE) as process:
                for frame_index in range(total):
                    t = args.clip_start + frame_index / FPS
                    page.evaluate('(t)=>window.pintar(t)', t)
                    avatar = Image.open(io.BytesIO(page.screenshot(type='png', omit_background=True))).convert('RGBA')
                    frame = make_frame(t, avatar, timeline, shots, subtitles, bg, qr, font, title_font)
                    process.stdin.write(frame.tobytes())
                    if frame_index % 240 == 0:
                        print(f'FRAME {frame_index}/{total}', flush=True)
                process.stdin.close()
                if process.wait() != 0:
                    raise RuntimeError(f'ffmpeg falló con código {process.returncode}')
            print('VIDEO', output, output.stat().st_size, flush=True)
        browser.close()


if __name__ == '__main__':
    main()
