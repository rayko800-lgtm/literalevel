"""Tejidos del corte didáctico; unidades y contactos del rig existente.

El espesor añadido es una decisión de ilustración, no una medición clínica.
Las secciones labiales se derivan de los mismos vértices/morfos del exterior.
"""
import math
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon


def curva(puntos, pasos=8):
    out = []
    for i in range(len(puntos)-1):
        ps = [puntos[max(0,i-1)], puntos[i], puntos[i+1], puntos[min(len(puntos)-1,i+2)]]
        for k in range(pasos):
            t=k/pasos
            out.append(tuple(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
                             for a,b,c,d in zip(*ps)))
    return out+[puntos[-1]]


def tejido(nombre, contorno, profundidad=.65, color=(.68,.40,.38)):
    """Sección cerrada en el plano medio; volumen hacia la mitad lejana."""
    n=len(contorno)
    vertices=[(x,lat,y) for lat in (0.,profundidad) for x,y in contorno]
    poly=[Vector((x,y,0)) for x,y in contorno]
    tris=tessellate_polygon([poly])
    faces=[tuple(t) for t in tris]+[tuple(n+i for i in reversed(t)) for t in tris]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh=bpy.data.meshes.new(nombre);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(nombre,mesh);bpy.context.collection.objects.link(ob)
    mat=bpy.data.materials.new(nombre+'_tejido');mat.diffuse_color=(*color,1)
    mat.use_nodes=True; bsdf=mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.76
    mesh.materials.append(mat)
    # Caras del corte planas, pared curva suave; evita apariencia de manguera.
    for p in mesh.polygons:p.use_smooth=p.index>=2*len(tris)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
    return ob


