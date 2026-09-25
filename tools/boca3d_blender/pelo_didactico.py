"""Pelo ilustrativo sobre la cabeza didáctica (24 sep 2026, petición de Miguel).

La cabeza escaneada es rapada y, al alejar la cámara, se veía un maniquí
extraño. Se añade una capa de pelo corto: el cuero cabelludo de cada mitad del
exterior, subdividido (la malla del escaneo es gruesa y el borde salía en
escalones) y desplazado hacia fuera desde el centro de la cabeza. El grosor es
mayor en la coronilla y llega a cero en el nacimiento, así que el borde se
funde con la piel en vez de cortar en seco. Pieza fija: no toca la boca.

Coordenadas del exterior (Blender): x delante(-)/detrás(+), y lateral, z arriba.
"""
import bmesh
import bpy
from mathutils import Vector


def _suave(t):
    t = max(0., min(1., t))
    return t * t * (3 - 2 * t)


# Nacimiento del pelo (altura z) según la posición delante-detrás (x):
# frente, entradas, sobre las orejas y nuca. Valores de ilustración.
# Medido sobre la malla: ojos a z≈3,4, orejas de z≈1,8 a 3,4 (x 0,5-1,6),
# coronilla a 7,8.
_NACIMIENTO = [(-3.2, 5.05), (-2.2, 4.85), (-1.2, 4.35), (-0.2, 3.8), (0.6, 3.65),
               (1.6, 3.55), (2.4, 2.9), (3.4, 1.8), (4.6, 1.15), (6.5, 1.0)]
CENTRO = Vector((1.2, 0.0, 3.6))     # centro aproximado del cráneo


def nacimiento(x):
    if x <= _NACIMIENTO[0][0]:
        return _NACIMIENTO[0][1]
    for (x0, z0), (x1, z1) in zip(_NACIMIENTO, _NACIMIENTO[1:]):
        if x <= x1:
            return z0 + (z1 - z0) * _suave((x - x0) / (x1 - x0))
    return _NACIMIENTO[-1][1]


def _alto(p):
    """Altura sobre el nacimiento; negativa en la cara y en las orejas."""
    if abs(p.y) > 2.6 and -0.2 < p.x < 2.1 and p.z < 3.5:
        return -1.
    # Entradas: en la frente el nacimiento sube un poco hacia las sienes, para
    # que no salga un flequillo recto de casco.
    frente = _suave((-1.0 - p.x) / 1.6)
    return p.z - nacimiento(p.x) - frente * 0.4 * min(1., abs(p.y) / 1.7) ** 2


def construir():
    for fuente in ('exterior_cercana', 'exterior_lejana'):
        ob = bpy.data.objects.get(fuente)
        if ob is None:
            continue
        mw = ob.matrix_world
        bm = bmesh.new()
        bm.from_mesh(ob.data)                 # posiciones de reposo (clave base)
        bmesh.ops.transform(bm, matrix=mw, verts=bm.verts)
        # Solo las caras que tocan el cuero cabelludo (con margen bajo el borde).
        fuera = [f for f in bm.faces if max(_alto(v.co) for v in f.verts) < -0.45]
        bmesh.ops.delete(bm, geom=fuera, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=2, use_grid_fill=True)
        capa = bm.verts.layers.float.new('borde')
        for v in bm.verts:
            h = _alto(v.co)
            borde = _suave((h + 0.3) / 0.8)            # 0 bajo el nacimiento
            corona = _suave((v.co.z - 4.2) / 3.0)      # más volumen arriba
            grosor = borde * (0.10 + 0.22 * corona)
            fuera_dir = (v.co - CENTRO).normalized()
            v.co = v.co + fuera_dir * grosor
            v[capa] = borde
        # Quitar lo que queda muy por debajo (grosor 0, superpuesto a la piel);
        # el borde visible lo dibuja el visor con el color por vértice.
        sobra = [f for f in bm.faces if max(v[capa] for v in f.verts) <= 0.0]
        bmesh.ops.delete(bm, geom=sobra, context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        mesh = bpy.data.meshes.new('pelo_' + fuente.split('_')[1])
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        for poly in mesh.polygons:
            poly.use_smooth = True
        color = mesh.vertex_colors.new(name='pelo')
        for loop in mesh.loops:
            p = mesh.vertices[loop.vertex_index].co
            b = _suave((_alto(p) + 0.3) / 0.8)
            color.data[loop.index].color = (b, b, b, 1.)
        mat = bpy.data.materials.new('pelo')
        mat.diffuse_color = (.07, .05, .04, 1)
        mesh.materials.append(mat)
        pelo = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(pelo)
    print('PELO_OK')
