"""Biblioteca compartilhada: carregar movel de blend BlenderKit, normalizar, aplicar efeitos.

Os blends BlenderKit vem com um objeto 'Cube' 2x2x2 (container de thumbnail) que
precisa ser ignorado, e a geometria real em 1+ sub-meshes. Esta lib:
- importa so a geometria real
- junta tudo em 1 mesh
- normaliza pra altura-alvo, apoia em Z=0, centraliza em XY
- aplica efeito CARDBOARD (geo nodes) ou MASSINHA (clay material + displacement)
"""
import bpy, bmesh, math, mathutils, os

CARDBOARD_BLEND = r"C:\Users\manu\ved\blender-experiments-2026\experiment-13-easy-cardboard\assets\easy-cardboard-3.1.blend"
CLAY_BLEND = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"
NG_CARDBOARD = "\U0001F4E6 Easy Cardboard 3.0"
NG_SMOOTH = "Smooth by Angle"
MAT_CARDBOARD = "Easy Cardboard 3"


def log(m): print(f"[LIB] {m}", flush=True)


def _set_input(mod, name, value):
    ng = mod.node_group
    target = name.strip()
    for item in ng.interface.items_tree:
        if getattr(item, 'in_out', None) == 'INPUT' and (item.name or "").strip() == target:
            try:
                mod[item.identifier] = value
                return True
            except Exception as e:
                log(f"  set_input fail {name!r}: {e}")
                return False
    log(f"  socket nao encontrado: {name!r}")
    return False


def import_furniture(blend_path, name):
    """Importa geometria real do blend (ignora Cube container), junta em 1 mesh chamado `name`."""
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(blend_path, link=False) as (df, dt):
        dt.objects = list(df.objects)
    imported = [o for o in bpy.data.objects if o not in before]
    # linkar a cena
    for o in imported:
        if o.name not in bpy.context.collection.objects:
            try: bpy.context.collection.objects.link(o)
            except Exception: pass

    # filtrar: meshes reais (descartar Cube container de 8 verts 2x2x2)
    real = []
    for o in imported:
        if o.type != 'MESH':
            continue
        if o.name == 'Cube' and len(o.data.vertices) == 8:
            continue
        # qualquer mesh de 8 verts cubo 2x2x2 perfeito = container
        if len(o.data.vertices) == 8 and tuple(round(d,2) for d in o.dimensions) == (2.0,2.0,2.0):
            continue
        real.append(o)

    # deletar nao-reais importados (containers, empties, cameras, luzes do asset)
    for o in imported:
        if o not in real:
            try: bpy.data.objects.remove(o, do_unlink=True)
            except Exception: pass

    if not real:
        raise RuntimeError(f"nenhuma mesh real em {blend_path}")

    # join
    bpy.ops.object.select_all(action='DESELECT')
    for o in real:
        o.select_set(True)
    bpy.context.view_layer.objects.active = real[0]
    if len(real) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    # aplicar transforms pra escala/rot ficarem 1
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def normalize(obj, target_height, floor_z=0.0):
    """Escala uniforme pra altura Z = target_height, apoia base em floor_z, centraliza XY."""
    bpy.context.view_layer.update()
    # bbox em world
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    mins = mathutils.Vector((min(c[i] for c in corners) for i in range(3)))
    maxs = mathutils.Vector((max(c[i] for c in corners) for i in range(3)))
    size = maxs - mins
    h = size.z if size.z > 1e-5 else 1.0
    s = target_height / h
    obj.scale = (s, s, s)
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    mins = mathutils.Vector((min(c[i] for c in corners) for i in range(3)))
    maxs = mathutils.Vector((max(c[i] for c in corners) for i in range(3)))
    cx = (mins.x + maxs.x) / 2
    cy = (mins.y + maxs.y) / 2
    obj.location.x -= cx
    obj.location.y -= cy
    obj.location.z += (floor_z - mins.z)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def ensure_uv(obj):
    """Garante uma UV ativa. Smart project se nao tiver (cardboard precisa)."""
    me = obj.data
    if not me.uv_layers:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
        bpy.ops.object.mode_set(mode='OBJECT')
    me.uv_layers.active_index = 0
    me.uv_layers[0].active_render = True
    return me.uv_layers[0].name


# ---------- CARDBOARD ----------
_cb_loaded = False
def _load_cardboard():
    global _cb_loaded
    if _cb_loaded:
        return
    names = [NG_CARDBOARD, NG_SMOOTH]
    with bpy.data.libraries.load(CARDBOARD_BLEND, link=False) as (df, dt):
        dt.node_groups = [n for n in names if n in df.node_groups]
        dt.materials = [MAT_CARDBOARD] if MAT_CARDBOARD in df.materials else []
    _cb_loaded = True


