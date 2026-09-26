"""Tono de piel (u, v del mapa de color). Lee tono.json."""
import json
import unreal
D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'tono.json'))
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')
piel = car.get_editor_property('skin_settings')
s = piel.get_editor_property('skin')
for k, v in cfg.items():
    s.set_editor_property(k, v)
piel.set_editor_property('skin', s)
sub.commit_skin_settings(car, piel)
open(D + 'tono.ok', 'w').write('ok')
