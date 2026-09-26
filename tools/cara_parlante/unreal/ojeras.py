"""Aclara párpados y ojeras: corrector del maquillaje y acento de bajo el ojo. Lee ojeras.json."""
import json
import unreal
D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'ojeras.json'))
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')
mk = car.get_editor_property('makeup_settings')
fo = mk.get_editor_property('foundation')
for k, v in cfg['base'].items():
    fo.set_editor_property(k, v)
mk.set_editor_property('foundation', fo)
sub.commit_makeup_settings(car, mk)
piel = car.get_editor_property('skin_settings')
acc = piel.get_editor_property('accents')
z = acc.get_editor_property('under_eye')
for k, v in cfg['bajo_ojo'].items():
    z.set_editor_property(k, v)
acc.set_editor_property('under_eye', z)
piel.set_editor_property('accents', acc)
sub.commit_skin_settings(car, piel)
open(D + 'ojeras.ok', 'w').write('ok')
