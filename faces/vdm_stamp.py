"""4b: estampa um brush VDM no centro de cada face da mesh original.

Estrategia:
  1. Cria mesh primitiva (cube/icosphere/cilindro/etc) com poucas faces grandes
  2. Memoriza centro+normal+tangentes de cada face ORIGINAL
  3. Subdivide a mesh densamente (geometria pra deformar)
  4. Pra cada face original, pra cada vertex novo dentro do disco do stamp:
     - sample EXR no UV do disco
     - converte RGB do VDM em deslocamento tangent-space
     - aplica no vertex
  5. Aplica material Clay Doh, smart unwrap, bake, GLB

Args (depois de --):
  --shape {cube,sphere,cylinder,torus,suzanne,icosphere}
  --exr  caminho EXR do brush
  --material "Nome do material" (Clay Doh, etc)
  --src-blend caminho .blend dos materiais
  --out-glb caminho.glb
  --out-render caminho.png
  --tex-dir pasta
  --combo-id slug
  --bake-res 1024
  --subdiv-levels 5
  --stamp-scale 0.85   # 1.0 = stamp cobre face inteira; <1 deixa margem
  --displace-strength 0.5
"""
import bpy
import bmesh
import os
import sys
import math
import argparse
from mathutils import Vector


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--shape", required=True,
                   choices=["cube", "sphere", "cylinder", "torus", "suzanne", "icosphere"])
    p.add_argument("--exr", required=True, help="EXR vector displacement map")
    p.add_argument("--material", required=True)
    p.add_argument("--src-blend", required=True)
    p.add_argument("--out-glb", required=True)
    p.add_argument("--out-render", default=None)
    p.add_argument("--tex-dir", required=True)
    p.add_argument("--combo-id", required=True)
    p.add_argument("--bake-res", type=int, default=1024)
    p.add_argument("--subdiv-levels", type=int, default=5)
    p.add_argument("--stamp-scale", type=float, default=0.85)
    p.add_argument("--displace-strength", type=float, default=0.5)
    p.add_argument("--smooth-result", action="store_true",
                   help="aplica subdivisao final pra suavizar")
    p.add_argument("--no-clay", action="store_true",
                   help="usa material cinza simples (sem clay doh) pra ver relevo melhor")
    return p.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def create_shape(shape):
    if shape == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    elif shape == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1),
                                              segments=12, ring_count=8)
    elif shape == "icosphere":
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1, location=(0, 0, 1), subdivisions=1)
    elif shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1),
                                             vertices=12)
    elif shape == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.4,
                                          location=(0, 0, 1),
                                          major_segments=12, minor_segments=8)
    elif shape == "suzanne":
        bpy.ops.mesh.primitive_monkey_add(size=1.5, location=(0, 0, 1))
    obj = bpy.context.active_object
    obj.name = "Target"
    return obj


def collect_face_anchors(obj):
    """Snapshot do centro/normal/tangentes/raio de cada face ANTES da subdivisao."""
    mw = obj.matrix_world
    anchors = []
    mesh = obj.data
    for poly in mesh.polygons:
        center = mw @ poly.center
        normal = (mw.to_3x3() @ poly.normal).normalized()
        # tangentes: escolhe um edge da face como U, calcula V por cross com normal
        if len(poly.vertices) >= 2:
            v0 = mw @ mesh.vertices[poly.vertices[0]].co
            v1 = mw @ mesh.vertices[poly.vertices[1]].co
            t_u = (v1 - v0).normalized()
            # garantir ortonormalidade
            t_u = (t_u - normal * t_u.dot(normal)).normalized()
            t_v = normal.cross(t_u).normalized()
        else:
            t_u = Vector((1, 0, 0))
            t_v = Vector((0, 1, 0))
        radius = math.sqrt(poly.area) * 0.5  # ~raio do disco circunscrito
        anchors.append({
            "center": center,
            "normal": normal,
            "u": t_u,
            "v": t_v,
            "radius": radius,
        })
    print(f"[anchors] coletados {len(anchors)} pontos de estampa")
    return anchors


