"""Pipeline completo de simulacao de fluido:

1. Cria cena: emissor (esfera), domain (cubo), chao (plane)
2. Configura Mantaflow liquid sim com gravidade
3. Baka data + mesh
4. Pra cada frame, extrai mesh do domain (mesh sequence)
5. Tenta unificar topologia via remesh (pra morph targets) OU exporta como
   shape keys/mesh sequence -> GLB
6. Salva GLB final + .blend

Trade-offs:
- Resolucao 64 = leve mas blocada
- Resolucao 128 = balanceada (default)
- Resolucao 256 = pesada
- Frames 60-90 = 2-3s a 30fps (suficiente pra ciclo splash)
"""
import bpy
import sys
import math
from pathlib import Path

# Config
RESOLUTION = 96       # voxels do domain (64 leve, 96 medio, 128 detalhado)
FRAMES_TOTAL = 80     # 2.67s a 30fps
FPS = 30
CACHE_DIR = "//cache/"  # relativo ao .blend
OUT_DIR = Path(__file__).resolve().parent.parent / "out" / "glb"
OUT_DIR.mkdir(parents=True, exist_ok=True)
BLEND_PATH = OUT_DIR.parent / "fluid_sim.blend"

print("=" * 60)
print(f"FLUID SIM: res={RESOLUTION} frames={FRAMES_TOTAL} fps={FPS}")
print("=" * 60)

# Reset cena
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = FRAMES_TOTAL
scene.render.fps = FPS

# Precisa salvar o .blend ANTES de baker (cache relativo)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
print(f"\n[init] blend saved: {BLEND_PATH.name}")

# ============================================================
# 1. EMISSOR (esfera no alto)
# ============================================================
print("\n[1] Criando emissor...")
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, location=(0, 0, 3.0), segments=24, ring_count=16)
emitter = bpy.context.active_object
emitter.name = "Emitter"
bpy.ops.object.shade_smooth()

# Modifier FLUID -> FLOW liquid
bpy.ops.object.modifier_add(type='FLUID')
em_mod = emitter.modifiers["Fluid"]
em_mod.fluid_type = 'FLOW'
em_mod.flow_settings.flow_type = 'LIQUID'
em_mod.flow_settings.flow_behavior = 'GEOMETRY'  # vira liquido (nao continua emitindo)
em_mod.flow_settings.use_initial_velocity = False
print(f"  emitter: {emitter.name} flow_type={em_mod.flow_settings.flow_type}")

# Esconder o emissor no render (so existe pra alimentar a sim)
emitter.hide_render = True

# ============================================================
# 2. DOMAIN (cubo invisivel)
# ============================================================
print("\n[2] Criando domain...")
# Maior dominio em XY (pra agua espalhar) e altura suficiente
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1.5))
domain = bpy.context.active_object
domain.scale = (5, 5, 3.5)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
domain.name = "Domain"
domain.display_type = 'WIRE'  # so wireframe pra debug
domain.hide_render = True

bpy.ops.object.modifier_add(type='FLUID')
dm_mod = domain.modifiers["Fluid"]
dm_mod.fluid_type = 'DOMAIN'
ds = dm_mod.domain_settings
ds.domain_type = 'LIQUID'
ds.resolution_max = RESOLUTION
ds.use_mesh = True  # gera mesh-surface por frame
ds.mesh_scale = 2   # detalhe da extracao
ds.use_diffusion = False  # surface tension
ds.viscosity_base = 1.0
ds.viscosity_exponent = 6
ds.gravity = (0, 0, -9.81)

# Cache
ds.cache_frame_start = 1
ds.cache_frame_end = FRAMES_TOTAL
ds.cache_type = 'MODULAR'
ds.cache_data_format = 'OPENVDB'
ds.cache_mesh_format = 'BOBJECT'

# Mais substeps pra evitar penetracao do effector
ds.timesteps_min = 2
ds.timesteps_max = 8
ds.cfl_condition = 2.0  # default 4.0; menor = mais substeps

print(f"  domain: {domain.name} res={ds.resolution_max} use_mesh={ds.use_mesh}")

# ============================================================
# 3. CHAO (effector) - cubo achatado com top em z=0
# ============================================================
print("\n[3] Criando chao (effector cubo achatado)...")
# cubo de tamanho 1 em z=-0.5 -> top fica em z=0
# Escala 10x10x1 -> 10x10x1 unidades
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.5))
floor = bpy.context.active_object
floor.name = "Floor"
floor.scale = (10, 10, 1.0)  # grande e plano, top em z=0
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

