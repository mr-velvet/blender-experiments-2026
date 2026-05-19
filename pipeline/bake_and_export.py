"""
Pipeline: gera (forma x material) -> bake PBR -> GLB exportavel.

Roda 1 combo por invocacao do Blender (mais seguro). Argumentos depois de `--`:
  --shape {cube,sphere,cylinder,torus,suzanne}
  --material "Nome do material"
  --src-blend caminho.blend
  --out-glb caminho.glb
  --out-render caminho.png (opcional)
  --tex-dir pasta_para_texturas_bakeadas
  --bake-res 1024
"""
import bpy
import bmesh
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
    p.add_argument("--bake-res", type=int, default=1024)
    p.add_argument("--combo-id", required=True, help="prefixo unico das texturas")
    return p.parse_args(argv)


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def create_shape(shape):
    if shape == "cube":
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 1))
    elif shape == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 1))
        bpy.ops.object.shade_smooth()
    elif shape == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 1))
        bpy.ops.object.shade_smooth()
    elif shape == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.35, location=(0, 0, 1))
        bpy.ops.object.shade_smooth()
    elif shape == "suzanne":
        bpy.ops.mesh.primitive_monkey_add(size=1.5, location=(0, 0, 1))
        bpy.ops.object.shade_smooth()
    obj = bpy.context.active_object
    obj.name = "Target"
    return obj


def append_material(src_blend, mat_name):
    with bpy.data.libraries.load(src_blend, link=False) as (data_from, data_to):
        if mat_name not in data_from.materials:
            raise SystemExit(f"Material {mat_name!r} nao existe em {src_blend}. "
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
    img = bpy.data.images.new(
        name=name, width=res, height=res, alpha=False,
        float_buffer=False, is_data=(is_data or is_normal)
    )
    return img


def bake_pass(obj, mat, image, bake_type, normal_space='TANGENT'):
    """Add Image Texture node, set active, bake. Bake settings: Cycles."""
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
        scene.render.bake.normal_space = normal_space
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


def build_pbr_material(name, base_color_img, roughness_img, normal_img):
    mat = bpy.data.materials.new(name=name + "_PBR")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    out.location = (400, 0)
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    bc_node = nodes.new('ShaderNodeTexImage')
    bc_node.image = base_color_img
    bc_node.location = (-400, 200)
    links.new(bc_node.outputs['Color'], bsdf.inputs['Base Color'])

    r_node = nodes.new('ShaderNodeTexImage')
    r_node.image = roughness_img
    r_node.image.colorspace_settings.name = 'Non-Color'
    r_node.location = (-400, -100)
    links.new(r_node.outputs['Color'], bsdf.inputs['Roughness'])

    n_tex = nodes.new('ShaderNodeTexImage')
    n_tex.image = normal_img
    n_tex.image.colorspace_settings.name = 'Non-Color'
    n_tex.location = (-700, -400)
    n_map = nodes.new('ShaderNodeNormalMap')
    n_map.location = (-300, -400)
    links.new(n_tex.outputs['Color'], n_map.inputs['Color'])
    links.new(n_map.outputs['Normal'], bsdf.inputs['Normal'])

    return mat


def setup_render_camera_lights():
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    cam.location = (4, -4, 3.2)
    cam.rotation_euler = (1.0, 0, 0.785)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (0.785, 0.3, 0.5)
    bpy.context.scene.collection.objects.link(sun)

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
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
    src_mat = append_material(args.src_blend, args.material)
    obj.data.materials.clear()
    obj.data.materials.append(src_mat)
    smart_unwrap(obj)

    res = args.bake_res
    bc_img = make_bake_image(f"{args.combo_id}_baseColor", res)
    r_img = make_bake_image(f"{args.combo_id}_roughness", res, is_data=True)
    n_img = make_bake_image(f"{args.combo_id}_normal", res, is_normal=True)

    print(f"BAKING: {args.combo_id} ({args.shape} x {args.material})")
    bake_pass(obj, src_mat, bc_img, 'DIFFUSE')
    bake_pass(obj, src_mat, r_img, 'ROUGHNESS')
    bake_pass(obj, src_mat, n_img, 'NORMAL')

    bc_path = os.path.join(args.tex_dir, f"{args.combo_id}_baseColor.png")
    r_path = os.path.join(args.tex_dir, f"{args.combo_id}_roughness.png")
    n_path = os.path.join(args.tex_dir, f"{args.combo_id}_normal.png")
    save_image(bc_img, bc_path)
    save_image(r_img, r_path)
    save_image(n_img, n_path)
    print(f"BAKED_TEXTURES: {bc_path}, {r_path}, {n_path}")

    pbr_mat = build_pbr_material(args.combo_id, bc_img, r_img, n_img)
    obj.data.materials.clear()
    obj.data.materials.append(pbr_mat)

    setup_render_camera_lights()
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