def subdivide_mesh(obj, levels, preserve_creases=True):
    """Subdivide com Subsurf. Se preserve_creases, marca todas as edges com
    crease=1 antes via bmesh (preserva as quinas do cubo/cilindro/torus)."""
    if preserve_creases:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        # garantir crease layer
        crease_layer = bm.edges.layers.float.get("crease_edge")
        if crease_layer is None:
            crease_layer = bm.edges.layers.float.new("crease_edge")
        for e in bm.edges:
            e[crease_layer] = 1.0
        bm.to_mesh(obj.data)
        bm.free()
        print(f"[crease] marcadas {len(obj.data.edges)} edges com crease=1")
    mod = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = levels
    mod.use_creases = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"[subdiv] mesh subdividida {levels}x (creases={preserve_creases}) -> {len(obj.data.vertices)} vertices")


def load_exr_pixels(exr_path):
    """Carrega EXR via bpy e devolve um buffer (W, H, 4) de float."""
    img = bpy.data.images.load(exr_path, check_existing=False)
    w, h = img.size
    pixels = list(img.pixels)  # flat [r,g,b,a, r,g,b,a, ...]
    print(f"[exr] {exr_path} -> {w}x{h}, {len(pixels)} floats")
    return img, w, h, pixels


def sample_exr_bilinear(pixels, w, h, u, v):
    """u,v em [0,1]. Retorna (r,g,b)."""
    # clamp
    u = max(0.0, min(1.0, u))
    v = max(0.0, min(1.0, v))
    x = u * (w - 1)
    y = v * (h - 1)
    x0, y0 = int(x), int(y)
    x1 = min(x0 + 1, w - 1)
    y1 = min(y0 + 1, h - 1)
    fx, fy = x - x0, y - y0
    def px(xi, yi):
        idx = (yi * w + xi) * 4
        return pixels[idx], pixels[idx+1], pixels[idx+2]
    r00, g00, b00 = px(x0, y0)
    r10, g10, b10 = px(x1, y0)
    r01, g01, b01 = px(x0, y1)
    r11, g11, b11 = px(x1, y1)
    def lerp(a, b, t): return a + (b - a) * t
    r = lerp(lerp(r00, r10, fx), lerp(r01, r11, fx), fy)
    g = lerp(lerp(g00, g10, fx), lerp(g01, g11, fx), fy)
    b = lerp(lerp(b00, b10, fx), lerp(b01, b11, fx), fy)
    return r, g, b


