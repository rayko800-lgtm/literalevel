"""Prepara la escena de retrato de Eos para renderizar una secuencia de Speech2Face.

La secuencia exportada pone a la MetaHuman en (40, 0, 3) mirando a -X y su propia cámara
se descuadraba al capturar. Aquí: quita luces viejas, pone un fondo azul noche detrás de la
cabeza, luz de amanecer (llave cálida, relleno frío, contraluz dorado) del lado de la cámara
y una CineCamera propia, y hace que el corte de cámara de la secuencia use esa cámara.
Lee eos_render.json (clave "secuencia"). Escribe eos_escena.ok.
"""
import json

import unreal

D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'eos_render.json'))
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in acts.get_all_level_actors():
    if a.get_actor_label().startswith('Eos_'):
        acts.destroy_actor(a)

CABEZA = unreal.Vector(40.0, 0.5, 169.5)          # cara de la MetaHuman de la secuencia


def rotar_hacia(desde, hacia):
    return unreal.MathLibrary.find_look_at_rotation(desde, hacia)


# fondo: plano grande azul noche detrás de la cabeza
fondo = acts.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(160, 0, 160), unreal.Rotator(0, 90, 0))
fondo.set_actor_label('Eos_fondo')
fondo.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Plane'))
fondo.set_actor_rotation(unreal.Rotator(0, 90, 0), False)   # Rotator(roll, pitch, yaw): de pie, normal hacia -X
fondo.set_actor_scale3d(unreal.Vector(6, 6, 1))
mat = unreal.load_asset('/Engine/BasicShapes/BasicShapeMaterial')
mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_Eos_Fondo', '/Game/Eos', unreal.MaterialInstanceConstant,
                                                            unreal.MaterialInstanceConstantFactoryNew()) \
    if not unreal.EditorAssetLibrary.does_asset_exist('/Game/Eos/MI_Eos_Fondo') else unreal.load_asset('/Game/Eos/MI_Eos_Fondo')
mi.set_editor_property('parent', mat)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, 'Color', unreal.LinearColor(0.012, 0.02, 0.07, 1))
fondo.static_mesh_component.set_material(0, mi)

# luces (del lado de la cámara, fuera de cuadro)
for nombre, pos, color, inten, ancho in [
        ('Eos_llave', unreal.Vector(-30, -70, 210), unreal.Color(170, 214, 255, 255), 3.0, 60.0),   # BGRA: cálida
        ('Eos_relleno', unreal.Vector(-40, 80, 175), unreal.Color(255, 215, 195, 255), 1.0, 80.0),   # fría suave
        ('Eos_contra', unreal.Vector(110, 60, 220), unreal.Color(110, 190, 255, 255), 4.0, 40.0)]:  # dorada detrás
    luz = acts.spawn_actor_from_class(unreal.RectLight, pos, rotar_hacia(pos, CABEZA))
    luz.set_actor_label(nombre)
    c = luz.get_component_by_class(unreal.RectLightComponent)
    c.set_editor_property('light_color', color)
    c.set_editor_property('intensity', inten)
    c.set_editor_property('source_width', ancho)
    c.set_editor_property('source_height', ancho)
    c.set_editor_property('attenuation_radius', 600.0)

# cámara de retrato
pos_cam = unreal.Vector(-95, 0.5, 169.5)   # a la altura de los ojos: mira a cámara
cam = acts.spawn_actor_from_class(unreal.CineCameraActor, pos_cam, rotar_hacia(pos_cam, CABEZA))
cam.set_actor_label('Eos_camara')
cc = cam.get_cine_camera_component()
cc.set_editor_property('current_focal_length', 50.0)
fs = cc.get_editor_property('focus_settings')
fs.set_editor_property('manual_focus_distance', 135.0)
cc.set_editor_property('focus_settings', fs)
cc.set_editor_property('current_aperture', 2.8)
pp = cc.get_editor_property('post_process_settings')
pp.set_editor_property('override_motion_blur_amount', True)
pp.set_editor_property('motion_blur_amount', 0.0)
pp.set_editor_property('override_auto_exposure_bias', True)
pp.set_editor_property('auto_exposure_bias', -1.0)
cc.set_editor_property('post_process_settings', pp)

# corte de cámara → nuestra cámara
seq = unreal.load_asset(cfg['secuencia'].split('.')[0])
enlace = seq.add_possessable(cam)
corte = [t for t in seq.get_tracks() if isinstance(t, unreal.MovieSceneCameraCutTrack)]
corte = corte[0] if corte else seq.add_track(unreal.MovieSceneCameraCutTrack)
for s in list(corte.get_sections()):
    corte.remove_section(s)
sec = corte.add_section()
r = seq.get_playback_range()
sec.set_range(r.inclusive_start, r.exclusive_end)
sec.set_camera_binding_id(seq.get_portable_binding_id(seq, enlace) if hasattr(seq, 'get_portable_binding_id')
                          else unreal.MovieSceneSequenceExtensions.get_binding_id(seq, enlace))
unreal.EditorAssetLibrary.save_loaded_asset(seq)
unreal.EditorLoadingAndSavingUtils.save_current_level()
open(D + 'eos_escena.ok', 'w').write('ok')
