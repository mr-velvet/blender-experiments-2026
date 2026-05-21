"""Experimento 8: cubo Clay Doh quebra ao cair.

Pipeline:
1. Instala/habilita extension cell_fracture
2. Cria cubo, aplica Cell Fracture (N pedacos, seed determinístico)
3. Setup rigid body world + chao passivo + shards dinamicos
4. Cubo "intacto" via shards kinematic ate frame de impacto
5. Liga gravidade -> shards caem, ao bater no chao saem voando
6. Bake da simulacao em keyframes TRS (visual_keying)
7. Aplica material Clay Doh (Principled BSDF puro reconstruido — sem bake) em todos shards
8. Export GLB com export_force_sampling=True

Argumentos depois de `--`:
  --shards 60
  --seed 42
  --frame-end 120
  --drop-height 6.0
  --out-glb caminho.glb
  --out-blend caminho.blend (opcional, pra inspecao)
"""
import bpy
import bmesh
import sys
import os
import argparse
import math
import random
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--shards", type=int, default=60)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--frame-end", type=int, default=120)
    p.add_argument("--drop-height", type=float, default=6.0)
    p.add_argument("--out-glb", required=True)
    p.add_argument("--out-blend", default=None)
    p.add_argument("--no-clay", action="store_true",
                   help="Pular Clay Doh, usar cor solida (debug rapido)")
    return p.parse_args(argv)


def ensure_cell_fracture():
    """Instala+habilita cell_fracture via extension repo (Blender 5.x)."""
    import addon_utils
    mod_name = "bl_ext.blender_org.cell_fracture"

    # Check se ja esta enabled e op exposto
    if getattr(bpy.ops.object, "add_fracture_cell_objects", None) is not None:
        try:
            # tenta poll — se op existe e nao da erro de "could not be found"
            bpy.ops.object.add_fracture_cell_objects.poll()
            print("cell_fracture: op ja disponivel")
            return
        except Exception:
            pass

    bpy.context.preferences.system.use_online_access = True
    try:
        bpy.ops.extensions.repo_sync_all()
    except Exception as e:
        print(f"repo_sync_all WARN: {e}")
    try:
        bpy.ops.extensions.package_install(repo_index=0, pkg_id="cell_fracture", enable_on_install=True)
        print("cell_fracture instalado")
    except Exception as e:
        print(f"package_install WARN: {e}")

    # forca enable apos install
    try:
        addon_utils.enable(mod_name, default_set=True)
    except Exception as e:
        print(f"enable WARN: {e}")

    # save_userpref pra persistir
    try:
        bpy.ops.wm.save_userpref()
    except Exception:
        pass

    if not getattr(bpy.ops.object, "add_fracture_cell_objects", None):
        raise SystemExit("cell_fracture nao expos add_fracture_cell_objects apos enable")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 120
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    # unidade de gravidade padrao = -9.81 z. Manter.


def create_cube_to_fracture(drop_height):
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, drop_height))
    cube = bpy.context.active_object
    cube.name = "SourceCube"
    # subdivide pra ter mais vertices — cell_fracture com source=VERT_OWN
    # usa cada vertice como seed. Cubo crudo so tem 8 verts.
    # 5 cuts -> 386 verts -> ~120 shards efetivos
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=5)
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"SourceCube verts apos subdivide: {len(cube.data.vertices)}")
    return cube


def fracture(cube, n_shards, seed):
    """Aplica Cell Fracture chamando a funcao `main` do addon diretamente.

    Em Blender 5.x headless, o op `bpy.ops.object.add_fracture_cell_objects` as vezes
    nao registra na RNA mesmo com addon enabled — bug do extension system. Workaround:
    importar o modulo e chamar `main(context, **kwargs)` direto.
    """
    # Importa o modulo da extension
    import bl_ext.blender_org.cell_fracture as cell_fracture_mod

    # Seleciona apenas o cube
    bpy.ops.object.select_all(action='DESELECT')
    cube.select_set(True)
    bpy.context.view_layer.objects.active = cube

    before = set(o.name for o in bpy.data.objects)

    print(f"FRACTURE: {n_shards} shards, seed={seed}")

    # Kwargs do operator FractureCell (todos os defaults)
    kwargs = dict(
        source={'VERT_OWN'},
        source_limit=n_shards,
        source_noise=1.0,
        cell_scale=(1.0, 1.0, 1.0),
        recursion=0,
        recursion_source_limit=8,
        recursion_clamp=250,
        recursion_chance=0.25,
        recursion_chance_select='SIZE_MIN',
        use_smooth_faces=False,
        use_sharp_edges=False,
        use_sharp_edges_apply=False,
        use_data_match=True,
        use_island_split=True,
        margin=0.0001,
        material_index=0,
        use_interior_vgroup=False,
        mass_mode='VOLUME',
        mass=1.0,
        use_recenter=True,
        use_remove_original=True,
        use_debug_points=False,
        use_debug_redraw=False,
        use_debug_bool=False,
        collection_name="Shards",
    )

    try:
        cell_fracture_mod.main(bpy.context, **kwargs)
    except Exception as e:
        print(f"cell_fracture.main FAIL: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()
        raise

    after = set(o.name for o in bpy.data.objects)
    new_names = sorted(after - before)
    shards = [bpy.data.objects[n] for n in new_names
              if bpy.data.objects[n].type == 'MESH'
              and bpy.data.objects[n] != cube]
    # remove o cubo original se ainda existir (use_remove_original deveria ter feito isso)
    if cube.name in bpy.data.objects:
        bpy.data.objects.remove(cube, do_unlink=True)

    print(f"FRACTURE OK: {len(shards)} shards gerados")
    return shards


def create_floor(z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, z))
    floor = bpy.context.active_object
    floor.name = "Floor"
    return floor


