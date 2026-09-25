"""Coronas visuales contenidas en la envolvente del piloto didáctico.

Llamar construir() EN LUGAR del bucle dental de cara_didactica.py, después
de importar cara.glb. No mueve objetos, arcadas ni bordes de los incisivos
centrales y laterales. El color por vértice ``esmalte`` requiere material blanco en el
visor. No exporta archivos ni modifica la escena al importar el módulo.

Añade dos conjuntos gingivales ``papila_sup_dentalv2`` y
``papila_inf_dentalv2``. El visor debe habilitarlos en la capa exterior;
el inferior sigue el mismo grupo mandibular que los dientes inferiores.
Cada manguito ocupa únicamente la antigua envolvente de su propia corona.
Es anatomía visual simplificada, no un modelo odontológico individual.
"""
import math
import re


# La envolvente que ya se ha comprobado con los labios del piloto.
_NIVELES = ((-.25, .60), (-.23, .85), (-.17, 1.),
            (.08, 1.), (.20, .90), (.25, .74))
_MUESTRAS = (-.25, -.245, -.23, -.21, -.19, -.17, -.13, -.09,
             -.05, 0., .04, .08, .12, .16, .20, .225, .25)
_LADOS = 40  # dos muestras por arista original, sin extender su polígono


def _suave(t):
    t = max(0., min(1., t))
    return t*t*(3.-2.*t)


def _dimensiones(j):
    profundidad = .24 if j >= 4 else .30 if j == 3 else .36 if j else .42
    ancho = .255 if j == 5 else .245 if j == 4 else .29 if j == 3 else .35 if j else .42
    return profundidad, ancho


