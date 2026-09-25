"""Correspondencia superficial con el escaneo LPS (CC BY 3.0).

Injerta la superficie escaneada en el borde articulatorio conservado. Usa una
textura afeitada derivada de Map-COL; origen y prompt en texturas/README.md.
No es una reconstrucción clínica ni una simulación de dispersión de luz.
"""
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


class AparienciaEscaneo:
    def __init__(self):
        root = Path(__file__).resolve().with_name('lps')
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(root / 'LeePerrySmith.glb'))
        nuevos = [o for o in bpy.data.objects if o not in antes]
        fuente = next(o for o in nuevos if o.type == 'MESH')
        mesh = fuente.data
        self.vertices = [Vector(((v.co.y + 2.262)*2.15-3.15,
                                 -v.co.x*2.15, (v.co.z+.10)*2.15+.15-1.075104))
                         for v in mesh.vertices]
        # La punta del escaneo está a ~0.189 unidades del plano labial. Llevar
        # la región nasal a ese plano, con transición amplia hacia mejillas
        # y puente; las UV viajan con la superficie, sin mover la boca.
        punta=min((p for p in self.vertices if 1.2<p.z<3. and abs(p.y)<.7),key=lambda p:p.x)
        lateral_punta=punta.y
        def suave(t):
            t=max(0.,min(1.,t));return t*t*(3-2*t)
        for p in self.vertices:
            peso=suave((p.z-.75)/.55)*(1-suave((p.z-2.8)/1.5))*math.exp(-(p.y/1.45)**4)
            p.y-=lateral_punta*peso
        print('ALINEACION_NASAL',lateral_punta)
        # La boca funcional es algo más ancha y curva que la del escaneo.
        # Retraer suavemente la mejilla junto a la comisura evita que la piel
        # se coloque delante del borde al sonreír. El labio no cambia.
        for p in self.vertices:
            if p.x < -1.7:
                p.x += .50*(1-math.exp(-(p.y/.6)**2))*math.exp(-((p.z-.15)/.9)**2)*math.exp(-(p.y/2.2)**4)
        # 25 sep: tercio inferior más corto, mentón firme y mandíbula marcada
        # (rostro_didactico.py). No toca nada por encima de z = -0,9.
        from rostro_didactico import desplazar
        for p in self.vertices:
            dx, dy, dz = desplazar(p.x, p.y, p.z)
            p.x += dx; p.y += dy; p.z += dz
        self.superficie = bmesh.new()
        self.superficie.from_mesh(mesh)
        for v in self.superficie.verts: v.co = self.vertices[v.index]
        capa = self.superficie.loops.layers.uv.active
        for face in self.superficie.faces:
            for loop in face.loops: loop[capa].uv.y = 1-loop[capa].uv.y
        # glTF duplica vértices en costuras UV y normales. Antes de encontrar
        # el borde anatómico deben volver a ser una superficie conectada.
        bmesh.ops.remove_doubles(self.superficie, verts=list(self.superficie.verts), dist=1e-5)
        # El GLB también contiene geometría dentro de la boca cerrada.
        import ast
        source=Path(__file__).with_name('cara.py')
        tree=ast.parse(source.read_text(encoding='utf8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='quitar_interior_bm')
        env={};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),env)
        env['quitar_interior_bm'](self.superficie)
        # La correspondencia también se calcula sobre la superficie limpia:
        # el escaneo trae fragmentos solapados con UV ajenas a la piel visible.
        muestreo=self.superficie.copy()
        bmesh.ops.triangulate(muestreo,faces=list(muestreo.faces))
        muestreo.verts.ensure_lookup_table();muestreo.verts.index_update()
        muestreo.normal_update()
        self.normales=[v.normal.copy() for v in muestreo.verts]
        capa=muestreo.loops.layers.uv.active
        self.vertices=[v.co.copy() for v in muestreo.verts]
        self.caras=[tuple(v.index for v in f.verts) for f in muestreo.faces]
        self.uvs=[tuple(Vector((l[capa].uv.x,1-l[capa].uv.y,0.)) for l in f.loops) for f in muestreo.faces]
        self.bvh=BVHTree.FromPolygons(self.vertices,self.caras,all_triangles=True)
        muestreo.free()
        for ob in nuevos:
            bpy.data.objects.remove(ob, do_unlink=True)
        self.material = bpy.data.materials.new('piel_fotografica_LPS')
        self.material.use_nodes = True
        nodes, links = self.material.node_tree.nodes, self.material.node_tree.links
        bsdf = nodes['Principled BSDF']
        bsdf.inputs['Roughness'].default_value = .62
        color = nodes.new('ShaderNodeTexImage')
        color.image = bpy.data.images.load(str(root.parent / 'texturas' / 'piel_afeitada_v1.png'), check_existing=True)
        links.new(color.outputs['Color'], bsdf.inputs['Base Color'])
        # La normal tangencial antigua no se aplica a la retopología: necesita
        # un horneado nuevo. El visor calcula las normales del gesto real.

    def exterior(self, cercana):
        """Mitad del escaneo con ventana perioral y su cadena de sutura."""
        bm = self.superficie.copy()
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
            plane_co=(0,0,0), plane_no=(0,1,0), dist=1e-6,
            clear_outer=cercana, clear_inner=not cercana)
        def radio(p):
            h=.94 if p.z>=.15 else 1.08
            return (p.y/1.74)**2+((p.z-.15)/h)**2
        borrar=[f for f in bm.faces if f.calc_center_median().x < -1.8 and radio(f.calc_center_median())<1]
        bmesh.ops.delete(bm,geom=borrar,context='FACES')
        sueltos=[v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm,geom=sueltos,context='VERTS')
        bm.verts.ensure_lookup_table();bm.verts.index_update()
        capa=bm.loops.layers.uv.active
        bm.normal_update()
        vertices=[tuple(v.co) for v in bm.verts]
        sombras=[]
        for v in bm.verts:
            normal=v.normal.normalized()
            t=normal.cross(Vector((0,0,1)))
            if t.length<.01:t=normal.cross(Vector((0,1,0)))
            t.normalize();b=normal.cross(t)
            hits=0
            for j in range(10):
                phi=j*2.39996323; r=math.sqrt((j+.5)/10)*.85
                direction=normal*math.sqrt(1-r*r)+r*(math.cos(phi)*t+math.sin(phi)*b)
                hit=self.bvh.ray_cast(v.co+normal*.012,direction,.55)[0]
                hits+=hit is not None
            nasal=math.exp(-(v.co.y/.7)**4)*max(0.,min(1.,(v.co.z-.65)/.4))*max(0.,min(1.,(2.4-v.co.z)/.4))
            sombras.append(1-nasal*hits/10)
        uvs=[(0.,0.) for _ in vertices]
        caras=[];uv_caras=[]
        for face in bm.faces:
            caras.append(tuple(v.index for v in face.verts))
            uv_caras.append([tuple(loop[capa].uv) for loop in face.loops])
            for loop in face.loops:uvs[loop.vert.index]=tuple(loop[capa].uv)
        borde=set();adj={}
        for edge in bm.edges:
            a,b=edge.verts
            if (edge.is_boundary and not (abs(a.co.y)<1e-5 and abs(b.co.y)<1e-5)
                and max(a.co.x,b.co.x)<-1.5 and max(radio(a.co),radio(b.co))<2.):
                borde.update([a.index,b.index])
                adj.setdefault(a.index,[]).append(b.index)
                adj.setdefault(b.index,[]).append(a.index)
        # Cadena medial inferior -> comisura -> medial superior.
        cadenas=[];vistos=set()
        for inicio in [i for i in adj if len(adj[i])==1]:
            if inicio in vistos:continue
            cadena=[];actual=inicio
            while actual not in vistos:
                cadena.append(actual);vistos.add(actual)
                siguientes=[i for i in adj[actual] if i not in vistos]
                if not siguientes:break
                actual=siguientes[0]
            cadenas.append(cadena)
        assert len(cadenas)==1, 'La sutura debe ser una cadena conectada'
        orden=cadenas[0]
        if vertices[orden[0]][2]>vertices[orden[-1]][2]:orden.reverse()
        assert all(b in adj[a] for a,b in zip(orden,orden[1:])), 'Sutura discontinua'
        assert len(orden)>8, 'Ventana perioral no encontrada'
        assert abs(vertices[orden[0]][1])<1e-4 and abs(vertices[orden[-1]][1])<1e-4, 'Sutura abierta'
        bm.free()
        return vertices,caras,uvs,orden,uv_caras,sombras

    def proyectar(self, p):
        punto = Vector(p)
        # Muestreo frontal del escaneo limpio, con interpolación baricéntrica.
        hit, _, index, _ = self.bvh.ray_cast(Vector((-20., punto.y, punto.z)), Vector((1.,0.,0.)))
        if hit is None:
            hit, _, index, _ = self.bvh.find_nearest(punto)
        a,b,c = (self.vertices[i] for i in self.caras[index])
        ua,ub,uc = self.uvs[index]
        uv = barycentric_transform(hit,a,b,c,ua,ub,uc)
        return hit, (uv.x, 1.-uv.y)

    def normal(self,p):
        hit,_,index,_=self.bvh.find_nearest(Vector(p))
        ids=self.caras[index]
        a,b,c=(self.vertices[i] for i in ids)
        na,nb,nc=(self.normales[i] for i in ids)
        return barycentric_transform(hit,a,b,c,na,nb,nc).normalized()