def apply_vdm_stamps(obj, anchors, exr_path, stamp_scale, displace_strength):
    """Para cada anchor, para cada vertex dentro do disco, sample EXR e desloca."""
    img, w, h, pixels = load_exr_pixels(exr_path)
    mw = obj.matrix_world
    mw_inv = mw.inverted()

    mesh = obj.data
    # ler todas as posicoes em world space pra acelerar (pra mesh tipica eh barato)
    verts_world = [mw @ v.co for v in mesh.vertices]
    deltas = [Vector((0, 0, 0)) for _ in mesh.vertices]

    total_displaced = 0
    for anchor in anchors:
        c = anchor["center"]
        n = anchor["normal"]
        u_axis = anchor["u"]
        v_axis = anchor["v"]
        # raio "efetivo" do stamp = radius * stamp_scale, mas o disco do EXR
        # cobre o quadrado [-1,1] x [-1,1] em tangent space. Usar half-side:
        half = anchor["radius"] * stamp_scale

        for i, vw in enumerate(verts_world):
            d = vw - c
            # filtrar: distancia ao plano da face nao pode ser muito grande
            n_dist = abs(d.dot(n))
            if n_dist > half * 1.5:
                continue
            u_local = d.dot(u_axis)
            v_local = d.dot(v_axis)
            # dentro do quadrado?
            if abs(u_local) > half or abs(v_local) > half:
                continue
            # UV no EXR ([0,1])
            u_t = (u_local / half) * 0.5 + 0.5
            v_t = (v_local / half) * 0.5 + 0.5
            r, g, b = sample_exr_bilinear(pixels, w, h, u_t, v_t)
            # VDM convention: R=tangent (u), G=bitangent (v), B=normal
            # Centrado em 0 (cinza neutro = 0.5? ou 0?) -- EXRs sao linear, geralmente
            # ja centrados em 0 e nao em 0.5. Vou tratar como ja centrado.
            # MAS: alguns packs usam 0.5 como neutro. Vou usar (val) direto e ajustar
            # via displace-strength se precisar.
            dr = r
            dg = g
            db = b
            delta = (u_axis * dr + v_axis * dg + n * db) * displace_strength
            # falloff radial nas bordas (suaviza so na borda final, preserva detalhe centro)
            r_local = math.sqrt((u_local/half)**2 + (v_local/half)**2)
            if r_local > 0.85:
                falloff = max(0.0, 1.0 - (r_local - 0.85) / 0.15)
            else:
                falloff = 1.0
            delta = delta * falloff
            deltas[i] += delta
            total_displaced += 1

    # aplica deltas (converter de world pra local)
    rot_inv = mw_inv.to_3x3()
    for i, v in enumerate(mesh.vertices):
        if deltas[i].length_squared > 0:
            v.co += rot_inv @ deltas[i]
    mesh.update()
    print(f"[stamp] aplicado: {total_displaced} sample writes, "
          f"{sum(1 for d in deltas if d.length_squared > 0)} verts deslocados")


def smooth_normals(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()


def append_material(src_blend, mat_name):
    with bpy.data.libraries.load(src_blend, link=False) as (data_from, data_to):
        if mat_name not in data_from.materials:
            raise SystemExit(f"Material {mat_name!r} nao existe. "
                             f"Disponiveis: {list(data_from.materials)}")
        data_to.materials = [mat_name]
    return bpy.data.materials[mat_name]


def smart_unwrap(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15192, island_margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')


def make_bake_image(name, res, is_normal=False, is_data=False):
    return bpy.data.images.new(name=name, width=res, height=res, alpha=False,
                                float_buffer=False, is_data=(is_data or is_normal))


def bake_pass(obj, mat, image, bake_type):
    nodes = mat.node_tree.nodes
    tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.select = True; nodes.active = tex
    s = bpy.context.scene
    s.render.engine = 'CYCLES'; s.cycles.samples = 16; s.cycles.bake_type = bake_type
    s.render.bake.use_pass_direct = False; s.render.bake.use_pass_indirect = False
    s.render.bake.use_pass_color = True; s.render.bake.margin = 8; s.render.bake.use_clear = True
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    if bake_type == 'NORMAL':
        s.render.bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type='NORMAL')
    elif bake_type == 'ROUGHNESS':
        bpy.ops.object.bake(type='ROUGHNESS')
    elif bake_type == 'DIFFUSE':
        bpy.ops.object.bake(type='DIFFUSE')
    nodes.remove(tex)


def save_image(img, path):
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()


def build_pbr_material(name, bc, r, n):
    mat = bpy.data.materials.new(name=name + "_PBR"); mat.use_nodes = True
    nodes = mat.node_tree.nodes; links = mat.node_tree.links; nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bcn = nodes.new('ShaderNodeTexImage'); bcn.image = bc; bcn.location = (-400, 200)
    links.new(bcn.outputs['Color'], bsdf.inputs['Base Color'])
    rn = nodes.new('ShaderNodeTexImage'); rn.image = r; rn.image.colorspace_settings.name = 'Non-Color'; rn.location = (-400, -100)
    links.new(rn.outputs['Color'], bsdf.inputs['Roughness'])
    nt = nodes.new('ShaderNodeTexImage'); nt.image = n; nt.image.colorspace_settings.name = 'Non-Color'; nt.location = (-700, -400)
    nm = nodes.new('ShaderNodeNormalMap'); nm.location = (-300, -400)
    links.new(nt.outputs['Color'], nm.inputs['Color'])
    links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def setup_render(close=False):
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    if close:
        cam.location = (2.5, -2.5, 2.0); cam.rotation_euler = (1.0, 0, 0.785)
    else:
        cam.location = (5.5, -5.5, 4.5); cam.rotation_euler = (0.95, 0, 0.785)
    bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
    sun_data = bpy.data.lights.new("Sun", type='SUN'); sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data); sun.rotation_euler = (0.785, 0.3, 0.5)
    bpy.context.scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("World"); world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
        bg.inputs['Strength'].default_value = 0.5
    bpy.context.scene.world = world