def _anillo_original(t, bisel, j, q):
    """Interpolar el polígono original de 20 lados, no su superelipse ideal."""
    profundidad, ancho = _dimensiones(j)
    borde = max(0., -t/.25)
    fino = 1.-(.52 if j >= 4 else .28 if j == 3 else 0.)*borde
    estrecho = 1.-.30*borde if j == 3 else 1.
    puntos = []
    for k in (q//2, q//2+1):
        a = math.tau*(k % 20)/20
        c, s = math.cos(a), math.sin(a)
        puntos.append((math.copysign(abs(c)**.55, c)*profundidad*.5*bisel*fino,
                       math.copysign(abs(s)**.55, s)*ancho*.5*bisel*estrecho))
    f = (q % 2)*.5
    return tuple(a+(b-a)*f for a, b in zip(*puntos))


def _envolvente(t, j, q):
    """Sección del volumen antiguo a la misma altura: interpola sus caras."""
    for (ta, ba), (tb, bb) in zip(_NIVELES, _NIVELES[1:]):
        if ta-1e-9 <= t <= tb+1e-9:
            f = (t-ta)/(tb-ta)
            a, b = _anillo_original(ta, ba, j, q), _anillo_original(tb, bb, j, q)
            return tuple(x+(y-x)*f for x, y in zip(a, b))
    raise ValueError('altura fuera de la corona')


def _color(t, j, q=None, indice=None):
    # Blender 2.93 guarda vertex_colors.data.color como color de visualización;
    # su exportador glTF YA convierte sRGB a lineal al escribir COLOR_0.
    # Entregar sRGB aquí evita una segunda conversión y esmalte oscuro/amarillo.
    borde, cuerpo, cuello = ((.89, .905, .90), (.96, .935, .875), (.845, .805, .715)) if j >= 3 else ((.95, .935, .89), (.925, .90, .835), (.87, .815, .715))
    f = _suave((t+.20)/.17)
    rgb = tuple(a+(b-a)*f for a, b in zip(borde, cuerpo))
    f = .68*_suave((t+.065)/.17) if j >= 3 else .72*_suave((t-.08)/.17)
    rgb = tuple(a+(b-a)*f for a, b in zip(rgb, cuello))
    # Caninos levemente más cálidos; sin manchas ni translucidez ficticia.
    if j == 3:
        rgb = (rgb[0], rgb[1]*.991, rgb[2]*.974)
    if q is not None and j >= 3:
        a = math.tau*q/_LADOS
        # Variación muy leve: no dibujar manchas ni simular translucidez física.
        delta = .0025*math.cos(3*a+.3*(indice or 0))*math.sin((t+.25)*17.)
        rgb = tuple(max(0., min(1., v+delta)) for v in rgb)
    return tuple(rgb)+(1.,)


def _margen(j, q, superior=True):
    """Margen cervical festoneado: cénit vestibular y papila interproximal.

    Las alturas son una adaptación a la arcada calibrada, no medidas humanas.
    Altura clínica central .322, lateral .272, canino .317 aproximadamente.
    """
    s = abs(math.sin(math.tau*q/_LADOS))
    cenit = .072 if j == 5 else .022 if j == 4 else .085
    return cenit-.064*s**2-(0.020 if not superior else 0.)


def _punto_base(t, j, q):
    """Superficie v2: referencia exacta de la banda de contacto incisal."""
    x, y = _envolvente(t, j, q)
    a = math.tau*q/_LADOS
    c, s = math.cos(a), math.sin(a)
    if j <= 2:
        # El ajuste de proporción se limita a los seis anteriores.
        libre = _suave((t+.25)/.05)
        cuello = _suave((t-.06)/.19)
        radial = 1.-.065*(2.*abs(c*s))**2*libre
        return x*radial*(1.-.055*cuello), y*radial*(1.-.095*cuello)
    libre = _suave((t+.25)/.055)
    cervical = _suave((t+.025)/.24)
    vientre = math.exp(-((t+.085)/.10)**2)
    esquina = (2.*abs(c*s))**2
    radial = 1.-(.16 if j >= 3 else .065)*esquina*libre
    x *= radial*(1.-(.15 if j >= 3 else .055)*cervical)
    y *= radial*(1.-(.22 if j >= 3 else .095)*cervical)
    if j >= 4:
        if x > 0:
            x *= 1.-.20*vientre*(1.-abs(s)**3)*libre
        else:
            # Convexidad vestibular amplia; no acanaladuras de tamaño visible.
            x *= 1.-.085*(1.-vientre)*libre
        if j == 4:
            # Conservar también los contactos /fv/ con laterales: su anillo
            # incisal anterior llevaba .93 de ancho y .97 de profundidad.
            # Diferenciar sólo el cuerpo, con transición nula en la arista.
            y *= .93-.05*libre
            x *= .97-.02*libre
    elif j == 3:
        punta = 1.-.50*(1.-_suave((t+.25)/.13))
        x *= punta
        y *= punta
    return x, y


def _punto_corona(t, j, q, indice=None):
    """Incisivos en pala y caninos convexos; banda t<=-.23 preservada.

    La pala se esculpe dentro del volumen calibrado, sin añadir espesor que
    invada los labios. Las tres primeras secciones
    incisales son idénticas a v2; las demás se funden gradualmente.
    """
    bx, by = _punto_base(t, j, q)
    if j <= 2 or t <= -.23:
        return bx, by
    ex, ey = _envolvente(t, j, q)
    a = math.tau*q/_LADOS
    c, s = math.cos(a), math.sin(a)
    mezcla = _suave((t+.23)/.08)
    cuello = _suave((t+.14)/.24)
    vientre = math.exp(-((t+.08)/.13)**2)
    if j >= 4:
        # Una sección elíptica hacía que incisivos y caninos fueran tubos.
        # Cara labial amplia con hombros redondeados: recortar el volumen
        # original mediante un plano ligeramente convexo, nunca ensancharlo.
        cervical = _suave((t+.055)/.155)
        ty = ey*(1.-(.25 if j == 5 else .22)*cervical)
        if ex < 0:
            radio = abs(_envolvente(t, j, _LADOS//2)[0])
            limite = -radio*(.70+.055*_suave((t+.12)/.20))
            limite *= 1.-.035*abs(s)**2
            # Máximo suavizado de ex y el plano; el redondeo se dirige
            # siempre hacia dentro y evita una arista dura en los hombros.
            bisel = .0035
            tx = min(0., .5*(ex+limite+math.sqrt((ex-limite)**2+bisel*bisel)))
        else:
            # Concavidad palatina real: bordes marginales y cíngulo cervical
            # más gruesos que el centro de la pala. Se aprecia en tres cuartos.
            tx = ex*(.31+.40*abs(s)**4+.23*cervical)
        if j == 4:
            # No estrechar el cuerpo por debajo de la banda incisal fijada:
            # se vería un borde abultado aunque los contactos fueran correctos.
            ty *= .85
            tx *= .92
    else:
        # Canino: cresta vestibular ancha, hombros hacia el cuello.
        tx = bx*(1.-.18*cuello-.08*abs(s)**2)
        ty = by*(1.-.16*cuello)
    distal = max(0., s*(1. if indice is None or indice < 6 else -1.))
    ty *= 1.-.035*distal**2*cuello
    # Microrelieve geométrico submilimétrico y determinista. Al ser una
    # contracción no amplía la envolvente; tampoco afecta la banda incisal.
    if ex < 0:
        relieve = .00022*(.5+.5*math.sin(118*t+1.7*math.sin(3*a)))
        relieve *= vientre*abs(c)**4
        tx *= max(.98, 1.-relieve/max(abs(tx), .001))
    return bx+(tx-bx)*mezcla, by+(ty-by)*mezcla


def _muestras(j):
    # Más detalle longitudinal donde cambia el domo, sin densificar molares.
    if j <= 2:
        return _MUESTRAS
    return tuple(sorted(set(_MUESTRAS+tuple((a+b)*.5 for a,b in
                 zip(_MUESTRAS, _MUESTRAS[1:]) if a >= -.23))))


def datos_corona(indice, superior):
    """Datos puros: vértices locales, caras y colores sRGB de Blender 2.93."""
    if not 0 <= indice <= 11:
        raise ValueError('índice dental fuera de 0..11')
    j = min(indice, 11-indice)
    vertices, caras, colores = [], [], []
    muestras = _muestras(j)
    for t in muestras:
        for q in range(_LADOS):
            s = abs(math.sin(math.tau*q/_LADOS))
            # Sólo caninos: hombros de la cúspide. Los 40 puntos de TODOS
            # los incisivos, incluidos laterales de contacto /fv/, conservan
            # exactamente la posición anterior.
            subida = .018+.042*s**2 if j == 3 else 0.
            altura = t+subida*(1.-_suave((t+.25)/.13))
            x, y = _punto_corona(altura, j, q, indice)
            z = altura if superior else -altura
            vertices.append((x, y, z))
            colores.append(_color(altura, j, q, indice))
    for r in range(len(muestras)-1):
        for q in range(_LADOS):
            a = r*_LADOS+q
            b = r*_LADOS+(q+1) % _LADOS
            caras.append((a, b, b+_LADOS, a+_LADOS))

    # Incisales planos con perímetro fino; en posteriores, pequeñas fosas
    # oclusales dentro de la corona, sin añadir cúspides fuera del límite.
    anterior = list(range(_LADOS))
    if j <= 2:
        interior = []
        for q in range(_LADOS):
            x, y, _ = vertices[q]
            surco = .020*math.exp(-(x/.055)**2)
            if j == 0:
                surco += .014*math.exp(-(y/.065)**2)
            t = -.25+surco
            interior.append(len(vertices))
            vertices.append((x*.52, y*.52, t if superior else -t))
            colores.append(_color(-.25, j))
        for q in range(_LADOS):
            k = (q+1) % _LADOS
            caras.append((anterior[q], interior[q], interior[k], anterior[k]))
        anterior = interior
    if j == 3:
        # La terminación no coplanar no debe ser un n-gon: su triangulación
        # implícita producía una muesca visual en el canino. Abanico explícito.
        t = -.232
        centro = len(vertices)
        vertices.append((0., 0., t if superior else -t))
        colores.append(_color(t, j))
        for q in range(_LADOS):
            caras.append((anterior[(q+1)%_LADOS], anterior[q], centro))
    else:
        caras.append(tuple(reversed(anterior)))
    caras.append(tuple((len(muestras)-1)*_LADOS+q for q in range(_LADOS)))
    return vertices, caras, colores


def datos_gingiva(indice, superior):
    """Manguito cervical cerrado dentro de la envolvente dental original.

    Primer anillo coincide con esmalte; el labio marginal crece suavemente
    hacia la antigua superficie, cubriendo el cuello sin ampliar colisiones.
    No simula ligamento, raíz ni periodonto clínico.
    """
    j = min(indice, 11-indice)
    if j < 3:
        return [], [], []
    vertices, caras, colores = [], [], []
    pasos = (0., .015, .05, .12, .25, .45, .7, 1.)
    for f in pasos:
        for q in range(_LADOS):
            margen = _margen(j, q, superior)
            t = margen+(.25-margen)*f
            cx, cy = _punto_corona(t, j, q, indice)
            ex, ey = _envolvente(t, j, q)
            # Cuello conectado sin el abultamiento cilíndrico de v2.
            mezcla = .50*_suave(f/.42)
            x, y = cx+(ex*.985-cx)*mezcla, cy+(ey*.985-cy)*mezcla
            vertices.append((x, y, t if superior else -t))
            # Color de referencia; runtime puede usar su material de encía.
            perfusion = math.exp(-((f-.12)/.13)**2)
            colores.append((.57+.025*f+.018*perfusion,
                            .26+.025*f-.007*perfusion, .285+.02*f, 1.))
    for r in range(len(pasos)-1):
        for q in range(_LADOS):
            a, b = r*_LADOS+q, r*_LADOS+(q+1)%_LADOS
            caras.append((a, b, b+_LADOS, a+_LADOS))
    caras.append(tuple(reversed(range(_LADOS))))
    caras.append(tuple((len(pasos)-1)*_LADOS+q for q in range(_LADOS)))
    return vertices, caras, colores


def construir():
    """Sustituir sólo datos de coronas; preservar matriz, nombre y materiales."""
    import bpy
    import bmesh

    resultado = []
    gingiva = {True: ([], [], []), False: ([], [], [])}
    for ob in list(bpy.context.scene.objects):
        match = re.fullmatch(r'diente_(sup|inf)_(\d{2})', ob.name)
        if ob.type != 'MESH' or match is None:
            continue
        indice, superior = int(match[2]), match[1] == 'sup'
        vertices, caras, colores = datos_corona(indice, superior)
        gv, gf, gc = datos_gingiva(indice, superior)
        if gv:
            from mathutils import Vector
            vv, ff, cc = gingiva[superior]
            offset = len(vv)
            vv.extend(tuple(ob.matrix_world @ Vector(v)) for v in gv)
            ff.extend(tuple(offset+k for k in cara) for cara in gf)
            cc.extend(gc)
        old = ob.data
        mesh = bpy.data.meshes.new(ob.name+'_esmalte')
        mesh.from_pydata(vertices, [], caras)
        mesh.update()
        # Recalcular orientación también en inferiores (z reflejada), sin
        # operadores que cambien selección, modo o contexto del generador.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        for mat in old.materials:
            mesh.materials.append(mat)
        color = mesh.vertex_colors.new(name='esmalte')
        for loop in mesh.loops:
            color.data[loop.index].color = colores[loop.vertex_index]
        for p in mesh.polygons:
            p.use_smooth = len(p.vertices) == 4 or (
                indice in (3, 8) and len(p.vertices) == 3)
        ob.data = mesh
        ob['corona_visual'] = 'esmalte_v4'
        resultado.append({'nombre': ob.name, 'vertices': len(vertices)})
        if old.users == 0:
            bpy.data.meshes.remove(old)
    for superior, (vertices, caras, colores) in gingiva.items():
        if not vertices:
            continue
        nombre = 'papila_%s_dentalv2' % ('sup' if superior else 'inf')
        anterior = bpy.data.objects.get(nombre)
        if anterior:
            old = anterior.data
            bpy.data.objects.remove(anterior, do_unlink=True)
            if old.users == 0:
                bpy.data.meshes.remove(old)
        mesh = bpy.data.meshes.new(nombre)
        mesh.from_pydata(vertices, [], caras)
        mesh.update()
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        color = mesh.vertex_colors.new(name='gingiva')
        for loop in mesh.loops:
            color.data[loop.index].color = colores[loop.vertex_index]
        for p in mesh.polygons:
            p.use_smooth = True
        ob = bpy.data.objects.new(nombre, mesh)
        bpy.context.collection.objects.link(ob)
        # Geometría agregada ya en coordenadas de escena; matriz identidad.
        # El visor añade el conjunto inferior a dentroMandibula, igual que
        # los dientes. No aplicar aquí el movimiento mandibular por segunda vez.
        fuente = bpy.data.objects.get('encia_superior' if superior else 'encia_inferior')
        if fuente and fuente.data.materials:
            mesh.materials.append(fuente.data.materials[0])
        ob['gingiva_visual'] = 'manguitos_cervicales_v3'
        resultado.append({'nombre': nombre, 'vertices': len(vertices)})
    return resultado
