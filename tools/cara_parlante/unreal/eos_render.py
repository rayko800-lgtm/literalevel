"""Renderiza la secuencia de Eos (Speech2Face) a PNG con la captura de Sequencer.

Lee D:/literalevel_cara/ue/eos_render.json: {"secuencia": "/Game/Eos/hola/LS_hola",
"mapa": "/Game/Eos/Escena", "salida": "D:/literalevel_cara/eos_demo/render/hola", "ancho": 1280, "alto": 720}
Guarda el nivel abierto como `mapa` (MRQ necesita un nivel guardado), añade una luz cálida de
amanecer y lanza el render en el editor. Escribe eos_render.ok al terminar.
"""
import json

import unreal

D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'eos_render.json'))
ed = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
mundo = ed.get_editor_world()

# luz de amanecer (una sola vez): llave cálida y relleno suave
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not any(a.get_actor_label().startswith('Eos_') for a in acts.get_all_level_actors()):
    for nombre, pos, rot, color, inten in [
            ('Eos_llave', (80, -120, 190), (0, -20, 125), (1.0, 0.82, 0.62), 12.0),
            ('Eos_relleno', (90, 130, 175), (0, -10, -130), (0.75, 0.82, 1.0), 4.0),
            ('Eos_contra', (-120, 40, 210), (0, -25, -20), (1.0, 0.75, 0.4), 10.0)]:
        luz = acts.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*pos), unreal.Rotator(*rot))
        luz.set_actor_label(nombre)
        c = luz.get_component_by_class(unreal.RectLightComponent)
        c.set_editor_property('light_color', unreal.Color(int(color[2] * 255), int(color[1] * 255), int(color[0] * 255), 255))
        c.set_editor_property('intensity', inten)
unreal.EditorLoadingAndSavingUtils.save_map(mundo, cfg['mapa'])

# Captura de Sequencer (viene con el motor; Movie Render Queue es un plugin aparte)
cap = unreal.AutomatedLevelSequenceCapture()
cap.level_sequence_asset = unreal.SoftObjectPath(cfg['secuencia'])
ajustes = cap.get_editor_property('settings')
ajustes.output_directory = unreal.DirectoryPath(cfg['salida'])
ajustes.output_format = '{frame}'
ajustes.resolution = unreal.CaptureResolution(cfg.get('ancho', 1280), cfg.get('alto', 720))
ajustes.overwrite_existing = True
ajustes.use_relative_frame_numbers = True
cap.set_editor_property('settings', ajustes)
cap.set_image_capture_protocol_type(unreal.ImageSequenceProtocol_PNG)


def fin(ok):
    open(D + 'eos_render.ok', 'w').write(json.dumps({'ok': bool(ok)}))


unreal.SequencerTools.render_movie(cap, unreal.OnRenderMovieStopped(fin))