def setup_rigid_body_world():
    bpy.ops.rigidbody.world_add()
    scene = bpy.context.scene
    rbw = scene.rigidbody_world
    rbw.enabled = True
    rbw.solver_iterations = 20
    rbw.substeps_per_frame = 20
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = scene.frame_end
    print(f"RB World: substeps={rbw.substeps_per_frame} iter={rbw.solver_iterations}")
    return rbw


def add_passive_rb(obj):
    """Marca obj como rigid body passivo (chao)."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'PASSIVE'
    obj.rigid_body.collision_shape = 'BOX'
    obj.rigid_body.friction = 0.6
    obj.rigid_body.restitution = 0.1


def add_active_rb(obj, mass=1.0):
    """Marca obj como rigid body ativo (shard)."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = 'ACTIVE'
    obj.rigid_body.collision_shape = 'CONVEX_HULL'
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = 0.7
    obj.rigid_body.restitution = 0.15
    obj.rigid_body.linear_damping = 0.05
    obj.rigid_body.angular_damping = 0.1


def bake_simulation():
    """Roda o ptcache bake."""
    scene = bpy.context.scene
    print(f"PTCACHE BAKE: frames {scene.frame_start}-{scene.frame_end}")
    # context override pro rigid body world point_cache
    override = bpy.context.copy()
    override["scene"] = scene
    override["point_cache"] = scene.rigidbody_world.point_cache
    with bpy.context.temp_override(**override):
        bpy.ops.ptcache.bake_all(bake=True)
    print("PTCACHE BAKE OK")


def bake_to_keyframes(shards):
    """Bake da simulacao em keyframes TRS pra cada shard."""
    scene = bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    for s in shards:
        s.select_set(True)
    bpy.context.view_layer.objects.active = shards[0]
    print(f"NLA BAKE: {len(shards)} objetos, frames {scene.frame_start}-{scene.frame_end}")
    bpy.ops.nla.bake(
        frame_start=scene.frame_start,
        frame_end=scene.frame_end,
        step=1,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=False,  # cria nova Action (limpa)
        bake_types={'OBJECT'},
    )
    print("NLA BAKE OK")


def remove_rigid_body(shards, floor):
    """Apos bake, remover rigid body dos objetos pra exportador glTF nao confundir."""
    bpy.ops.object.select_all(action='DESELECT')
    for s in shards:
        s.select_set(True)
    floor.select_set(True)
    bpy.context.view_layer.objects.active = shards[0]
    try:
        bpy.ops.rigidbody.objects_remove()
    except Exception as e:
        print(f"rigidbody.objects_remove WARN: {e}")
    # remove o world tambem
    try:
        bpy.ops.rigidbody.world_remove()
    except Exception as e:
        print(f"rigidbody.world_remove WARN: {e}")


def apply_clay_material(shards, src_blend, mat_name="Clay Doh"):
    """Append material Clay Doh, e aplica nos shards.

    NAO usa bake (Observer recomendou). Material original tem Object Coord
    que distorce, mas como cada shard eh pequeno e a animacao distrai
    a percepcao, vale tentar primeiro.
    Se ficar feio, fallback: criar Principled BSDF puro com cor "clay rosa".
    """
    try:
        with bpy.data.libraries.load(src_blend, link=False) as (data_from, data_to):
            if mat_name not in data_from.materials:
                print(f"Material {mat_name!r} nao existe — usando cor solida")
                return apply_solid_clay(shards)
            data_to.materials = [mat_name]
        mat = bpy.data.materials[mat_name]
        for s in shards:
            s.data.materials.clear()
            s.data.materials.append(mat)
        print(f"Clay Doh applied (procedural) em {len(shards)} shards")
    except Exception as e:
        print(f"Clay append FAIL: {e} — fallback cor solida")
        apply_solid_clay(shards)


