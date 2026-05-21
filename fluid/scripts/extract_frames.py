"""Extrai mesh por frame e exporta CADA FRAME como GLB individual.
Reaproveita o cache do Mantaflow ja bakeado no .blend.
"""
import bpy
import sys
import json
from pathlib import Path

BLEND_PATH = Path(r"C:/Users/manu/ved/blender-experiments-2026/fluid/out/fluid_sim.blend")
OUT_DIR = Path(r"C:/Users/manu/ved/blender-experiments-2026/fluid/out/glb/frames")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST = OUT_DIR.parent / "manifest.json"

FRAMES_TOTAL = 80
VOXEL_REMESH = 0.13  # tamanho do voxel pro decimate (maior = mais leve)

print(f"[load] {BLEND_PATH}")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

scene = bpy.context.scene
domain = bpy.data.objects.get("Domain")
print(f"  domain: {domain}")

# Limpar objetos de tentativa anterior (liquid_frame_*)
to_remove = [o for o in bpy.data.objects if o.name.startswith("liquid_frame_") or o.name.startswith("_temp_") or o.name == "Liquid"]
for o in to_remove:
    bpy.data.objects.remove(o, do_unlink=True)
print(f"  cleaned up {len(to_remove)} prev objects")

# Material liquid
mat = bpy.data.materials.get("LiquidMat") or bpy.data.materials.new("LiquidMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.18, 0.58, 0.92, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.08
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.9
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 1.33
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = 0.0

manifest = {
    "frames": [],
    "fps": 30,
    "total_frames": FRAMES_TOTAL,
}

print(f"\n[extract] {FRAMES_TOTAL} frames...")
for f in range(1, FRAMES_TOTAL + 1):
    scene.frame_set(f)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    domain_eval = domain.evaluated_get(depsgraph)
    raw_mesh = bpy.data.meshes.new_from_object(domain_eval, depsgraph=depsgraph)

    raw_verts = len(raw_mesh.vertices)

    # Criar obj temporario pra fazer remesh
    temp = bpy.data.objects.new(f"_t_{f}", raw_mesh)
    bpy.context.collection.objects.link(temp)

    # Remesh voxel pra decimar mantendo silhueta
    rm = temp.modifiers.new("Remesh", 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = VOXEL_REMESH

    depsgraph = bpy.context.evaluated_depsgraph_get()
    temp_eval = temp.evaluated_get(depsgraph)
    final_mesh = bpy.data.meshes.new_from_object(temp_eval, depsgraph=depsgraph)
    final_verts = len(final_mesh.vertices)

    # Limpar temp + raw
    bpy.data.objects.remove(temp, do_unlink=True)
    bpy.data.meshes.remove(raw_mesh)

    # Pular frames vazios (volume zero)
    if final_verts < 50:
        bpy.data.meshes.remove(final_mesh)
        manifest["frames"].append({"frame": f, "file": None, "verts": 0, "skipped": True})
        if f % 10 == 0:
            print(f"  f{f}: skip (empty)")
        continue

    # Recriar obj final e shade smooth
    obj = bpy.data.objects.new(f"liquid_{f}", final_mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    # smooth shading
    for poly in obj.data.polygons:
        poly.use_smooth = True

    # OFFSET vertices em +1.5 em Z (Blender) -> agua sai no piso (z=0 viceversa y=0 three.js)
    # O domain estava em z=1.5 com escala 3.5; mesh extraida vem em local coords centradas
    # em z=0 do domain, mas world era em z=1.5. Re-aplicar offset pra world coords.
    OFFSET_Z = 1.5
    for v in obj.data.vertices:
        v.co.z += OFFSET_Z

    # Selecionar so esse obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Export
    frame_filename = f"f{f:04d}.glb"
    frame_path = OUT_DIR / frame_filename
    bpy.ops.export_scene.gltf(
        filepath=str(frame_path),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_animations=False,
    )
    sz = frame_path.stat().st_size

    manifest["frames"].append({
        "frame": f,
        "file": frame_filename,
        "verts": final_verts,
        "raw_verts": raw_verts,
        "size_bytes": sz,
        "skipped": False,
    })

    # Limpar do scene pra nao acumular
    bpy.data.objects.remove(obj, do_unlink=True)

    if f % 10 == 0 or f == 1:
        print(f"  f{f}: raw={raw_verts} -> remeshed={final_verts} -> GLB {sz/1024:.1f}KB")

# Salvar manifest
with open(MANIFEST, "w") as fp:
    json.dump(manifest, fp, indent=2)

# Stats
non_empty = [fm for fm in manifest["frames"] if not fm["skipped"]]
total_size = sum(fm["size_bytes"] for fm in non_empty) / 1024
print(f"\n[done] {len(non_empty)}/{FRAMES_TOTAL} frames exportados, total {total_size:.1f}KB")
print(f"  manifest: {MANIFEST}")
print(f"  frames: {OUT_DIR}")
