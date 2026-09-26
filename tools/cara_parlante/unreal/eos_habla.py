"""Eos habla en Unreal con todo el potencial: audio → animación facial completa (MetaHuman
Animator, Speech2Face, local y gratis) → secuencia con la MetaHuman ensamblada → vídeo.

Uso desde la consola del editor:  py "D:/.../eos_habla.py"   (lee D:/literalevel_cara/ue/eos_habla.json)
eos_habla.json: {"clips": ["hola", "alicia"], "wav_dir": "D:/literalevel_cara/eos_demo",
                 "bp": "/Game/Cara_LiteraLevel/BP_Cara_LiteraLevel", "animo": "Happiness", "intensidad": 0.6}
Por cada clip deja /Game/Eos/<clip>/ con SoundWave, Performance y LevelSequence, y escribe
D:/literalevel_cara/ue/eos_habla.ok con lo hecho (o el error).
"""
import json
import traceback

import unreal

D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'eos_habla.json'))
herr = unreal.AssetToolsHelpers.get_asset_tools()
informe = {'moods': [m for m in dir(unreal.AudioDrivenAnimationMood) if m.isupper()], 'clips': {}}


def importar_wav(ruta, destino, nombre):
    t = unreal.AssetImportTask()
    t.filename = ruta
    t.destination_path = destino
    t.destination_name = nombre
    t.automated = True
    t.replace_existing = True
    t.save = True
    herr.import_asset_tasks([t])
    return unreal.load_asset(f'{destino}/{nombre}')


for clip in cfg['clips']:
    dest = f'/Game/Eos/{clip}'
    r = informe['clips'].setdefault(clip, {})
    try:
        onda = importar_wav(f"{cfg['wav_dir']}/{clip}/voz.wav", dest, f'SW_{clip}')
        perf = unreal.load_asset(f'{dest}/MHP_{clip}') or herr.create_asset(
            f'MHP_{clip}', dest, unreal.MetaHumanPerformance, None)
        perf.set_editor_property('input_type', unreal.DataInputType.AUDIO)
        perf.set_editor_property('audio', onda)
        perf.set_editor_property('generate_blinks', True)
        try:   # el ánimo solo se expone para audio en tiempo real en algunas versiones; se intenta
            ov = perf.get_editor_property('audio_driven_animation_solve_overrides')
            ov.set_editor_property('mood', getattr(unreal.AudioDrivenAnimationMood, cfg.get('animo', 'AUTO_DETECT').upper()))
            ov.set_editor_property('mood_intensity', cfg.get('intensidad', 0.6))
            perf.set_editor_property('audio_driven_animation_solve_overrides', ov)
            r['animo'] = cfg.get('animo')
        except Exception as e:
            r['animo_error'] = str(e)[:200]
        perf.set_blocking_processing(True)
        err = perf.start_pipeline(True)
        r['pipeline'] = str(err)
        r['fotogramas'] = perf.get_number_of_processed_frames()
        ajustes = unreal.MetaHumanPerformanceExportUtils.get_export_level_sequence_settings(perf)
        ajustes.set_editor_property('show_export_dialog', False)
        ajustes.set_editor_property('package_path', dest)
        ajustes.set_editor_property('asset_name', f'LS_{clip}')
        ajustes.set_editor_property('target_meta_human_class', unreal.load_asset(cfg['bp']))
        try:
            ajustes.set_editor_property('enable_head_movement', True)
        except Exception:
            pass
        sec = unreal.MetaHumanPerformanceExportUtils.export_level_sequence(perf, ajustes)
        r['secuencia'] = sec.get_path_name() if sec else None
        unreal.EditorAssetLibrary.save_directory(dest)
    except Exception:
        r['error'] = traceback.format_exc()[-1500:]

json.dump(informe, open(D + 'eos_habla.ok', 'w'), indent=1)
