"""Superficie perioral ilustrativa, de topología regular y con bermellón volumétrico."""
import ast
import math
from pathlib import Path
import bpy

SUAVIDAD_MANDIBULA=[0.,0.,0.,.05,.13,.26,.42]

def desplazamiento_mandibula(p, apertura=.2, suavidad=0.):
    """Campo de piel del visor (x, altura, lateral), antes de sumar morfos.

    La prueba medir_didactica usa aplicar() del visor para contrastarlo.
    """
    x, lat, y = p
    def suave(t):
        t=max(0.,min(1.,t));return t*t*(3-2*t)
    frente=suave((-1.6-x)/.8)*(1-suave((abs(lat)-.85)/.5))
    seco=suave((.15-y)/suavidad) if suavidad else (1. if y<.15-1e-6 else 0.)
    arriba=(suave((y-.15)/suavidad) if suavidad else (1. if y>.15+1e-6 else 0.))*(1-suave((y-.55)/.25))
    bajo=suave((.45-y)/1.35)
    bajo+=(seco-.03*arriba-bajo)*frente
    delante=suave((2.3-x)/.9)
    retraso=frente*seco*max(0.,min(1.,(y+1.2)/1.35))*delante
    k=.2+.8*suave((apertura-.2)/.3)
    ang=.21*apertura*(bajo*delante-retraso*(1-k))
    return (2.6+(x-2.6)*math.cos(ang)-(y-.9)*math.sin(ang)-x,
            .9+(x-2.6)*math.sin(ang)+(y-.9)*math.cos(ang)-y)