def render_preview(out_path):
    s = bpy.context.scene
    s.render.engine = 'CYCLES'; s.cycles.samples = 64
    s.render.resolution_x = 600; s.render.resolution_y = 600
    s.render.filepath = out_path; s.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    os.makedirs(args.tex_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.out_glb), exist_ok=True)
    if args.out_render:
        os.makedirs(os.path.dirname(args.out_render), exist_ok=True)

    reset_scene()
    obj = create_shape(args.shape)

    # 1. Snapshot dos centros antes de subdividir
    anchors = collect_face_anchors(obj)

    # 2. Subdividir densamente. Preservar creases SO em primitivos quadrangulares
    # (cube tem 6 quads, cylinder com vertices=12 tem 14 faces sendo 12 quads laterais).
    # Icosphere/sphere/suzanne sao organicos -> nao preservar.
    preserve = args.shape in ("cube", "cylinder")
    subdivide_mesh(obj, args.subdiv_levels, preserve_creases=preserve)

    # 3. Aplicar VDM stamps
    apply_vdm_stamps(obj, anchors, args.exr, args.stamp_scale, args.displace_strength)
    smooth_normals(obj)

    # 4. Material + bake + GLB
    if args.no_clay:
        # material cinza simples pra ver relevo
        src_mat = bpy.data.materials.new(name="GrayClay")
        src_mat.use_nodes = True
        bsdf = src_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.75, 0.65, 0.55, 1)
            bsdf.inputs["Roughness"].default_value = 0.7
    else:
        src_mat = append_material(args.src_blend, args.material)
    obj.data.materials.clear(); obj.data.materials.append(src_mat)
    smart_unwrap(obj)

    res = args.bake_res
    bc = make_bake_image(f"{args.combo_id}_baseColor", res)
    rg = make_bake_image(f"{args.combo_id}_roughness", res, is_data=True)
    nm = make_bake_image(f"{args.combo_id}_normal", res, is_normal=True)
    print(f"BAKING: {args.combo_id}")
    bake_pass(obj, src_mat, bc, 'DIFFUSE')
    bake_pass(obj, src_mat, rg, 'ROUGHNESS')
    bake_pass(obj, src_mat, nm, 'NORMAL')

    bcp = os.path.join(args.tex_dir, f"{args.combo_id}_baseColor.png")
    rp = os.path.join(args.tex_dir, f"{args.combo_id}_roughness.png")
    np_ = os.path.join(args.tex_dir, f"{args.combo_id}_normal.png")
    save_image(bc, bcp); save_image(rg, rp); save_image(nm, np_)

    pbr = build_pbr_material(args.combo_id, bc, rg, nm)
    obj.data.materials.clear(); obj.data.materials.append(pbr)

    setup_render(close=False)
    if args.out_render:
        render_preview(args.out_render); print(f"RENDER_OK: {args.out_render}")

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=args.out_glb, export_format='GLB',
        use_selection=True, export_apply=True,
        export_materials='EXPORT', export_image_format='AUTO',
    )
    print(f"GLB_OK: {args.out_glb} ({os.path.getsize(args.out_glb)} bytes)")


main()
