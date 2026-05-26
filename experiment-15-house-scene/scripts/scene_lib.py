"""
Biblioteca de montagem de cena (rodar dentro do Blender headless).

Responsabilidades:
- importar um gltf do PolyHaven e agrupar seus objetos sob um Empty (handle)
- medir a bounding box do conjunto no mundo
- posicionar (place): poe o asset no chao (base em Z=0), centra no XY do alvo,
  rotaciona em torno de Z, opcionalmente escala por altura/largura alvo
- construir o shell da casa (piso, paredes externas, divisorias) com material PBR
- camera e luzes

Convencao de eixos: Z = up, metros. PolyHaven exporta em escala real (metros),
entao raramente precisa reescalar — mas a API de place suporta caso precise.
"""
import json
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(bpy.path.abspath("//")) if bpy.data.filepath else None
EXP = Path(__file__).resolve().parent.parent
ASSETS = EXP / "assets"


# ---------------------------------------------------------------- import / medir

def _all_mesh_objects_before():
    return set(o.name for o in bpy.data.objects)


def import_gltf(slug):
    """Importa o gltf do slug, agrupa tudo sob um Empty nomeado, retorna o Empty."""
    manifest = json.loads((ASSETS / "_manifest.json").read_text(encoding="utf-8"))
    rel = manifest.get(slug)
    if not rel:
        raise FileNotFoundError(f"asset {slug} ausente no manifest")
    gltf_path = EXP / rel
    before = _all_mesh_objects_before()
    bpy.ops.import_scene.gltf(filepath=str(gltf_path))
    new = [bpy.data.objects[n] for n in
           (set(o.name for o in bpy.data.objects) - before)]
    # cria empty handle, faz parent de todas as raizes importadas
    handle = bpy.data.objects.new(f"H_{slug}", None)
    bpy.context.scene.collection.objects.link(handle)
    handle.empty_display_size = 0.1
    roots = [o for o in new if o.parent is None or o.parent.name not in
             set(x.name for x in new)]
    for r in roots:
        # preserva transform mundial ao reparentar
        mw = r.matrix_world.copy()
        r.parent = handle
        r.matrix_world = mw
    bpy.context.view_layer.update()
    handle["slug"] = slug
    return handle


def world_bbox(handle):
    """Bounding box (min, max) em coords de mundo de todas as meshes sob handle."""
    mins = Vector((1e9, 1e9, 1e9))
    maxs = Vector((-1e9, -1e9, -1e9))
    found = False
    for o in [handle] + list(_descendants(handle)):
        if o.type != "MESH":
            continue
        found = True
        for corner in o.bound_box:
            wc = o.matrix_world @ Vector(corner)
            for i in range(3):
                mins[i] = min(mins[i], wc[i])
                maxs[i] = max(maxs[i], wc[i])
    if not found:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    return mins, maxs


def _descendants(obj):
    for c in obj.children:
        yield c
        yield from _descendants(c)


def dims(handle):
    mn, mx = world_bbox(handle)
    return mx - mn


# ---------------------------------------------------------------- posicionamento

def place(handle, x, y, rot_z_deg=0.0, scale=None,
          target_height=None, on_floor=True, z_offset=0.0):
    """
    Posiciona um asset:
    - rot_z_deg: rotacao em torno de Z (graus)
    - scale: fator multiplicativo direto (opcional)
    - target_height: reescala uniformemente p/ o asset ter essa altura em Z (opcional)
    - on_floor: assenta a base do bbox em Z=0 (+ z_offset)
    - x,y: centro do bbox vai pra essa posicao no plano
    """
    # 1) rotacao
    handle.rotation_euler[2] = math.radians(rot_z_deg)
    bpy.context.view_layer.update()

    # 2) escala
    if target_height is not None:
        d = dims(handle)
        if d.z > 1e-6:
            f = target_height / d.z
            handle.scale = (handle.scale[0] * f,
                            handle.scale[1] * f,
                            handle.scale[2] * f)
            bpy.context.view_layer.update()
    elif scale is not None:
        handle.scale = (scale, scale, scale)
        bpy.context.view_layer.update()

    # 3) translacao: centra XY no alvo, base no chao
    mn, mx = world_bbox(handle)
    center = (mn + mx) / 2
    dx = x - center.x
    dy = y - center.y
    dz = (-mn.z + z_offset) if on_floor else z_offset
    handle.location.x += dx
    handle.location.y += dy
    handle.location.z += dz
    bpy.context.view_layer.update()
    return handle


def place_on(handle, support_handle, x=None, y=None, rot_z_deg=0.0,
             target_height=None, scale=None):
    """Coloca handle EM CIMA de support_handle (ex: vaso na mesa)."""
    smn, smx = world_bbox(support_handle)
    top_z = smx.z
    if x is None:
        x = (smn.x + smx.x) / 2
    if y is None:
        y = (smn.y + smx.y) / 2
    place(handle, x, y, rot_z_deg=rot_z_deg, target_height=target_height,
          scale=scale, on_floor=False)
    # agora assenta a base no topo do suporte
    mn, mx = world_bbox(handle)
    handle.location.z += (top_z - mn.z)
    bpy.context.view_layer.update()
    return handle


# ---------------------------------------------------------------- materiais PBR

def _img(path):
    return bpy.data.images.load(str(EXP / path), check_existing=True)


def pbr_material(name, diffuse, normal=None, rough=None, scale_uv=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # mapping p/ tilar a textura
    texcoord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale_uv, scale_uv, scale_uv)
    nt.links.new(texcoord.outputs["UV"], mapping.inputs["Vector"])

    d = nt.nodes.new("ShaderNodeTexImage")
    d.image = _img(diffuse)
    nt.links.new(mapping.outputs["Vector"], d.inputs["Vector"])
    nt.links.new(d.outputs["Color"], bsdf.inputs["Base Color"])

    if rough:
        r = nt.nodes.new("ShaderNodeTexImage")
        r.image = _img(rough)
        r.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mapping.outputs["Vector"], r.inputs["Vector"])
        nt.links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    if normal:
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = _img(normal)
        n.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(mapping.outputs["Vector"], n.inputs["Vector"])
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _make_box(name, size, location, material=None):
    """Cria uma caixa (parede/piso) com dimensoes size=(sx,sy,sz)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj.scale = size
    obj.location = location
    # UV simples
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    if material:
        obj.data.materials.append(material)
    return obj


# ---------------------------------------------------------------- camera/luz

def add_sun(energy=2.5, angle=(0.7, 0.2, 0.5)):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    o = bpy.data.objects.new("Sun", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = angle
    return o


def add_area_light(name, location, size=2.0, energy=200.0):
    d = bpy.data.lights.new(name, "AREA")
    d.energy = energy
    d.size = size
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = location
    return o


def add_camera(location, look_at, lens=35.0):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    direction = Vector(look_at) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def world_background(color=(0.9, 0.9, 0.92, 1.0), strength=1.0):
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = color
        bg.inputs["Strength"].default_value = strength


def setup_render(samples=128, res=(1600, 1000)):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "GPU"
    except Exception:
        pass
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX" if "AgX" in [
        v.name for v in sc.view_settings.bl_rna.properties["view_transform"].enum_items
    ] else "Filmic"


def render_to(path):
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
