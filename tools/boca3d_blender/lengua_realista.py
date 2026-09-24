"""Redondeo experimental de la lengua heredada, sin tocar assets de producción.

Blender 2.93 -b --python tools/boca3d_blender/lengua_realista.py
Salida: build/lengua_realista/. Geometría original, sin fotos incorporadas.
"""
import bpy
import json
import math
import os
import sys
import hashlib
import numpy as np
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.abspath(os.environ.get('SALIDA_LENGUA_REALISTA', os.path.join(ROOT, 'build', 'lengua_realista')))
SOURCE = os.path.join(ROOT, 'tools', 'boca3d_demo', 'lengua.glb')


def poses():
    base = os.path.join(ROOT, 'front', 'src', 'app', 'compartido', 'boca3d')
    with open(os.path.join(base, 'poses.ejemplo.json'), encoding='utf8') as f:
        cat = json.load(f)
    with open(os.path.join(base, 'poses.ajustes3d.json'), encoding='utf8') as f:
        extra = json.load(f)
    for symbol, changes in extra.get('sonidos', {}).items():
        cat['sonidos'][symbol].update(changes)
    for symbol, changes in extra.get('rp', {}).items():
        cat['rp'][symbol] = dict(cat['rp'].get(symbol, cat['sonidos'].get(symbol, {})), **changes)
    return dict(reposo=cat['reposo'], **cat['sonidos'], **{'rp:' + k: v for k, v in cat['rp'].items()})


def weights(p):
    if '__weights' in p:
        return p['__weights']
    alt, ade = p['cuerpo']
    tip = p['punta']
    return [0.3 * min(1, max(0, p['mandibula'])),
            ((1 if tip == 'alveolar' else .85) if p['punta_toca'] else .75)
            if tip in ('alveolar', 'postalveolar') else .45 if tip == 'dental' else 0,
            1 if tip == 'retrofleja' else 0, 1 if tip == 'interdental' else 0,
            max(0, (alt - .45) / .55), max(0, (.45 - alt) / .45),
            max(0, (ade - .5) / .5), max(0, (.5 - ade) / .5),
            1 if p['dorso_velo'] else .9 * min(1, p['dorso_alto']), min(1, max(0, p['raiz']))]


def samples(catalog):
    result = dict(catalog)
    rest = catalog['reposo']
    for symbol, pose in catalog.items():
        if pose.get('hacia'):
            result[symbol + ':destino'] = pose['hacia']
        for name, start, end in [('entrada', rest, pose), ('deslizamiento', pose, pose.get('hacia'))]:
            if not end:
                continue
            for t in (.25, .5, .75):
                mixed = dict(end)
                mixed['mandibula'] = start['mandibula']*(1-t)+end['mandibula']*t
                mixed['__weights'] = [a*(1-t)+b*t for a,b in zip(weights(start), weights(end))]
                result[symbol + ':' + name + str(t)] = mixed
    return result


def dental_penalty(points, upper):
    """Misma envolvente conservadora (coronas antiguas) que lengua.py."""
    x, lat, height = points.T
    u = np.linspace(-1, 1, 61)
    def tube(center, radius, back=2.3):
        return radius - np.sqrt((x[:, None] - (-2.6 + back * abs(u) ** 2.6)) ** 2
                                + (lat[:, None] - 1.35 * u) ** 2
                                + (height[:, None] - center) ** 2).min(axis=1)
    penalty = tube(.98 if upper else -.2, .2)
    if not upper:
        penalty = np.maximum(penalty, tube(-.62, .28, 2.6))
    for t in [-.92, -.76, -.6, -.44, -.28, -.1, .1, .28, .44, .6, .76, .92]:
        width, depth = (.34, .24) if abs(t) < .3 else (.34, .3) if abs(t) < .5 else (.38, .36) if abs(t) < .85 else (.46, .42)
        angle = -math.atan2(2.3 * 2.6 * abs(t) ** 1.6 * np.sign(t), 1.35)
        dx, dl = x - (-2.6 + 2.3 * abs(t) ** 2.6), lat - 1.35 * t
        lx = dx * math.cos(angle) + dl * math.sin(angle)
        ly = -dx * math.sin(angle) + dl * math.cos(angle)
        tooth = np.minimum(np.minimum(depth / 2 - abs(lx), width / 2 - abs(ly)), .25 - abs(height - (.7 if upper else .1)))
        penalty = np.maximum(penalty, tooth)
    skip = (height < .3) | ((abs(lat) < .5) & (x > -2.2)) if upper else (height > .5) | ((abs(lat) < .5) & (height > -.25) & (x > -2.2))
    penalty[skip] = -9
    return penalty