def construir():
    paladar=[(-2.55,.5),(-2.3,.75),(-2.05,.92),(-1.7,1.15),(-1.2,1.35),
             (-.6,1.48),(0,1.52),(.6,1.5),(1.2,1.42),(1.7,1.32),(2.05,1.22)]
    centro=curva(paladar)
    # Misma envolvente oral central que perfil(grosor=.13) del generador v8.
    oral=[]
    for i,(x,y) in enumerate(centro):
        a,b=centro[max(0,i-1)],centro[min(len(centro)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1]; l=math.hypot(dx,dy)
        oral.append((x+dy/l*.13,y-dx/l*.13))
    nasal=curva([(-2.75,1.45),(-2.4,1.66),(-1.5,1.81),(0,1.86),(1.2,1.77),(2.05,1.35)])
    tejido('anatomia_paladar',oral+list(reversed(nasal)),.95)
    # Un solo revestimiento desde la cavidad nasal a la faringe.
    pared=curva([(-2.2,3.),(-1.4,2.85),(.4,2.8),(1.8,2.6),(2.8,2.1),
                 (3.05,1.55),(3.16,.6),(3.08,-.55),(2.95,-1.65),(2.8,-2.5),(2.75,-3.1)])
    exterior=[];interior=[]
    for i,(x,y) in enumerate(pared):
        a,b=pared[max(0,i-1)],pared[min(len(pared)-1,i+1)]
        dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy)
        radio=.11 if y>2.1 else .15
        interior.append((x+dy/l*radio,y-dx/l*radio))
        exterior.append((x-dy/l*.16,y+dx/l*.16))
    tejido('anatomia_pared',interior+list(reversed(exterior)),.8,(.71,.45,.43))
    # Suelo muscular apoyado en la mandíbula, continuo hasta la raíz.
    arriba=curva([(-2.55,-.26),(-2.25,-.72),(-1.55,-.90),(-.4,-1.05),(1.2,-1.16),(2.15,-1.55)])
    abajo=curva([(-2.55,-.65),(-2.15,-1.23),(-1.4,-1.52),(0,-1.72),(1.4,-1.83),(2.15,-1.55)])
    tejido('anatomia_suelo',arriba+list(reversed(abajo[:-1])),.8,(.72,.44,.41))
    tejido('anatomia_maxilar',curva([(-2.93,.81),(-2.96,1.15),(-2.9,1.51),(-2.55,1.65)])
           +[(-2.35,1.35),(-2.55,.82)],.45,(.80,.60,.52))
    tejido('anatomia_menton',curva([(-2.93,-.69),(-2.89,-1.10),(-2.65,-1.50),(-1.9,-1.75),(-.4,-1.81)])
           +[(-.4,-1.40),(-1.55,-1.12),(-2.3,-.84),(-2.63,-.50)],.45,(.80,.60,.52))
    tejido('anatomia_alveolo_sup',curva([(-2.77,.78),(-2.72,1.01),(-2.50,1.24),(-2.24,1.19)])
           +[(-2.37,.77)],.36,(.79,.48,.47))
    tejido('anatomia_alveolo_inf',curva([(-2.77,-.06),(-2.70,-.52),(-2.47,-.85),(-2.19,-.84)])
           +[(-2.35,-.12)],.36,(.79,.48,.47))
    # Velo local al pivote. Superficie oral conserva el espesor previo .13.
    abajo=curva([(-.08,-.13),(.35,-.13),(.7,-.145),(1.12,-.16)])
    arriba=curva([(-.08,.14),(.35,.13),(.7,.105),(1.12,.055)])
    tejido('anatomia_velo',abajo+list(reversed(arriba)),.62,(.69,.39,.38))
    tejido('anatomia_uvula',curva([(.91,-.13),(.96,-.31),(1.08,-.44),(1.16,-.37),(1.17,-.18)])
           +[(1.12,-.10)],.07,(.70,.37,.37))
    # Copia exacta del borde sagital, incluyendo TODAS las shape keys.
    fuente=bpy.data.objects['exterior_cercana']; keys=fuente.data.shape_keys.key_blocks
    for nombre,q in [('anatomia_labio_sup',64),('anatomia_labio_inf',0)]:
        ids=[ri*65+q for ri in range(7)]
        base=[keys[0].data[i].co.copy() for i in ids]
        sup=q==64
        interior=[(-2.66,.82),(-2.73,.46)] if sup else [(-2.63,-.50),(-2.72,-.12)]
        contorno=[(p.x,p.z) for p in base]+interior
        ob=tejido(nombre,contorno,.025,(.73,.43,.41))
        from perioral_didactico import SUAVIDAD_MANDIBULA
        ob.data.uv_layers.new(name='UVMap')
        rig=ob.data.uv_layers.new(name='RigMandibula')
        # Distinguir la raiz cutanea del bermellon sin cambiar el contorno.
        # Son colores de ilustracion, no regiones histologicas.
        region=ob.data.vertex_colors.new(name='region_labial')
        colores=[(.72,.45,.44),(.72,.44,.43),(.68,.38,.39),(.72,.46,.44),
                 (.77,.60,.54),(.78,.65,.58),(.78,.66,.59),(.78,.65,.58),(.72,.46,.44)]
        for loop in ob.data.loops:
            j=loop.vertex_index%len(contorno)
            region.data[loop.index].color=(*colores[j],1.)
            # Raíz estable: -1 maxilar fijo, -2 mandíbula rígida. El visor
            # interpreta estos marcadores; 0..6 conserva el campo exterior.
            rig.data[loop.index].uv=(SUAVIDAD_MANDIBULA[j] if j<7 else (-1. if sup else -2.),0.)
        ob.shape_key_add(name='Basis')
        for key in list(keys)[1:]:
            target=ob.shape_key_add(name=key.name)
            for j,i in enumerate(ids):
                delta=key.data[i].co-keys[0].data[i].co
                for off in (0,len(contorno)):target.data[j+off].co+=delta
            # Los dos puntos internos se insertan en maxilar/mandíbula.
            # No suman gestos labiales: eso separaba la raíz del mentón.
        ob['borde_compartido']=1
    print('INTERIOR_DIDACTICO_OK')
