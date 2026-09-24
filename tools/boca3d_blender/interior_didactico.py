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


def seccion_labial(nombre, puntos, profundidad=.025, lado=None):
    """Losa del corte labial y franjas de tejido (piel, bermellón, mucosa).

    `puntos`: (x, z, índice exterior o None, rig, color del relleno, franja).
    Las franjas se dibujan un poco hacia la cámara (y<0) para no competir
    con la losa; sus vértices copian rig y deltas de su punto del contorno.
    Devuelve el objeto y, por vértice, el índice de `puntos` del que copia.
    """
    n=len(puntos)
    contorno=[(q[0],q[1]) for q in puntos]
    vertices=[(x,lat,y) for lat in (0.,profundidad) for x,y in contorno]
    origen=[j for _ in range(2) for j in range(n)]
    colores=[q[4] for _ in range(2) for q in puntos]
    poly=[Vector((x,y,0)) for x,y in contorno]
    tris=tessellate_polygon([poly])
    faces=[tuple(t) for t in tris]+[tuple(n+i for i in reversed(t)) for t in tris]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    # Orientación del polígono: la normal hacia fuera en el plano x-z.
    area=sum(contorno[i][0]*contorno[(i+1)%n][1]-contorno[(i+1)%n][0]*contorno[i][1] for i in range(n))
    signo=1. if area>0 else -1.
    franja=[j for j,q in enumerate(puntos) if q[5]]
    indice={}
    for j in franja:
        a,b=contorno[(j-1)%n],contorno[(j+1)%n]
        tx,tz=b[0]-a[0],b[1]-a[1];l=math.hypot(tx,tz) or 1.
        nx,nz=signo*tz/l,-signo*tx/l      # normal exterior
        ancho=puntos[j][5]
        x,z=contorno[j]
        indice[j]=(len(vertices),len(vertices)+1)
        zi=z-nz*ancho
        # El visor decide qué labio sigue a la mandíbula por la altura (0.15):
        # la franja interior no debe cruzar la línea de la boca.
        if lado=='sup':zi=max(zi,.152)
        elif lado=='inf':zi=min(zi,.148)
        vertices+= [(x,-.004,z),(x-nx*ancho,-.004,zi)]
        origen+= [j,j]
        colores+= [FRANJA[puntos[j][6]]]*2
    for j in franja:
        k=(j+1)%n
        if k in indice:
            (a0,a1),(b0,b1)=indice[j],indice[k]
            faces.append((a0,b0,b1,a1))
    mesh=bpy.data.meshes.new(nombre);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(nombre,mesh);bpy.context.collection.objects.link(ob)
    mat=bpy.data.materials.new(nombre+'_tejido');mat.diffuse_color=(.73,.43,.41,1)
    mesh.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=False
    region=mesh.vertex_colors.new(name='region_labial')
    for loop in mesh.loops:region.data[loop.index].color=(*colores[loop.vertex_index],1.)
    return ob,origen


# Colores de ilustración (sRGB de Blender), no regiones histológicas medidas.
FRANJA={'piel':(.40,.24,.18),'bermellon':(.62,.20,.24),'mucosa':(.80,.42,.46)}


def lamina(nombre, contorno, color, borde=None, ancho=0., y=-.008):
    """Pieza plana del corte (una cara), con franja de borde opcional."""
    n=len(contorno)
    poly=[Vector((x,z,0)) for x,z in contorno]
    tris=tessellate_polygon([poly])
    vertices=[(x,y,z) for x,z in contorno];faces=[tuple(t) for t in tris];colores=[color]*n
    if borde and ancho:
        area=sum(contorno[i][0]*contorno[(i+1)%n][1]-contorno[(i+1)%n][0]*contorno[i][1] for i in range(n))
        signo=1. if area>0 else -1.
        base=len(vertices)
        for j in range(n):
            a,b=contorno[(j-1)%n],contorno[(j+1)%n]
            tx,tz=b[0]-a[0],b[1]-a[1];l=math.hypot(tx,tz) or 1.
            nx,nz=signo*tz/l,-signo*tx/l
            x,z=contorno[j]
            vertices+=[(x,y-.001,z),(x-nx*ancho,y-.001,z-nz*ancho)];colores+=[borde,borde]
        for j in range(n):
            k=(j+1)%n
            faces.append((base+2*j,base+2*k,base+2*k+1,base+2*j+1))
    mesh=bpy.data.meshes.new(nombre);mesh.from_pydata(vertices,[],faces);mesh.update()
    ob=bpy.data.objects.new(nombre,mesh);bpy.context.collection.objects.link(ob)
    mat=bpy.data.materials.new(nombre+'_tejido');mat.diffuse_color=(*color,1);mesh.materials.append(mat)
    region=mesh.vertex_colors.new(name='region_labial')
    for loop in mesh.loops:region.data[loop.index].color=(*colores[loop.vertex_index],1.)
    return ob