def roof(x, opened):
    profile = np.array([[-2.55,.5],[-2.3,.75],[-2.05,.92],[-1.7,1.15],[-1.2,1.35],[-.6,1.48],
                        [0,1.52],[.6,1.5],[1.2,1.42],[1.7,1.32],[2.05,1.22]])
    result = np.interp(x, profile[:,0], profile[:,1]) - .13
    result[x <= -2.55] = 8.87
    angle = -1.22 if opened else -.44
    soft = np.ones_like(x) * 9
    for f in np.linspace(0, 1, 11):
        px, pz = 2.05 + math.cos(angle)*1.2*f, 1.22+math.sin(angle)*1.2*f
        soft = np.where(abs(px-x) < .25, np.minimum(soft, pz-math.cos(angle)*.13), soft)
    result[x > 2.05] = soft[x > 2.05]
    return result


def metrics(arrays, catalog):
    result = {}
    for symbol, p in catalog.items():
        influence = np.array(weights(p))
        local = arrays[0] + np.einsum('i,ijk->jk', influence, arrays[1:]-arrays[0])
        angle = min(1, max(0, p['mandibula']))*.21
        c, s = math.cos(angle), math.sin(angle)
        world = local.copy()
        world[:,0] = 2.6+(local[:,0]-2.6)*c-(local[:,2]-.9)*s
        world[:,2] = .9+(local[:,0]-2.6)*s+(local[:,2]-.9)*c
        top = world[:,2]-roof(world[:,0], p['velo_abierto'])
        front = world[world[:,0] < world[:,0].min()+.1]
        result[symbol] = {'techo': float(top.max()),
                          'diente_sup': float(dental_penalty(world, True).max()),
                          'diente_inf': float(dental_penalty(local, False).max()),
                          'frente': float(world[:,0].min()),
                          'punta_abajo': float(front[:,2].min()), 'punta_arriba': float(front[:,2].max())}
    return result