bpy.ops.object.modifier_add(type='FLUID')
fl_mod = floor.modifiers["Fluid"]
fl_mod.fluid_type = 'EFFECTOR'
fl_mod.effector_settings.effector_type = 'COLLISION'
fl_mod.effector_settings.use_plane_init = False
# Reforcar colisao
fl_mod.effector_settings.surface_distance = 0.1
floor.hide_render = True
print(f"  floor: {floor.name} (cube top em z=0)")

# Paredes laterais pra agua nao sair do dominio
print("[3b] Criando paredes laterais...")
def make_wall(name, location, scale):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    w = bpy.context.active_object
    w.name = name
    w.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.modifier_add(type='FLUID')
    m = w.modifiers["Fluid"]
    m.fluid_type = 'EFFECTOR'
    m.effector_settings.effector_type = 'COLLISION'
    w.hide_render = True
    return w

# Sem paredes - agua espalha livre no chao
print("  sem paredes - agua espalha livre")

# Salvar antes do bake (Mantaflow exige .blend salvo)
bpy.ops.wm.save_mainfile()

# ============================================================
# 4. BAKE
# ============================================================
print(f"\n[4] Bake data + mesh (res={RESOLUTION}, frames={FRAMES_TOTAL})...")
print("   isso pode demorar... aguarde")

# Domain precisa ser active pra baker
bpy.context.view_layer.objects.active = domain
bpy.ops.object.select_all(action='DESELECT')
domain.select_set(True)

import time
t0 = time.time()
result = bpy.ops.fluid.bake_data()
print(f"   bake_data: {result} ({time.time()-t0:.1f}s)")

t0 = time.time()
result = bpy.ops.fluid.bake_mesh()
print(f"   bake_mesh: {result} ({time.time()-t0:.1f}s)")

# Salvar com cache
bpy.ops.wm.save_mainfile()

# ============================================================
# 5. EXTRAIR MESH SEQUENCE
# ============================================================
print(f"\n[5] Extraindo mesh por frame...")

# A malha simulada vive no Domain. Pra cada frame, definimos a scene
# nesse frame, fazemos depsgraph evaluate, copiamos a mesh resultante.

import bmesh

# Vamos criar um objeto novo "Liquid" que vai conter a malha do frame ATUAL,
# e adicionar shape keys com a malha em cada frame.

# Primeiro: precisamos pegar a malha do domain frame 1 como base
scene.frame_set(1)
depsgraph = bpy.context.evaluated_depsgraph_get()
domain_eval = domain.evaluated_get(depsgraph)
mesh_data_frame1 = bpy.data.meshes.new_from_object(domain_eval, depsgraph=depsgraph)

# Vendo o que veio (deve ter os vertices do mesh-surface da sim)
print(f"   frame 1: verts={len(mesh_data_frame1.vertices)} tris={len(mesh_data_frame1.polygons)}")

# Criar objeto liquid
liquid = bpy.data.objects.new("Liquid", mesh_data_frame1)
bpy.context.collection.objects.link(liquid)

# Estrategia: pra cada frame, extrair mesh e armazenar como Shape Key
# PROBLEMA conhecido: mesh-surface do Mantaflow tem topologia VARIAVEL.
# Shape keys exigem mesma contagem de vertices.
#
# Solucao: forcar mesh constante via REMESH modifier voxel (vai gerar
# topologia identica pra cada frame que extrairmos antes de capturar)

# Vou fazer abordagem alternativa: extrair cada frame como objeto separado,
# depois unificar via remesh + transfer normals.

# Lista de meshes por frame
frame_meshes = []
print("   extraindo cada frame...")
for f in range(1, FRAMES_TOTAL + 1):
    scene.frame_set(f)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    domain_eval = domain.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(domain_eval, depsgraph=depsgraph)
    frame_meshes.append((f, mesh))
    if f % 10 == 0:
        print(f"     frame {f}: verts={len(mesh.vertices)}")

# Agora normalizar topologia: cada frame vai pra um Voxel remesh com mesmo voxel_size
# Isso garante mesma contagem de verts/tris.

print("\n[6] Normalizando topologia via remesh...")
TARGET_VOXEL_SIZE = 0.08  # menor = mais detalhe, mais peso

