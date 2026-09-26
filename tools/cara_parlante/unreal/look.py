"""Piel clara y luminosa, labios con algo de brillo, pestañas visibles. Lee look.json."""
import json
import unreal

cfg = json.load(open('D:/literalevel_cara/ue/look.json'))
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')

piel = car.get_editor_property('skin_settings')
s = piel.get_editor_property('skin')
s.set_editor_property('u', cfg['u'])
s.set_editor_property('v', cfg['v'])
s.set_editor_property('roughness', cfg['rugosidad'])
if 'textura' in cfg:
    s.set_editor_property('face_texture_index', cfg['textura'])
piel.set_editor_property('skin', s)
acc = piel.get_editor_property('accents')
for zona, vals in cfg.get('acentos', {}).items():
    z = acc.get_editor_property(zona)
    for k, v in vals.items():
        z.set_editor_property(k, v)
    acc.set_editor_property(zona, z)
piel.set_editor_property('accents', acc)
sub.commit_skin_settings(car, piel)

mk = car.get_editor_property('makeup_settings')
lab = mk.get_editor_property('lips')
lab.set_editor_property('type', getattr(unreal.MetaHumanCharacterLipsMakeupType, cfg['labios_tipo']))
lab.set_editor_property('opacity', cfg['labios_opacidad'])
lab.set_editor_property('roughness', cfg['labios_rugosidad'])
lab.set_editor_property('metalness', 0.0)
mk.set_editor_property('lips', lab)
sub.commit_makeup_settings(car, mk)
open('D:/literalevel_cara/ue/look.ok', 'w').write('ok')
