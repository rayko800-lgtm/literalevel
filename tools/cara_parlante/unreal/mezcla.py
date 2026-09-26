"""Mezcla la cara de Vivian con la media de otros preajustes femeninos.

La media de varias caras suaviza rasgos marcados (efecto de promedio): mandíbula
y pómulos menos angulosos, forma más ovalada. Uso desde la consola de Unreal:
  py "D:/literalevel_cara/ue/mezcla.py"   (lee la receta de D:/literalevel_cara/ue/receta.json)
receta.json: {"base": 0.5, "otras": ["Ada", "Celeste"]}
"""
import json
import unreal

sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
receta = json.load(open('D:/literalevel_cara/ue/receta.json'))
viv = json.load(open('D:/literalevel_cara/ue/viv_coef.json'))   # Vivian original, guardada antes
otras = []
for n in receta['otras']:
    a = unreal.load_asset('/MetaHumanCharacter/Optional/Presets/' + n)
    sub.try_add_object_to_edit(a)
    otras.append(list(sub.get_face_model_coefficients(a)))
    sub.remove_object_to_edit(a)
w = receta['base']
media = [sum(o[i] for o in otras) / len(otras) for i in range(len(viv))]
nuevo = [w * viv[i] + (1 - w) * media[i] for i in range(len(viv))]
car = unreal.load_asset('/Game/Cara_LiteraLevel')
sub.set_face_model_coefficients(car, nuevo)
sub.commit_face_state(car)
open('D:/literalevel_cara/ue/mezcla.ok', 'w').write(json.dumps(receta))