def construir():
    # Reutiliza los mismos campos de deformación verificados en cara.py.
    # Extraer solo funciones evita ejecutar el generador y sobrescribir la app.
    source=Path(__file__).with_name('cara.py')
    names={'labios_en_piel','peso_labio_inferior_lps','perfil_lps'}
    tree=ast.parse(source.read_text(encoding='utf8'))
    module=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
    env={'bpy':bpy,'math':math,'RANURA':.012,'LPS_S':2.15,'MAND_MAX':.21,'MANDIBULA_CIERRE':.2}
    exec(compile(module,str(source),'exec'),env)
    # x, semiancho, alto superior, alto inferior, proporción de bermellón.
    rings=[(-2.91,1.03,.013,.013,1.),(-3.13,1.03,.013,.013,1.),
           (-3.19,1.07,.08,.105,1.),(-3.22,1.10,.15,.205,.9),
           (-3.10,1.16,.23,.29,.22),(-3.01,1.30,.36,.47,0.),
           (-2.93,1.55,.66,.84,0.),(-2.70,1.98,1.55,1.60,0.),
           (-1.85,2.70,3.50,2.65,0.),(.2,3.2,5.30,2.7,0.),
           (2.6,2.85,5.2,2.65,0.),(4.6,1.8,3.7,2.2,0.),(5.4,.45,1.0,.8,0.)]
    from apariencia_escaneo import AparienciaEscaneo
    foto = AparienciaEscaneo()
    # Conserva la franja funcional; fuera se sutura la superficie escaneada.
    rings = rings[:7]
    skin,red=(.76,.59,.49),(.64,.32,.31)
    costuras={}
    for name, start in [('cabeza_cercana',-math.pi/2),('cabeza_lejana',math.pi/2)]:
        old=bpy.data.objects[name]
        props=dict(old.items())
        # El corte aprobado conserva su silueta. El exterior anatómico comparte
        # rig y poses, pero no aparece en la capa del corte sagital.
        neutral=bpy.data.materials.new(name+'_mate')
        neutral.use_nodes=True
        neutral.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=skin+(1.,)
        old.data.materials.clear();old.data.materials.append(neutral)
        name=name.replace('cabeza_','exterior_')
        vertices,faces,colors,uvs=[],[],[],[]
        n=64
        for ri,(x,w,hu,hl,redness) in enumerate(rings):
            for q in range(n+1):
                theta=start+math.pi*q/n
                lateral=w*math.cos(theta);s=math.sin(theta)
                yy=.15+(hu if s>=0 else hl)*s
                # Arco de Cupido discreto: evita dos picos dibujados como maquillaje.
                if 2<=ri<=5 and s>0:
                    yy+=.028*(math.exp(-((abs(lateral)-.32)/.24)**2)-.3*math.exp(-(lateral/.18)**2))
                xx=x+.46*lateral*lateral
                _, uv = foto.proyectar((xx,-lateral,yy))
                if ri<=5:
                    # Anclas del bermellón en la fotografía cerrada. Proyectar
                    # rayos en el pliegue saltaba entre labio, piel y fondo.
                    h=([.001,.003,.007,.012,.020,.033] if s>=0 else
                       [.001,.003,.008,.016,.024,.037])[ri]
                    uv=(.500+.052*lateral/1.10, 1-(.467-h*s))
                vertices.append((xx,-lateral,yy))
                uvs.append(uv)
                f=redness
                # Variación suave del bermellón: interior más oscuro y labio
                # superior ligeramente menos luminoso, sin una raya pintada.
                shade=(.90 if s>0 else 1.02) * (.86 if ri==0 else .95 if ri==1 else 1.)
                tone=tuple(v*shade for v in red)
                colors.append(tuple(a+(b-a)*f for a,b in zip(skin,tone))+(1.,))
        for ri in range(len(rings)-1):
            for q in range(n):
                a=ri*(n+1)+q; b=a+1
                faces.append((a,b,b+n+1,a+n+1))
        exterior,caras,tex,borde,uv_caras,sombras=foto.exterior(name=='exterior_cercana')
        off=len(vertices);vertices.extend(exterior);uvs.extend(tex)
        colors.extend([skin+(ao,) for ao in sombras])
        inicio_scan=len(faces)
        faces.extend(tuple(off+i for i in f) for f in caras)
        # Las dos cadenas pueden tener distinta densidad. Triángulos en orden
        # angular unen la ventana del escaneo con el último anillo perioral.
        angulos=[math.atan2((exterior[i][2]-.15)/(.94 if exterior[i][2]>=.15 else 1.08),abs(exterior[i][1])/1.74) for i in borde]
        if name=='exterior_lejana':
            borde.reverse();angulos=[-a for a in reversed(angulos)]
        i=j=0
        while i<n or j<len(borde)-1:
            siguiente=-math.pi/2+math.pi*(i+1)/n
            if i<n and (j==len(borde)-1 or siguiente<=angulos[j+1]):
                faces.append((6*(n+1)+i,6*(n+1)+i+1,off+borde[j]));i+=1
            else:
                faces.append((6*(n+1)+i,off+borde[j+1],off+borde[j]));j+=1
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update()
        # Relaja únicamente la unión exterior. Borde, bermellón y contactos
        # de los primeros cinco anillos mantienen la calibración aprobada.
        vecinos=[set() for _ in vertices]
        for edge in mesh.edges:
            a,b=edge.vertices;vecinos[a].add(b);vecinos[b].add(a)
        relajables=set(range(5*(n+1),7*(n+1))) | {off+j for j in borde}
        from mathutils import Vector
        for _ in range(6):
            cambios={}
            for j in relajables:
                p=mesh.vertices[j].co
                media=sum((mesh.vertices[k].co for k in vecinos[j]),Vector())/len(vecinos[j])
                nuevo=p.lerp(media,.28)
                if abs(p.y)<1e-5:nuevo.y=0
                cambios[j]=nuevo
            for j,p in cambios.items():mesh.vertices[j].co=p
        mesh.update()
        ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
        for j,p in enumerate(vertices):
            if abs(p[1])>1e-5:continue
            if j<off:
                etiqueta=('labio',j//65,'sup' if p[2]>.15 else 'inf')
            else:etiqueta=('scan',round(p[0],5),round(p[2],5))
            costuras.setdefault(etiqueta,[]).append((ob,j))
        ob.data.materials.append(foto.material)
        ob['apariencia_fotografica']=1
        uv_layer=mesh.uv_layers.new(name='UVMap')
        for loop in mesh.loops: uv_layer.data[loop.index].uv=uvs[loop.vertex_index]
        # Segundo canal UV como dato de rig, no imagen: ancho de transición
        # mandibular. El borde articulatorio queda exacto; la piel vecina
        # no cambia de peso bruscamente a ambos lados de la línea de la boca.
        rig=mesh.uv_layers.new(name='RigMandibula')
        for loop in mesh.loops:
            ri=loop.vertex_index//65
            rig.data[loop.index].uv=(SUAVIDAD_MANDIBULA[ri] if ri<7 else .45,0.)
        for j,tex_cara in enumerate(uv_caras):
            for li,uv in zip(mesh.polygons[inicio_scan+j].loop_indices,tex_cara):
                uv_layer.data[li].uv=uv
        for k,v in props.items():
            if k not in ('targetNames',): ob[k]=v
        ob['labios_en_piel']=2
        ob.vertex_groups.new(name='mucosa').add(list(range(n+1)),1.,'REPLACE')
        color=mesh.vertex_colors.new(name='bermellon')
        for loop in mesh.loops: color.data[loop.index].color=colors[loop.vertex_index]
        for p in mesh.polygons:p.use_smooth=True
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
        env['labios_en_piel'](ob,env['perfil_lps']())
        keys=mesh.shape_keys.key_blocks
        seal=ob.shape_key_add(name='sello_didactico',from_mix=False)
        neutral_open=ob.shape_key_add(name='abrir_neutro',from_mix=False)
        dental=ob.shape_key_add(name='contorno_dental',from_mix=False)
        for i,p in enumerate(keys[0].data):
            ri=i//(n+1)
            w=max(0.,1-ri/4.) if ri>=2 else 1.
            displacement=max(-.013,min(.013,p.co.z-.15))*w
            seal.data[i].co.z-=displacement
            # La presión comprime tejido, no hace cruzar los bordes ya sellados.
            keys['compresion_labios'].data[i].co.z+=.6*displacement
            # Los dos anillos de borde coinciden al cerrar, en profundidad y
            # altura. El campo heredado suponía otra curva de contacto.
            correccion=[1.,1.,.60,.20,0.][min(ri,4)]
            if correccion:
                dx,dy=desplazamiento_mandibula(p.co,suavidad=SUAVIDAD_MANDIBULA[min(ri,6)])
                cierre=keys['cierre_labios'].data[i]
                cierre.co.x+=(p.co.x-dx-cierre.co.x)*correccion
                cierre.co.z+=(p.co.z-dy-cierre.co.z)*correccion
            if ri<=1:
                keys['compresion_labios'].data[i].co=p.co
        # Morfos propios de la topología regular. Los campos del escaneo
        # levantaban /i/ como una mueca rectangular y /f v/ como un bloque.
        for i,p in enumerate(keys[0].data):
            x,lat,y=p.co
            ri=i//(n+1)
            if ri>=7: continue
            q=i%(n+1);theta=start+math.pi*q/n
            s=math.sin(theta);t=abs(math.cos(theta))
            # Neutros articulados: abertura libre, sin heredar el sello de reposo.
            band=[1.,1.,1.,.95,.70,.32,.08][ri]
            if s>0: neutral_open.data[i].co.z += .49*s*band
            # /theta eth/: mandíbula deja espacio a la punta; el labio
            # inferior no tiene que descender tanto como el arco dental.
            dental.data[i].co.z += (.40 if s<0 else -.04)*abs(s)*band
            # Redondeo propio: un orificio oval y proyección contenida. El campo
            # del escaneo comprimía el ancho, pero dejaba una ranura horizontal.
            rounded=keys['fruncir'].data[i]
            rounded.co=p.co
            dx,dy=desplazamiento_mandibula(p.co,.12,SUAVIDAD_MANDIBULA[ri])
            rounded.co.x -= .46*band*(.75+.25*abs(s)) + dx*band
            rounded.co.y *= 1-.66*band
            # La abertura queda entre los bordes incisales, no delante de
            # toda la arcada inferior (que parecía una dentadura expuesta).
            rounded.co.z += (.37+.145*s)*band - dy*band
            if s<0 and 2<=ri<=4:
                rounded.co.z += .06*abs(s)**4*[.4,1.,.7][ri-2]
            # /i/: comisuras arriba y afuera, labios finos y abertura corta.
            # Las cifras son objetivos de diseño, no medidas clínicas.
            taper=[1.,1.,1.,.97,.82,.40,.1][ri]
            spread=1+.24*taper
            lat_i=lat*spread
            corner=.38*t*t*taper
            rim_open=(.50 if s>=0 else -.17)*s
            thin=(y-.15)*(1.15 if ri<=1 else (.96 if s>=0 else .92) if ri<=4 else 1.)
            target_y=.15+thin+rim_open*taper+corner
            dx,dy=desplazamiento_mandibula(p.co,.12,SUAVIDAD_MANDIBULA[ri])
            stretch=keys['estirar'].data[i]
            stretch.co.x=x+.12*taper+.10*t*taper-dx*taper
            stretch.co.y=lat_i
            stretch.co.z=target_y-dy*taper
            # /f v/: rodar solo la mucosa y el borde. La base del bermellón
            # queda estable. El punto de contacto está en la cara interna.
            k=keys['labio_atras'].data[i]
            k.co=p.co
            arch=max(0.,1-(abs(lat)/1.10)**4)
            dx,dy=desplazamiento_mandibula(p.co,.14,SUAVIDAD_MANDIBULA[ri])
            influence=.9419120638128117  # poseNumerica(/f v/) actual; medidor lo verifica
            if s>0:
                lift=[.52,.52,.50,.47,.32,.145,.035][ri]*arch*(s**.5)
                k.co.z+=lift/influence
            elif s<0 and ri<=4:
                # Por dentro el labio llega al filo dental; por fuera conserva
                # una curva descendente: los incisivos no desaparecen detrás.
                target_x=[-2.60+.80*lat*lat,-2.83+.48*lat*lat,-3.08+.46*lat*lat,x,x][ri]
                target_y=[.448,.345,.20,y+.055,y+.020][ri]
                roll=arch*min(1.,(-s)/.35)
                k.co.x+=(target_x-x-dx)*roll/influence
                k.co.z+=(target_y-y-dy)*roll/influence
        # El escaneo está alineado a otra altura que el rig heredado. Los
        # campos viejos de fruncir alcanzaban la nariz. Extender SOLO la
        # deformación de la unión labial y extinguirla en la piel circundante.
        borde_ids=[6*(n+1)+q for q in range(n+1)]
        for i in range(off,len(mesh.vertices)):
            p=keys[0].data[i].co
            cercanos=sorted(borde_ids,key=lambda j:(keys[0].data[j].co.y-p.y)**2+(keys[0].data[j].co.z-p.z)**2)[:2]
            distancias=[math.hypot(keys[0].data[j].co.y-p.y,keys[0].data[j].co.z-p.z) for j in cercanos]
            d=min(distancias)
            peso=max(0.,1-d/.7);peso=peso*peso*(3-2*peso)
            if p.x>-1.5 or p.z>1.05:peso=0.
            mezcla=distancias[0]/max(1e-8,sum(distancias))
            for key in list(keys)[1:]:
                a=key.data[cercanos[0]].co-keys[0].data[cercanos[0]].co
                b=key.data[cercanos[1]].co-keys[0].data[cercanos[1]].co
                key.data[i].co=p+peso*a.lerp(b,mezcla)
        # Regulariza la curvatura de CADA gesto, no sólo la malla en reposo.
        # La unión irregular del escaneo y el loft tenía cambios de pendiente
        # visibles con iluminación fotográfica. Los bordes de contacto (0..2)
        # quedan fijados; la relajación se extingue hacia el rostro.
        pesos={j:(.10 if j//65==3 else .30 if j//65==4 else .42)
               for j in range(3*65,7*65)}
        frontera={off+j for j in borde}
        for j in frontera:pesos[j]=.35
        for _ in range(2):
            nuevos=set().union(*(vecinos[j] for j in frontera))-{j for j in pesos}
            nuevos={j for j in nuevos if j>=off}
            for j in nuevos:pesos[j]=.16 if _==0 else .06
            frontera=nuevos
        for key in keys:
            for _ in range(12):
                cambios={}
                for j,peso in pesos.items():
                    p=key.data[j].co
                    media=sum((key.data[k].co for k in vecinos[j]),Vector())/len(vecinos[j])
                    nuevo=p.lerp(media,peso)
                    if abs(keys[0].data[j].co.y)<1e-5:nuevo.y=0
                    cambios[j]=nuevo
                for j,p in cambios.items():key.data[j].co=p
        # Volumen labial diferenciado: dos lóbulos superiores, surco de Cupido
        # y almohadilla central inferior. Un relleno uniforme hasta la piel
        # producía un aro inflado, también en /i/. Los anillos funcionales
        # 0 y 1 mantienen sus posiciones; sólo se esculpe el tejido exterior.
        for key in keys:
            for ri in range(2,6):
                for q in range(n+1):
                    i=ri*(n+1)+q;theta=start+math.pi*q/n
                    s=math.sin(theta)
                    t=abs(math.cos(theta))
                    taper=abs(s)**1.25
                    lobulos=(.67+.45*math.exp(-((t-.31)/.19)**2)
                             -.16*math.exp(-(t/.11)**2))
                    cuerpo=lobulos if s>0 else 1.-.26*t*t
                    plenitud=[.018,.074,.036,.004][ri-2]
                    altura=plenitud*(1. if s>0 else -.54)*cuerpo*taper
                    if key.name=='estirar':altura*=.90 if s>0 else .82
                    key.data[i].co.z+=altura
                    proyeccion=[.012,.052,.012,0.][ri-2]
                    key.data[i].co.x-=proyeccion*cuerpo*taper
        for j,v in enumerate(mesh.vertices):v.co=keys[0].data[j].co
        mesh.update()
        normals=[]
        for v in mesh.vertices:
            normal=v.normal.copy()
            if v.co.z>1.05:normal=foto.normal(v.co)
            elif abs(v.co.y)<1e-6: normal.y=0;normal.normalize()
            normals.append(tuple(normal))
        mesh.use_auto_smooth=True
        mesh.normals_split_custom_set_from_vertices(normals)
    # Relajar mitades asimétricas por separado puede separar el plano medial.
    # Restituye una misma coordenada y delta en cada par, en TODOS los gestos.
    for pares in costuras.values():
        if len(pares)<2:continue
        nombres=pares[0][0].data.shape_keys.key_blocks.keys()
        for nombre in nombres:
            media=sum((ob.data.shape_keys.key_blocks[nombre].data[j].co for ob,j in pares),Vector())/len(pares)
            media.y=0.
            for ob,j in pares:ob.data.shape_keys.key_blocks[nombre].data[j].co=media
        for ob,j in pares:ob.data.vertices[j].co=ob.data.shape_keys.key_blocks[0].data[j].co
    for nombre in ['exterior_cercana','exterior_lejana']:bpy.data.objects[nombre].data.update()

    # Resolver la piel móvil sobre las DOS mitades unidas. Resolverlas por
    # separado imponía una frontera artificial justo debajo del mentón.
    grupos={}; refs={}
    for nombre in ['exterior_cercana','exterior_lejana']:
        ob=bpy.data.objects[nombre];base=ob.data.shape_keys.key_blocks[0]
        for j,v in enumerate(base.data):
            k=tuple(round(c,5) for c in v.co)
            grupos.setdefault(k,[]).append((ob,j));refs[(nombre,j)]=k
    puntos={k:sum((ob.data.shape_keys.key_blocks[0].data[j].co for ob,j in pares),Vector())/len(pares) for k,pares in grupos.items()}
    adj={k:set() for k in grupos}
    for nombre in ['exterior_cercana','exterior_lejana']:
        for e in bpy.data.objects[nombre].data.edges:
            a,b=(refs[(nombre,j)] for j in e.vertices)
            if a!=b:adj[a].add(b);adj[b].add(a)
    libres={}
    for k,p in puntos.items():
        if any(j<4*65 for _,j in grupos[k]):continue
        if p.x>-1.6 or p.z>1.05 or math.hypot(p.y/2.1,(p.z-.15)/1.5)>1:continue
        libres[k]=[(v,1/max(.025,(puntos[v]-p).length)) for v in adj[k]]
    for nombre in ['fruncir','estirar','abrir_neutro']:
        delta={k:sum((ob.data.shape_keys.key_blocks[nombre].data[j].co-puntos[k] for ob,j in pares),Vector())/len(pares) for k,pares in grupos.items()}
        for k in delta:
            if abs(puntos[k].y)<1e-5:delta[k].y=0.
        for _ in range(110):
            cambios={}
            for k,ws in libres.items():
                media=sum((delta[v]*w for v,w in ws),Vector())/sum(w for _,w in ws)
                cambios[k]=delta[k].lerp(media,.55)
                if abs(puntos[k].y)<1e-5:cambios[k].y=0.
            delta.update(cambios)
        for k in libres:
            for ob,j in grupos[k]:
                ob.data.shape_keys.key_blocks[nombre].data[j].co=puntos[k]+delta[k]
    print('CAMPO_FACIAL_CONTINUO',len(libres))
