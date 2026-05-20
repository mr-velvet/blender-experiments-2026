"""Pipeline 4a: forma -> subdiv + displace procedural ('massinha amassada')
-> aplica material Clay Doh -> bake -> GLB.

Diferencas vs pipeline original:
  1. Mesh inicial eh subdividida (modifier) pra ter geometria suficiente
  2. Displace modifier com noise texture deforma a mesh de verdade
  3. Ambos modifiers sao APLICADOS antes do bake/export -> GLB tem geometria real

Args (depois de --):
  --shape {sphere,cube,cylinder,torus,suzanne}
  --material "Nome do material"
  --src-blend caminho.blend
  --out-glb caminho.glb
  --out-render caminho.png
  --tex-dir pasta_para_texturas_bakeadas
  --combo-id prefixo
  --bake-res 1024
  --subdiv-levels 4         # subdivisoes antes do displace
  --displace-strength 0.15  # 0=sem amassado, 0.3=bem amassado
  --noise-scale 1.5         # frequencia do noise (maior = bumps menores)
"""
import bpy
import os
import sys
import argparse


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--shape", required=True,
                   choices=["cube", "sphere", "cylinder", "torus", "suzanne"])
    p.add_argument("--material", required=True)
    p.add_argument("--src-blend", required=True)
    p.add_argument("--out-glb", required=True)
    p.add_argument("--out-render", default=None)
    p.add_argument("--tex-dir", required=True)
    p.add_argument("--combo-id", required=True)
    p.add_argument("--bake-res", type=int, default=1024)
    p.add_argument("--subdiv-levels", type=int, default=4)
    p.add_argument("--displace-strength", type=float, default=0.15)
    p.add_argument("--noise-scale", type=float, default=1.5)
    return p.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def create_shape(shape):
    if shape == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    elif shape == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1),
                                              segments=32, ring_count=16)
    elif shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1),
                                             vertices=32)
    elif shape == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.35,
                                          location=(0, 0, 1),
                                          major_segments=48, minor_segments=24)
    elif shape == "suzanne":
        bpy.ops.mesh.primitive_monkey_add(size=1.5, location=(0, 0, 1))
    obj = bpy.context.active_object
    obj.name = "Target"
    bpy.ops.object.shade_smooth()
    return obj


def add_subdiv_and_displace(obj, subdiv_levels, displace_strength, noise_scale):
    """Adiciona Subsurf + Displace com noise, aplica os dois."""
    # Subsurf
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = subdiv_levels
    subsurf.render_levels = subdiv_levels

    # Texture noise (precisa criar uma data texture pro Displace usar)
    tex = bpy.data.textures.new(name=f"NoiseTex_{obj.name}", type='NOISE')
    # tipo NOISE eh white noise; pra organico melhor usar MUSGRAVE/CLOUDS
    # mudar pra CLOUDS pra ter bumps suaves estilo massinha
    tex2 = bpy.data.textures.new(name=f"CloudsTex_{obj.name}", type='CLOUDS')
    tex2.noise_scale = 1.0 / max(noise_scale, 0.1)
    tex2.noise_depth = 2

    # Displace modifier
    disp = obj.modifiers.new(name="Displace", type='DISPLACE')
    disp.texture = tex2
    disp.strength = displace_strength
    disp.mid_level = 0.5

    # Aplica os modifiers (Subsurf primeiro, depois Displace)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=subsurf.name)
    bpy.ops.object.modifier_apply(modifier=disp.name)

    print(f"[squash] aplicado subsurf={subdiv_levels} + displace={displace_strength}")


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
    return bpy.data.images.new(
        name=name, width=res, height=res, alpha=False,
        float_buffer=False, is_data=(is_data or is_normal)
    )


def bake_pass(obj, mat, image, bake_type):
    nodes = mat.node_tree.nodes
    tex_node = nodes.new('ShaderNodeTexImage')
    tex_node.image = image
    tex_node.select = True
    nodes.active = tex_node

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.bake_type = bake_type
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True
    scene.render.bake.margin = 8
    scene.render.bake.use_clear = True

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if bake_type == 'NORMAL':
        scene.render.bake.normal_space = 'TANGENT'
        bpy.ops.object.bake(type='NORMAL')
    elif bake_type == 'ROUGHNESS':
        bpy.ops.object.bake(type='ROUGHNESS')
    elif bake_type == 'DIFFUSE':
        bpy.ops.object.bake(type='DIFFUSE')

    nodes.remove(tex_node)


def save_image(img, path):
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()


def build_pbr_material(name, bc, r, n):
    mat = bpy.data.materials.new(name=name + "_PBR")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial'); out.location = (400, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled'); bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bcn = nodes.new('ShaderNodeTexImage'); bcn.image = bc; bcn.location = (-400, 200)
    links.new(bcn.outputs['Color'], bsdf.inputs['Base Color'])
    rn = nodes.new('ShaderNodeTexImage'); rn.image = r
    rn.image.colorspace_settings.name = 'Non-Color'; rn.location = (-400, -100)
    links.new(rn.outputs['Color'], bsdf.inputs['Roughness'])
    nt = nodes.new('ShaderNodeTexImage'); nt.image = n
    nt.image.colorspace_settings.name = 'Non-Color'; nt.location = (-700, -400)
    nm = nodes.new('ShaderNodeNormalMap'); nm.location = (-300, -400)
    links.new(nt.outputs['Color'], nm.inputs['Color'])
    links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def setup_render():
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (4, -4, 3.2)
    cam.rotation_euler = (1.0, 0, 0.785)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
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
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.render.resolution_x = 600
    scene.render.resolution_y = 600
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    os.makedirs(args.tex_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.out_glb), exist_ok=True)
    if args.out_render:
        os.makedirs(os.path.dirname(args.out_render), exist_ok=True)

    reset_scene()
    obj = create_shape(args.shape)

    # NOVO: deforma a geometria antes de qualquer outra coisa
    add_subdiv_and_displace(
        obj,
        subdiv_levels=args.subdiv_levels,
        displace_strength=args.displace_strength,
        noise_scale=args.noise_scale,
    )

    src_mat = append_material(args.src_blend, args.material)
    obj.data.materials.clear()
    obj.data.materials.append(src_mat)
    smart_unwrap(obj)

    res = args.bake_res
    bc = make_bake_image(f"{args.combo_id}_baseColor", res)
    r = make_bake_image(f"{args.combo_id}_roughness", res, is_data=True)
    n = make_bake_image(f"{args.combo_id}_normal", res, is_normal=True)

    print(f"BAKING: {args.combo_id} ({args.shape} squashed x {args.material})")
    bake_pass(obj, src_mat, bc, 'DIFFUSE')
    bake_pass(obj, src_mat, r, 'ROUGHNESS')
    bake_pass(obj, src_mat, n, 'NORMAL')

    bcp = os.path.join(args.tex_dir, f"{args.combo_id}_baseColor.png")
    rp = os.path.join(args.tex_dir, f"{args.combo_id}_roughness.png")
    np_ = os.path.join(args.tex_dir, f"{args.combo_id}_normal.png")
    save_image(bc, bcp); save_image(r, rp); save_image(n, np_)

    pbr = build_pbr_material(args.combo_id, bc, r, n)
    obj.data.materials.clear()
    obj.data.materials.append(pbr)

    setup_render()
    if args.out_render:
        render_preview(args.out_render)
        print(f"RENDER_OK: {args.out_render}")

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=args.out_glb,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='EXPORT',
        export_image_format='AUTO',
    )
    print(f"GLB_OK: {args.out_glb} ({os.path.getsize(args.out_glb)} bytes)")


main()