def redondeado(x0,z0,x1,z1,r=.06,pasos=4):
    """Rectángulo de esquinas redondas (x0<x1, z0<z1)."""
    out=[]
    for cx,cz,a0 in ((x1-r,z0+r,-math.pi/2),(x1-r,z1-r,0.),(x0+r,z1-r,math.pi/2),(x0+r,z0+r,math.pi)):
        for k in range(pasos+1):
            a=a0+k*(math.pi/2)/pasos
            out.append((cx+r*math.cos(a),cz+r*math.sin(a)))
    return out


def cerrada(puntos, pasos=6):
    """Curva Catmull-Rom cerrada por los puntos dados."""
    n=len(puntos);out=[]
    for i in range(n):
        a,b,c,d=puntos[(i-1)%n],puntos[i],puntos[(i+1)%n],puntos[(i+2)%n]
        for k in range(pasos):
            t=k/pasos
            out.append(tuple(.5*(2*q1+(-q0+q2)*t+(2*q0-5*q1+4*q2-q3)*t*t+(-q0+3*q1-3*q2+q3)*t*t*t)
                             for q0,q1,q2,q3 in zip(a,b,c,d)))
    return out


def anatomia_de_apoyo(medial,contorno,pared_exterior):
    HUESO=(.93,.88,.78);CORTICAL=(.66,.58,.46);DISCO=(.70,.77,.80)
    CEREBRO=(.84,.70,.68);CEREBELO=(.78,.62,.60);NERVIO=(.90,.84,.74);MUSCULO=(.60,.27,.27)
    # Interior del cráneo: piel (0.12) y hueso (0.33) por dentro del contorno.
    pts=[(medial[i].x,medial[i].z) for i in contorno]
    arco=[j for j,(x,z) in enumerate(pts) if (x<1 and z>3.45) or (x>=1 and z>3.0 and not (x<3 and z<5))]
    tramo_=pts[arco[0]:arco[-1]+1]
    centro=(1.3,4.2)
    def adentro(lista,d):
        out=[]
        for i,(x,z) in enumerate(lista):
            a,b=lista[max(0,i-1)],lista[min(len(lista)-1,i+1)]
            tx,tz=b[0]-a[0],b[1]-a[1];l=math.hypot(tx,tz) or 1.
            nx,nz=tz/l,-tx/l
            if nx*(centro[0]-x)+nz*(centro[1]-z)<0:nx,nz=-nx,-nz
            out.append((x+nx*d,z+nz*d))
        return out
    interior=adentro(tramo_,.45)[::3]
    # Cerebro: bóveda, tentorio sobre el cerebelo y base media y anterior.
    delante=[p for p in interior if not (p[0]>3.0 and p[1]<3.9)]
    cerebro=delante+[(3.9,3.95),(3.1,3.62),(2.45,3.62),(1.95,3.35),(1.2,3.0),(.3,3.05),(-.8,3.38),(-1.9,3.6)]
    lamina('anatomia_cerebro',cerebro,CEREBRO,(.62,.46,.45),.035)
    lamina('anatomia_cerebelo',cerrada([(3.25,3.35),(3.95,3.78),(4.75,3.72),(5.3,3.3),(5.38,2.7),(5.0,2.18),(4.35,2.0),(3.72,2.25),(3.35,2.75)]),
           CEREBELO,(.55,.40,.39),.03)
    # Tronco del encéfalo y médula: del cerebro al agujero occipital y al cuello.
    def pared_x(z):
        pe=[q for q in pared_exterior]
        for (x0,z0),(x1,z1) in zip(pe,pe[1:]):
            if min(z0,z1)<=z<=max(z0,z1) and z0!=z1:return x0+(z-z0)/(z1-z0)*(x1-x0)
        return pe[-1][0]
    def piel_x(z):
        atras=[(x,zz) for x,zz in pts if x>3.8]
        return min(atras,key=lambda q:abs(q[1]-z))[0]
    cuerpo=lambda z:pared_x(z)+.10
    tronco_d=[(1.85,3.4),(2.45,2.65),(3.2,1.95),(cuerpo(1.5)+.66,1.45)]
    tronco_t=[(cuerpo(1.5)+.92,1.6),(3.85,2.2),(3.05,3.0),(2.5,3.62)]
    medula_d=[(cuerpo(z)+.66,z) for z in (1.2,.4,-.6,-1.6,-2.6,-3.2)]
    medula_t=[(cuerpo(z)+.88,z) for z in (-3.2,-2.6,-1.6,-.6,.4,1.2)]
    lamina('anatomia_medula',tronco_d+medula_d+medula_t+tronco_t,NERVIO,(.70,.62,.52),.025,y=-.009)
    # Vértebras cervicales: C1 (arco anterior), C2 con apófisis odontoides,
    # C3–C7 y el comienzo de T1, con discos intervertebrales.
    lamina('anatomia_c1',cerrada([(pared_x(1.35)+.06,1.3),(pared_x(1.35)+.12,1.46),(pared_x(1.35)+.26,1.42),(pared_x(1.35)+.25,1.24)],4),
           HUESO,CORTICAL,.025)
    x2=cuerpo(.6)
    lamina('anatomia_c2',[(x2+.30,1.62),(x2+.42,1.55),(x2+.44,1.12),(x2+.6,1.05),(x2+.6,.3),(x2+.52,.24),
                          (x2+.06,.24),(x2,.3),(x2,1.0),(x2+.18,1.1),(x2+.18,1.5)],HUESO,CORTICAL,.025)
    alto,disco=.5,.12
    for k,techo in enumerate([.12,-.5,-1.12,-1.74,-2.36,-2.98]):
        base=max(techo-alto,-3.2);xc=cuerpo(techo-alto/2)
        lamina('anatomia_vertebra_%d'%(k+3),redondeado(xc,base,xc+.6,techo),HUESO,CORTICAL,.025)
        if techo+disco<=1.1:lamina('anatomia_disco_%d'%(k+3),redondeado(xc+.03,techo+.01,xc+.57,techo+disco-.01,.03,2),DISCO)
        # Apófisis espinosa detrás del conducto, sin salir de la nuca.
        z=techo-alto/2;xa=cuerpo(z)+.95;xb=min(xa+.45,piel_x(z)-.14)
        if xb>xa+.08:lamina('anatomia_espinosa_%d'%(k+3),cerrada([(xa,z+.16),(xb,z+.02),(xb,z-.12),(xa,z-.14)],4),HUESO,CORTICAL,.02)
    # Músculos de la nuca, entre las apófisis y la piel.
    nuca=[p for p in adentro([q for q in pts if q[0]>3.8 and -3.2<q[1]<2.1],.14)][::2]
    nuca_int=[(cuerpo(z)+1.0,z) for z in (-3.2,-2.0,-.8,.4,1.4)]+[(4.75,2.0)]
    if len(nuca)>3:lamina('anatomia_nuca',nuca+nuca_int,MUSCULO,(.46,.18,.19),.02,y=-.007)
    # Hioides.
    lamina('anatomia_hioides',cerrada([(.7,-2.26),(1.35,-2.06),(1.47,-2.18),(.82,-2.4)],4),HUESO,CORTICAL,.02)


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
    pared_exterior=list(exterior)
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
    # Sección de tejido blando del perfil (24 sep). Antes eran dos cuñas de
    # 7 puntos que flotaban delante de los dientes: sin piel bajo la nariz ni
    # barbilla. Ahora el contorno exterior es la cadena medial REAL de la piel
    # (subnasal → bermellón → borde; borde → mentón → submentón), con sus
    # deltas en todos los gestos; el interior apoya en el hueso ilustrativo.
    fuente=bpy.data.objects['exterior_cercana']; keys=fuente.data.shape_keys.key_blocks
    from perioral_didactico import SUAVIDAD_MANDIBULA
    medial={i:keys[0].data[i].co.copy() for i in range(len(keys[0].data))
            if abs(keys[0].data[i].co.y)<1e-4}
    def cadena(z_desde,z_hasta,x_max):
        ids=[i for i,c in medial.items() if z_hasta<=c.z<=z_desde and -1.5>c.x and c.x<=x_max and i>=7*65]
        return sorted(ids,key=lambda i:-medial[i].z)
    # Contorno medial de la cabeza de frente, ordenado: del subnasal sube por
    # la nariz, cráneo y nuca, baja al cuello y vuelve por delante al mentón.
    vecinos={i:set() for i in medial if i>=7*65}
    for e in fuente.data.edges:
        a,b=e.vertices
        if a in vecinos and b in vecinos:vecinos[a].add(b);vecinos[b].add(a)
    subnasal=min(vecinos,key=lambda i:(medial[i].x+3.298)**2+(medial[i].z-1.225)**2)
    contorno_cabeza=[subnasal]
    siguiente=max(vecinos[subnasal],key=lambda i:medial[i].z)
    while siguiente is not None:
        contorno_cabeza.append(siguiente)
        libres=[i for i in vecinos[siguiente] if i not in contorno_cabeza]
        siguiente=libres[0] if libres else None
    def tramo(condicion_inicio,condicion_fin,desde=0):
        a=next(k for k in range(desde,len(contorno_cabeza)) if condicion_inicio(medial[contorno_cabeza[k]]))
        b=next(k for k in range(a,len(contorno_cabeza)) if condicion_fin(medial[contorno_cabeza[k]]))
        return a,b
    def rig_de(i):
        return SUAVIDAD_MANDIBULA[i//65] if i<7*65 else .45
    # Colores de ilustración (lineales), no regiones histológicas medidas.
    GRASA=(.64,.42,.35); MUSCULO=(.55,.20,.22)
    anillos_sup=[6*65+64,5*65+64,4*65+64,3*65+64,2*65+64,65+64,64]
    anillos_inf=[0,65,130,195,260,325,390]
    for nombre in ('anatomia_labio_sup','anatomia_labio_inf'):
        sup=nombre.endswith('_sup')
        puntos=[]  # (x, z, índice exterior o None, rig, relleno, ancho de franja, tejido)
        def exterior(i,relleno,ancho,tej):puntos.append((medial[i].x,medial[i].z,i,rig_de(i),relleno,ancho,tej))
        tipo_anillo=[('mucosa',.035),('bermellon',.05),('bermellon',.06),('bermellon',.06),('piel',.045),('piel',.045),('piel',.045)]
        if sup:
            # Subnasal hasta el borde. La columela (x<-3.30) es de la nariz.
            for i in cadena(1.226,.95,-3.10):exterior(i,GRASA,.045,'piel')
            for k,i in enumerate(anillos_sup):
                tej,ancho=tipo_anillo[6-k];exterior(i,GRASA if k<3 else MUSCULO,ancho,tej)
            # Cara interna: mucosa hasta la inserción, luego sobre el maxilar.
            puntos+= [(-2.73,.46,None,-1.,MUSCULO,.035,'mucosa'),(-2.66,.82,None,-1.,MUSCULO,0,None),
                      (-2.945,.86,None,-1.,GRASA,0,None),(-2.975,1.04,None,-1.,GRASA,0,None),(-2.975,1.225,None,-1.,GRASA,0,None)]
        else:
            for k,i in enumerate(anillos_inf):
                tej,ancho=tipo_anillo[k];exterior(i,GRASA if k>=4 else MUSCULO,ancho,tej)
            for i in cadena(-.62,-2.30,-1.60):exterior(i,GRASA,.045,'piel')
            cuello=sorted((i for i in contorno_cabeza if medial[i].x<0.5 and -3.2<=medial[i].z<-2.30),key=lambda i:-medial[i].z)
            for i in cuello:
                c=medial[i];t=min(1.,max(0.,(-2.30-c.z)/.9));w=1-t*t*(3-2*t)
                puntos.append((c.x+.002,c.z,None,-3.-w,GRASA,.045,'piel'))
            k=contorno_cabeza.index(cuello[-1])
            c0=medial[cuello[-1]]
            c1=min((medial[contorno_cabeza[k-1]],medial[contorno_cabeza[(k+1)%len(contorno_cabeza)]]),key=lambda c:c.z)
            f=(-3.2-c0.z)/(c1.z-c0.z)
            puntos.append((c0.x+f*(c1.x-c0.x)+.002,-3.2,None,-3.,GRASA,.045,'piel'))
            # Tejido blando del cuello hasta la faringe y bajo el suelo de la boca.
            puntos+=[(2.5,-3.2,None,.45,GRASA,0,None),(2.55,-1.95,None,.45,GRASA,0,None),
                     (1.4,-1.9,None,.45,GRASA,0,None),(0.,-1.8,None,.45,GRASA,0,None)]
            # Bajo el mentón óseo y de vuelta por su frente hasta la inserción.
            hueso=[(-1.56,-1.80),(-1.90,-1.77),(-2.26,-1.70),(-2.52,-1.60),(-2.71,-1.48),
                   (-2.83,-1.32),(-2.91,-1.12),(-2.945,-.90),(-2.945,-.69)]
            puntos+=[(x,z,None,-2.,GRASA,0,None) for x,z in hueso]
            puntos+=[(-2.63,-.50,None,-2.,MUSCULO,0,None),(-2.72,-.12,None,-2.,MUSCULO,.035,'mucosa'),
                     (-2.80,.02,None,0.,MUSCULO,.035,'mucosa')]
        # Quitar duplicados exactos consecutivos del escaneo.
        limpio=[]
        for q in puntos:
            if limpio and math.hypot(q[0]-limpio[-1][0],q[1]-limpio[-1][1])<1e-4:continue
            limpio.append(q)
        puntos=limpio
        # Deltas de cada gesto por punto; los interiores no se mueven.
        nombres_gesto=[k.name for k in list(keys)[1:]]
        deltas=[{g:(keys[g].data[q[2]].co-keys[0].data[q[2]].co if q[2] is not None else Vector()) for g in nombres_gesto}
                for q in puntos]
        # El labio sólo tiene 7 anillos: el perfil salía en cuñas. Entre dos
        # anillos consecutivos se insertan 3 puntos Catmull-Rom, en reposo y en
        # cada gesto (se interpola la posición final, no sólo el reposo).
        def cr(a,b,c,d,t):
            return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
        n_p=len(puntos)
        interp={j for j,q in enumerate(puntos) if q[2] is not None and q[2]<7*65}
        if not sup:
            # Mucosa interior: sigue al 30 % del borde y del bermellón medio.
            r0=next(j for j,q in enumerate(puntos) if q[2]==0)
            r2=next(j for j,q in enumerate(puntos) if q[2]==130)
            deltas[-1]={g:.3*(deltas[r0][g]+deltas[r2][g]) for g in nombres_gesto}
            interp.add(n_p-1)
        nuevos=[];nuevos_d=[]
        for j,q in enumerate(puntos):
            nuevos.append(q);nuevos_d.append(deltas[j])
            k=(j+1)%n_p
            if j in interp and k in interp and (k==j+1 or not sup):
                h,m=(j-1)%n_p,(k+1)%n_p
                for paso in (1,2,3):
                    t=paso/4
                    x=cr(puntos[h][0],q[0],puntos[k][0],puntos[m][0],t)
                    z=cr(puntos[h][1],q[1],puntos[k][1],puntos[m][1],t)
                    # Sin cruzar la línea de la boca (0.15) en reposo: el visor
                    # haría girar con la mandíbula un punto del labio superior.
                    z=max(z,.152) if sup else min(z,.148)
                    d={}
                    for g in nombres_gesto:
                        fin=[Vector((pp[0],0,pp[1]))+dd[g] for pp,dd in ((puntos[h],deltas[h]),(q,deltas[j]),(puntos[k],deltas[k]),(puntos[m],deltas[m]))]
                        d[g]=cr(*fin,t)-Vector((x,0,z))
                        # /f v/: el labio recogido era una cuña recta. Se abomba
                        # hacia delante entre el bermellón medio y el borde
                        # externo, sólo en el corte (el exterior no cambia).
                        if g=='labio_atras' and not sup and {q[2],puntos[k][2]}<={65,130,195}:
                            a_,b_=fin[1],fin[2];tx,tz=b_.x-a_.x,b_.z-a_.z;l=math.hypot(tx,tz) or 1.
                            nx,nz=tz/l,-tx/l
                            if nx>0:nx,nz=-nx,-nz
                            d[g]+=Vector((nx,0,nz))*.07*math.sin(math.pi*t)
                    rig=q[3]+(puntos[k][3]-q[3])*t
                    nuevos.append((x,z,None,rig,q[4],q[5],q[6]));nuevos_d.append(d)
        puntos,deltas=nuevos,nuevos_d
        ob,origen=seccion_labial(nombre,puntos,lado='sup' if sup else 'inf')
        ob.data.uv_layers.new(name='UVMap')
        rig=ob.data.uv_layers.new(name='RigMandibula')
        for loop in ob.data.loops:rig.data[loop.index].uv=(puntos[origen[loop.vertex_index]][3],0.)
        ob.shape_key_add(name='Basis')
        for key in list(keys)[1:]:
            target=ob.shape_key_add(name=key.name)
            for v,j in enumerate(origen):target.data[v].co+=deltas[j][key.name]
        ob['borde_compartido']=1
    # La nariz: del subnasal a la raíz (y=3.2), con la cavidad nasal detrás.
    MARFIL=(.80,.76,.71)
    a,b=tramo(lambda c:True,lambda c:c.z>=3.2)
    nariz=[(medial[i].x,medial[i].z,None,-1.,GRASA,.045,'piel') for i in contorno_cabeza[a:b+1]]
    nariz+=[(-2.2,3.16,None,-1.,GRASA,0,None),(-2.2,2.4,None,-1.,GRASA,0,None),(-2.3,1.72,None,-1.,GRASA,0,None),
            (-2.77,1.60,None,-1.,GRASA,0,None),(-2.975,1.575,None,-1.,GRASA,0,None),(-2.975,1.225,None,-1.,GRASA,0,None)]
    seccion_labial('anatomia_nariz',nariz)
    # Cráneo y nuca: de la raíz nasal por la frente, la coronilla y la nuca
    # hasta y=-3.2; vuelve por fuera de la pared faríngea y del techo nasal.
    c,d=tramo(lambda c:c.z>=3.2,lambda c:c.x>2 and c.z<-3.2)
    craneo=[(medial[i].x,medial[i].z,None,-1.,MARFIL,.045,'piel') for i in contorno_cabeza[c:d]]
    c0,c1=medial[contorno_cabeza[d-1]],medial[contorno_cabeza[d]]
    f=(-3.2-c0.z)/(c1.z-c0.z)
    craneo.append((c0.x+f*(c1.x-c0.x),-3.2,None,-1.,MARFIL,0,None))
    craneo+=[(x,z,None,-1.,MARFIL,0,None) for x,z in reversed(pared_exterior) if z>-3.2]
    craneo.append((-2.2,3.16,None,-1.,MARFIL,0,None))
    seccion_labial('anatomia_craneo',craneo)
    anatomia_de_apoyo(medial,contorno_cabeza,pared_exterior)
    print('INTERIOR_DIDACTICO_OK')
