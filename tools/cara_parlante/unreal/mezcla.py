"""Mezcla la cara de Vivian con otros preajustes de MetaHuman.

La media de varias caras suaviza rasgos marcados (efecto de promedio). Uso desde la
consola de Unreal:  py "D:/literalevel_cara/ue/mezcla.py"  (lee receta.json)
receta.json: {"base": 0.5, "otras": ["Ada", "Celeste"]}           (media simple)
         o   {"base": 0.2, "pesos": {"Aoi": 2, "Lani": 1}}         (media ponderada)
Los coeficientes de cada preajuste se guardan en presets/<Nombre>.json.
"""
import json
import os
import unreal

D = 'D:/literalevel_cara/ue/'
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
receta = json.load(open(D + 'receta.json'))
viv = json.load(open(D + 'viv_coef.json'))   # Vivian original, guardada antes
pesos = receta.get('pesos') or {n: 1 for n in receta['otras']}
os.makedirs(D + 'presets', exist_ok=True)


def coef(n):
    f = D + 'presets/' + n + '.json'
    if os.path.exists(f):
        return json.load(open(f))
    a = unreal.load_asset('/MetaHumanCharacter/Optional/Presets/' + n)
    sub.try_add_object_to_edit(a)
    c = list(sub.get_face_model_coefficients(a))
    sub.remove_object_to_edit(a)
    json.dump(c, open(f, 'w'))
    return c


tot = sum(pesos.values())
media = [0.0] * len(viv)
for n, p in pesos.items():
    c = coef(n)
    for i in range(len(viv)):
        media[i] += p / tot * c[i]
w = receta['base']
nuevo = [w * viv[i] + (1 - w) * media[i] for i in range(len(viv))]
car = unreal.load_asset('/Game/Cara_LiteraLevel')
sub.set_face_model_coefficients(car, nuevo)
sub.commit_face_state(car)
open(D + 'mezcla.ok', 'w').write(json.dumps(receta))