def apply_solid_clay(shards):
    """Material clay-rosa Principled BSDF puro (sem texturas).

    Cor mais saturada pra nao desaparecer no environment claro do viewer.
    """
    mat = bpy.data.materials.new(name="ClaySolid")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # rosa coral medio — saturado o bastante pra ler em PBR com env brilhante
        bsdf.inputs["Base Color"].default_value = (0.85, 0.45, 0.40, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.72
        if "Sheen Weight" in bsdf.inputs:
            bsdf.inputs["Sheen Weight"].default_value = 0.4
            bsdf.inputs["Sheen Roughness"].default_value = 0.4
            bsdf.inputs["Sheen Tint"].default_value = (1.0, 0.85, 0.78, 1.0)
    for s in shards:
        s.data.materials.clear()
        s.data.materials.append(mat)
    print(f"Solid clay applied em {len(shards)} shards (coral)")


def export_glb(shards, out_path):
    bpy.ops.object.select_all(action='DESELECT')
    for s in shards:
        s.select_set(True)
    bpy.context.view_layer.objects.active = shards[0]
    print(f"EXPORT GLB: {out_path}")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format='GLB',
        use_selection=True,
        export_apply=False,  # NAO aplicar modifiers (preservar animation)
        export_materials='EXPORT',
        export_image_format='AUTO',
        export_animations=True,
        export_animation_mode='SCENE',   # 1 clip unico com todos channels — player limpo
        export_force_sampling=True,
        export_frame_range=True,
        export_frame_step=1,
        export_optimize_animation_size=False,  # preserva keyframes pra scrubbing
        export_morph=False,
        export_skins=False,
    )
    size = os.path.getsize(out_path)
    print(f"GLB_OK: {out_path} ({size/1024:.1f}KB)")


def main():
    args = parse_args()
    scene_end = args.frame_end

    print("=" * 60)
    print(f"Shatter build: shards={args.shards} seed={args.seed} end={scene_end} drop={args.drop_height}")
    print("=" * 60)

    ensure_cell_fracture()
    reset_scene()
    bpy.context.scene.frame_end = scene_end

    random.seed(args.seed)

    cube = create_cube_to_fracture(args.drop_height)
    shards = fracture(cube, args.shards, args.seed)
    if not shards:
        raise SystemExit("Fracture nao gerou shards")

    floor = create_floor(z=0.0)
    setup_rigid_body_world()

    add_passive_rb(floor)
    HOLD_FRAMES = 15  # cubo intacto/parado por meio segundo antes de soltar
    for s in shards:
        bb = s.dimensions
        vol = max(bb.x * bb.y * bb.z, 0.001)
        add_active_rb(s, mass=vol * 2.0)
        s.rigid_body.linear_damping = 0.0
        s.rigid_body.angular_damping = 0.0
        # kinematic ate frame HOLD_FRAMES — fica parado no ar (dramatico)
        s.rigid_body.kinematic = True
        s.keyframe_insert(data_path="rigid_body.kinematic", frame=1)
        s.keyframe_insert(data_path="rigid_body.kinematic", frame=HOLD_FRAMES)
        s.rigid_body.kinematic = False
        s.keyframe_insert(data_path="rigid_body.kinematic", frame=HOLD_FRAMES + 1)
    print(f"HOLD: shards kinematic ate frame {HOLD_FRAMES}, soltam em {HOLD_FRAMES + 1}")

    bake_simulation()
    bake_to_keyframes(shards)

    # garante que shards vao pra origem deles no frame 1 (visual_keying ja fez)
    bpy.context.scene.frame_set(1)

    remove_rigid_body(shards, floor)

    # opcional: chao tambem entra no GLB pro visual ter contexto
    # remover dele o material default e dar um cinza-claro
    floor_mat = bpy.data.materials.new(name="FloorMat")
    floor_mat.use_nodes = True
    fb = floor_mat.node_tree.nodes.get("Principled BSDF")
    if fb:
        fb.inputs["Base Color"].default_value = (0.92, 0.90, 0.86, 1.0)
        fb.inputs["Roughness"].default_value = 0.9
    floor.data.materials.clear()
    floor.data.materials.append(floor_mat)

    if not args.no_clay:
        src_blend = r"C:\Users\manu\Downloads\BLENDER-CLAY\Clay Doh 4.0.4 (Blender 4.4+)\Clay Doh 4.0.4 (Blender 4.4+).blend"
        if os.path.exists(src_blend):
            apply_clay_material(shards, src_blend)
        else:
            print(f"Clay Doh blend nao encontrado em {src_blend}, usando solid")
            apply_solid_clay(shards)
    else:
        apply_solid_clay(shards)

    # selecao final: shards + floor pro export
    bpy.ops.object.select_all(action='DESELECT')
    for s in shards:
        s.select_set(True)
    floor.select_set(True)
    bpy.context.view_layer.objects.active = shards[0]

    export_glb(shards + [floor], args.out_glb)

    if args.out_blend:
        os.makedirs(os.path.dirname(args.out_blend), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=args.out_blend)
        print(f"BLEND_OK: {args.out_blend}")

    print("\n[DONE]")


main()