def main():
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SOURCE, merge_vertices=True)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.data.shape_keys)
    keys = ob.data.shape_keys.key_blocks
    before = np.array([[tuple(p.co) for p in k.data] for k in keys], dtype=np.float64)
    print('TONGUE_SOURCE', before.shape, [k.name for k in keys], before[0].min(axis=0), before[0].max(axis=0), tuple(ob.rotation_euler))
    after = before.copy()
    # La clave heredada cuerpo_bajo se recortó contra cinco desplazamientos
    # incompatibles simultáneos. Su empuje discreto de .02 creó una pared
    # de .60 en la punta. Separar cizalla continua y corrección de colisión
    # permite redondear la corrección sin suavizar toda la malla.
    low = [k.name for k in keys].index('cuerpo_bajo')
    after[low] = before[0]
    after[low, :, 2] -= .7 * np.exp(-((before[0, :, 0] - .1) / 1.3) ** 2)
    jaw = [k.name for k in keys].index('mandibula')
    root = np.clip((before[0, :, 0] - .8) / 1.6, 0, 1)
    root = root * root * (3 - 2 * root)
    after[jaw] = before[0]
    after[jaw, :, 2] -= .55 * (.35 + .65 * root)
    # Difundir sólo la corrección de seguridad, nunca la superficie base:
    # reemplaza los saltos por una transición suave; volumen y grosor se
    # comprueban aparte con medir_lengua.mjs, sin relajar sus tolerancias.
    edges = np.array([tuple(e.vertices) for e in ob.data.edges])
    source = np.concatenate((edges[:,0], edges[:,1]))
    target = np.concatenate((edges[:,1], edges[:,0]))
    degree = np.bincount(source, minlength=len(before[0]))[:,None]
    for idx in (jaw, low):
        correction = before[idx] - after[idx]
        for _ in range(80):
            total = np.zeros_like(correction)
            np.add.at(total, source, correction[target])
            correction = .3 * correction + .7 * total / degree
        after[idx] += correction
    # La difusión elimina el grosor artificial del escalón. Reponer un pequeño
    # volumen oval en el tercio anterior, con continuidad, mantiene una punta
    # roma. Las tres claves de contacto conservan su superficie original.
    front = np.exp(-((before[0, :, 0] + 1.72) / .42) ** 4)
    thickness = .14 * (before[0, :, 2] + .45) * front
    for idx, key in enumerate(keys):
        if key.name not in ('punta_arriba', 'punta_atras', 'punta_interdental'):
            after[idx, :, 2] += thickness
    catalog = samples(poses())
    report = {'antes': metrics(before, catalog), 'despues': metrics(after, catalog)}
    report['max_delta'] = float(np.linalg.norm(after-before, axis=2).max())
    report['claves'] = [k.name for k in keys]
    report['estados'] = len(catalog)
    assert np.isfinite(after).all()
    edge_uses = {}
    for poly in ob.data.polygons:
        ids = list(poly.vertices)
        for a,b in zip(ids, ids[1:]+ids[:1]):
            edge = tuple(sorted((a,b)))
            edge_uses[edge] = edge_uses.get(edge, 0)+1
    report['aristas_no_manifold'] = sum(n != 2 for n in edge_uses.values())
    assert not report['aristas_no_manifold']
    report['bounds_claves'] = {k.name: [after[i].min(axis=0).tolist(), after[i].max(axis=0).tolist()]
                              for i,k in enumerate(keys)}
    regressions = []
    for symbol, p in catalog.items():
        old, new = report['antes'][symbol], report['despues'][symbol]
        for name, tolerance in [('techo', .08 if p['punta_toca'] or p['dorso_velo'] else 0),
                                ('diente_sup', .08 if p['punta'] == 'interdental' else 0),
                                ('diente_inf', .08 if p['punta'] == 'interdental' else 0)]:
            if new[name] > max(tolerance, old[name])+.002:
                regressions.append([symbol, name, old[name], new[name]])
    report['regresiones_contacto'] = regressions
    with open(os.path.join(OUT, 'medidas.json'), 'w', encoding='utf8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    assert not regressions, regressions[:10]
    print('WORST_BEFORE', max((v['diente_inf'], k) for k,v in report['antes'].items()))
    print('WORST_AFTER', max((v['diente_inf'], k) for k,v in report['despues'].items()))
    for i, key in enumerate(keys):
        for j, p in enumerate(key.data):
            p.co = after[i, j]
    for poly in ob.data.polygons:
        poly.use_smooth = True
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'lengua.glb'), export_format='GLB',
                             export_yup=True, export_morph=True, export_morph_normal=False,
                             export_extras=True, export_materials='EXPORT')
    with open(os.path.join(OUT, 'lengua.glb'), 'rb') as f:
        output_bytes = f.read()
    report['glb_bytes'] = len(output_bytes)
    report['glb_sha256'] = hashlib.sha256(output_bytes).hexdigest()
    with open(os.path.join(OUT, 'medidas.json'), 'w', encoding='utf8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'lengua.blend'))
    # Short, deterministic material preview, not a representation of final lighting.
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.light = 'STUDIO'
    scene.display.shading.studiolight_rotate_z = .35
    scene.display.shading.color_type = 'SINGLE'
    scene.display.shading.single_color = (.58, .16, .23)
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = 'WORLD'
    scene.display.shading.background_type = 'WORLD'
    scene.world = bpy.data.worlds.new('Fondo comparacion')
    scene.world.color = (.05, .05, .05)
    scene.render.resolution_x = 720
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    cam_data = bpy.data.cameras.new('Comparacion')
    cam = bpy.data.objects.new('Comparacion', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 5
    cam.location = (-8, -4, 5)
    target = Vector((.1, 0, -.35))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for name, arrays in [('antes', before), ('despues', after)]:
        for i, key in enumerate(keys):
            for j, p in enumerate(key.data):
                p.co = arrays[i, j]
        for pose in ('reposo', 'æ', 'θ', 't'):
            for key, weight in zip(list(keys)[1:], weights(poses()[pose])):
                key.value = weight
            scene.render.filepath = os.path.join(OUT, name + '-' + {'æ':'ae', 'θ':'theta'}.get(pose, pose) + '.png')
            bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
