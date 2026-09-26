"""Renderiza la secuencia de Eos (Speech2Face) a PNG con Movie Render Queue.

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

# Movie Render Queue (plugin MovieRenderPipeline activado en el .uproject)
sub = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
cola = sub.get_queue()
for j in list(cola.get_jobs()):
    cola.delete_job(j)
trabajo = cola.allocate_new_job(unreal.MoviePipelineExecutorJob)
trabajo.sequence = unreal.SoftObjectPath(cfg['secuencia'])
trabajo.map = unreal.SoftObjectPath(cfg['mapa'])
conf = trabajo.get_configuration()
salida = conf.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
salida.output_directory = unreal.DirectoryPath(cfg['salida'])
salida.output_resolution = unreal.IntPoint(cfg.get('ancho', 1280), cfg.get('alto', 720))
salida.file_name_format = '{frame_number}'
salida.zero_pad_frame_numbers = 4
conf.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
conf.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
aa = conf.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.override_anti_aliasing = True
aa.spatial_sample_count = 1
aa.temporal_sample_count = cfg.get('muestras', 4)
# sin simulación del pelo (arrancaba desde reposo y el pelo volaba sobre la cara)
cv = conf.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
cv.add_or_update_console_variable('r.HairStrands.Simulation', 0)
cv.add_or_update_console_variable('r.MotionBlurQuality', 0)
ejecutor = sub.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)


def fin(ej, ok):
    open(D + 'eos_render.ok', 'w').write(json.dumps({'ok': bool(ok)}))


ejecutor.on_executor_finished_delegate.add_callable(fin)
