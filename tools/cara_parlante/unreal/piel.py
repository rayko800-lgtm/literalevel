"""Cambia solo el índice de textura de la cara (edad/detalle de la piel). Lee piel.json {"textura": n}."""
import json
import unreal
D = 'D:/literalevel_cara/ue/'
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')
piel = car.get_editor_property('skin_settings')
s = piel.get_editor_property('skin')
s.set_editor_property('face_texture_index', json.load(open(D + 'piel.json'))['textura'])
piel.set_editor_property('skin', s)
sub.commit_skin_settings(car, piel)
open(D + 'piel.ok', 'w').write(str(s.get_editor_property('face_texture_index')))