# Vamos criar 1 objeto temporario por frame, aplicar remesh, e extrair vertices
normalized_meshes = []
for f, raw_mesh in frame_meshes:
    # criar objeto temp
    temp = bpy.data.objects.new(f"_temp_{f}", raw_mesh)
    bpy.context.collection.objects.link(temp)

    # adicionar Remesh modifier voxel
    rm = temp.modifiers.new("Remesh", 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = TARGET_VOXEL_SIZE

    # aplicar evaluacao
    depsgraph = bpy.context.evaluated_depsgraph_get()
    temp_eval = temp.evaluated_get(depsgraph)
    normalized = bpy.data.meshes.new_from_object(temp_eval, depsgraph=depsgraph)
    normalized_meshes.append((f, normalized))

    # cleanup
    bpy.data.objects.remove(temp, do_unlink=True)
    bpy.data.meshes.remove(raw_mesh)

    if f % 10 == 0:
        print(f"     frame {f}: remeshed verts={len(normalized.vertices)}")

# Verificar consistencia de topologia
vert_counts = [len(m.vertices) for _, m in normalized_meshes]
print(f"\n   vert counts unicos: {set(vert_counts)}")
print(f"   min={min(vert_counts)} max={max(vert_counts)}")

# Mesmo com remesh voxel, topologia pode variar quando geometria entra/sai
# do volume. Estrategia: usar o frame COM MAIS VERTICES como base,
# e fazer shrinkwrap dos outros frames nele.

# Simplificacao pragmatica:
# Vamos exportar mesh sequence como uma serie de objetos separados,
# e o player JS vai chavear entre eles a cada frame.

print(f"\n[7] Criando objetos por frame na cena...")
# Remover liquid temp
if liquid.name in bpy.data.objects:
    bpy.data.objects.remove(liquid, do_unlink=True)

# Material para o liquido
liquid_mat = bpy.data.materials.new("LiquidMat")
liquid_mat.use_nodes = True
bsdf = liquid_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.15, 0.55, 0.85, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.08
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = 0.95
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 1.33

# Criar objetos
frame_objects = []
for f, mesh in normalized_meshes:
    mesh.name = f"liquid_frame_{f:04d}"
    obj = bpy.data.objects.new(f"liquid_frame_{f:04d}", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(liquid_mat)
    # Esconder todos exceto o atual
    obj.hide_viewport = (f != 1)
    obj.hide_render = (f != 1)
    frame_objects.append(obj)

print(f"   criados {len(frame_objects)} objetos")

# ============================================================
# 8. Animar SCALE per frame (glTF nao exporta hide_viewport)
# Cada objeto: scale=1 no seu frame, scale=0 em todos os outros
# Com interpolation CONSTANT, troca instantanea
# ============================================================
print(f"\n[8] Animando scale (visibility) por frame com CONSTANT interp...")

for i, obj in enumerate(frame_objects):
    target_frame = i + 1

    # Reset: visivel apenas no proprio frame
    obj.scale = (0, 0, 0)
    obj.keyframe_insert("scale", frame=1)
    obj.scale = (0, 0, 0)
    obj.keyframe_insert("scale", frame=FRAMES_TOTAL)

    # No frame proprio: scale 1
    obj.scale = (1, 1, 1)
    obj.keyframe_insert("scale", frame=target_frame)

    # Antes e depois: scale 0 (com interpolation CONSTANT garante troca instantanea)
    if target_frame > 1:
        obj.scale = (0, 0, 0)
        obj.keyframe_insert("scale", frame=target_frame - 1)
    if target_frame < FRAMES_TOTAL:
        obj.scale = (0, 0, 0)
        obj.keyframe_insert("scale", frame=target_frame + 1)

# Setar todas as fcurves de scale como CONSTANT (sem interpolacao)
# No Blender 5.x, fcurves estao em action.layers[].strips[].channelbag()
for obj in frame_objects:
    if obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for slot in action.slots:
                    cb = strip.channelbag(slot, ensure=False)
                    if cb:
                        for fc in cb.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = "CONSTANT"

scene.frame_set(1)

# ============================================================
# 9. EXPORT GLB
# ============================================================
print(f"\n[9] Exportando GLB...")

# Selecionar so os frame objects
bpy.ops.object.select_all(action='DESELECT')
for obj in frame_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = frame_objects[0]

glb_path = OUT_DIR / "fluid_sequence.glb"
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_force_sampling=True,
    export_frame_step=1,
    export_optimize_animation_size=False,
)
print(f"   exported: {glb_path.name} ({glb_path.stat().st_size / 1024:.1f}KB)")

# Salvar blend final
bpy.ops.wm.save_mainfile()
print(f"\n[DONE]")
print(f"   GLB: {glb_path}")
print(f"   blend: {BLEND_PATH}")