def apply_cardboard(obj):
    """Aplica Easy Cardboard como modifier GeoNodes + smooth, faz apply (geometria real)."""
    _load_cardboard()
    uv_name = ensure_uv(obj)
    obj.data.materials.clear()
    obj.data.materials.append(bpy.data.materials[MAT_CARDBOARD])

    ng_cb = bpy.data.node_groups[NG_CARDBOARD]
    m = obj.modifiers.new("EC", 'NODES')
    m.node_group = ng_cb
    # escala global: moveis sao ~0.4-1m; corrugacao default e calibrada pra metros.
    preset = {
        "Thickness": 0.015,
        "Global Scale": 0.5,
        "Wear ⏰": 0.25,
        "Strength": 0.35,
        "Separation": 1.0,
        "Separation Noise Scale": 1.0,
        "Z Position": 1.0,
        " Fibers Density": 4.0,
        "Fibers Size": 0.02,
        "Displacement Strength": 0.3,
        "Normal Strength": 1.0,
        "UV Name": uv_name,
    }
    for k, v in preset.items():
        _set_input(m, k, v)

    ng_sm = bpy.data.node_groups.get(NG_SMOOTH)
    msm = None
    if ng_sm:
        msm = obj.modifiers.new("Smooth", 'NODES')
        msm.node_group = ng_sm
        _set_input(msm, 'Angle', math.radians(30.0))

    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="EC")
    if not obj.data.materials or obj.data.materials[0] is None:
        obj.data.materials.clear(); obj.data.materials.append(bpy.data.materials[MAT_CARDBOARD])
    if msm:
        bpy.ops.object.modifier_apply(modifier="Smooth")
        if not obj.data.materials or obj.data.materials[0] is None:
            obj.data.materials.clear(); obj.data.materials.append(bpy.data.materials[MAT_CARDBOARD])
    log(f"  cardboard applied: {len(obj.data.vertices)}v / {len(obj.data.polygons)}f")
    return obj


# ---------- MASSINHA (Clay Doh) ----------
def _set_group_input(mat, name, value):
    """Seta input por nome no node group GROUP do material clay."""
    for n in mat.node_tree.nodes:
        if n.type == 'GROUP':
            for sock in n.inputs:
                if sock.name == name:
                    try:
                        sock.default_value = value
                        return True
                    except Exception as e:
                        log(f"  clay set {name!r} fail: {e}")
                        return False
    return False


def apply_clay(obj, clay_mat="Modeling Clay", subdiv_render=4,
               color=None, displacement=0.18, tex_scale=14.0):
    """Aplica material Clay Doh (procedural, displacement BOTH = relevo real de massa).
    Cycles displacement precisa de geometria densa -> Subdivision modifier (adaptive)."""
    with bpy.data.libraries.load(CLAY_BLEND, link=False) as (df, dt):
        if clay_mat in df.materials:
            dt.materials = [clay_mat]
    mat = bpy.data.materials.get(clay_mat)
    if mat is None:
        raise RuntimeError(f"material clay {clay_mat!r} nao carregou")
    mat = mat.copy()
    mat.name = f"{clay_mat}_{obj.name}"
    mat.displacement_method = 'BOTH'
    # parametros de look da massinha
    if color is not None:
        _set_group_input(mat, "Clay Color", (*color, 1.0))
    _set_group_input(mat, "Displacement Strength", displacement)
    _set_group_input(mat, "Global Displacement", displacement)
    _set_group_input(mat, "Texture Scale", tex_scale)
    _set_group_input(mat, "Global Texture Scale", tex_scale)
    _set_group_input(mat, "Random Per Object: No | Yes", 1.0)

    obj.data.materials.clear()
    obj.data.materials.append(mat)
    ensure_uv(obj)

    # Subdivision modifier com adaptive subdivision do Cycles (relevo de microtextura)
    msub = obj.modifiers.new("ClaySubsurf", 'SUBSURF')
    msub.subdivision_type = 'CATMULL_CLARK'
    msub.levels = 2
    msub.render_levels = subdiv_render
    # adaptive subdivision do Cycles fica no modifier (Blender 5.x)
    try:
        msub.use_adaptive_subdivision = True
    except Exception:
        # fallback: campo da mesh.cycles
        try:
            obj.data.cycles.use_adaptive_subdivision = True
        except Exception as e:
            log(f"  adaptive subdiv via fallback indisponivel: {e}")
    log(f"  clay applied ({clay_mat}): displacement={mat.displacement_method}")
    return obj
