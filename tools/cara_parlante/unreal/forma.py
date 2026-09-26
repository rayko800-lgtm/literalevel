"""Esculpe la cara moviendo puntos de referencia (cm; x lado, y adelante, z arriba). Lee forma.json:
{"grupos": [{"idx": [62, 3], "d": [0, 0, 0.6], "escala": 1.0}, ...], "f": 1.0}
Aplicar después de mezcla.py, que deja la forma base."""
import json
import unreal
D = 'D:/literalevel_cara/ue/'
cfg = json.load(open(D + 'forma.json'))
sub = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
car = unreal.load_asset('/Game/Cara_LiteraLevel')
lm = list(sub.get_face_landmarks(car))
f = cfg.get('f', 1.0)
idx, deltas = [], []
for g in cfg['grupos']:
    for i in g['idx']:
        dx, dy, dz = [v * f for v in g['d']]
        if g.get('espejo') and lm[i].x < 0:   # los desplazamientos laterales se reflejan en el lado izquierdo
            dx = -dx
        idx.append(i)
        deltas.append(unreal.Vector(dx, dy, dz))
sub.translate_face_landmarks(car, idx, deltas)
sub.commit_face_state(car)
json.dump([[p.x, p.y, p.z] for p in sub.get_face_landmarks(car)], open(D + 'lm_despues.json', 'w'))
open(D + 'forma.ok', 'w').write('ok')
