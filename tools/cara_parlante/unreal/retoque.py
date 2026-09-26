"""Labios rosa claro, pecas/lunares y color de ojos. Lee retoque.json."""
import json
import unreal
D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'retoque.json'))
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')

mk = car.get_editor_property('makeup_settings')
lab = mk.get_editor_property('lips')
lab.set_editor_property('type', getattr(unreal.MetaHumanCharacterLipsMakeupType, cfg['labios_tipo']))
r, g, b = cfg['labios_color']
lab.set_editor_property('color', unreal.LinearColor(r, g, b, 1.0))
lab.set_editor_property('opacity', cfg['labios_opacidad'])
lab.set_editor_property('roughness', cfg['labios_rugosidad'])
lab.set_editor_property('metalness', 0.0)
mk.set_editor_property('lips', lab)
sub.commit_makeup_settings(car, mk)

piel = car.get_editor_property('skin_settings')
acc = piel.get_editor_property('accents')
z = acc.get_editor_property('lips')
for k, v in cfg['acento_labios'].items():
    z.set_editor_property(k, v)
acc.set_editor_property('lips', z)
piel.set_editor_property('accents', acc)
fr = piel.get_editor_property('freckles')
fr.set_editor_property('mask', getattr(unreal.MetaHumanCharacterFrecklesMask, cfg['pecas']['mask']))
for k in ('density', 'strength', 'saturation', 'tone_shift'):
    if k in cfg['pecas']:
        fr.set_editor_property(k, cfg['pecas'][k])
piel.set_editor_property('freckles', fr)
sub.commit_skin_settings(car, piel)

ojos = car.get_editor_property('eyes_settings')
for lado in ('eye_left', 'eye_right'):
    e = ojos.get_editor_property(lado)
    iris = e.get_editor_property('iris')
    for k, v in cfg['iris'].items():
        iris.set_editor_property(k, v)
    e.set_editor_property('iris', iris)
    ojos.set_editor_property(lado, e)
sub.commit_eyes_settings(car, ojos)
open(D + 'retoque.ok', 'w').write('ok')
