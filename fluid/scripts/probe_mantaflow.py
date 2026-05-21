"""Sonda: Mantaflow funciona em Blender 5.1 headless? Quais APIs existem?"""
import bpy

print("=" * 60)
print("BLENDER:", bpy.app.version_string)
print("=" * 60)

# Limpar cena
bpy.ops.wm.read_factory_settings(use_empty=True)

# Criar emissor (sphere)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.5, location=(0, 0, 2))
emitter = bpy.context.active_object
emitter.name = "Emitter"

# Criar domain (cube around)
bpy.ops.mesh.primitive_cube_add(size=4, location=(0, 0, 2))
domain = bpy.context.active_object
domain.name = "Domain"

# Tentar adicionar modifier FLUID no domain
print("\n[1] Adicionando FLUID modifier no domain...")
try:
    bpy.ops.object.modifier_add(type='FLUID')
    print(f"  OK. modifiers: {[m.name for m in domain.modifiers]}")

    fluid_mod = domain.modifiers["Fluid"]
    print(f"  fluid_type (default): {fluid_mod.fluid_type}")
    fluid_mod.fluid_type = 'DOMAIN'
    print(f"  fluid_type set: {fluid_mod.fluid_type}")

    # Configurar como liquid
    domain_settings = fluid_mod.domain_settings
    domain_settings.domain_type = 'LIQUID'
    print(f"  domain_type: {domain_settings.domain_type}")
    print(f"  resolution_max: {domain_settings.resolution_max}")
    print(f"  use_mesh: {domain_settings.use_mesh}")
except Exception as e:
    print(f"  ERR: {type(e).__name__}: {e}")

# Configurar emitter como FLOW
print("\n[2] Adicionando FLUID modifier no emitter (FLOW)...")
bpy.context.view_layer.objects.active = emitter
try:
    bpy.ops.object.modifier_add(type='FLUID')
    emitter_mod = emitter.modifiers["Fluid"]
    emitter_mod.fluid_type = 'FLOW'
    print(f"  fluid_type: {emitter_mod.fluid_type}")
    flow_settings = emitter_mod.flow_settings
    flow_settings.flow_type = 'LIQUID'
    flow_settings.flow_behavior = 'GEOMETRY'  # solido virando liquido
    print(f"  flow_type: {flow_settings.flow_type}")
    print(f"  flow_behavior: {flow_settings.flow_behavior}")
except Exception as e:
    print(f"  ERR: {type(e).__name__}: {e}")

# Tentar bake
print("\n[3] Tentando bake_all...")
bpy.context.view_layer.objects.active = domain
try:
    # bake operator requer domain active
    print("  vou tentar bake (frames=10) — pode demorar")
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 10
    # Reduzir resolucao pra teste rapido
    fluid_mod = domain.modifiers["Fluid"]
    fluid_mod.domain_settings.resolution_max = 32
    fluid_mod.domain_settings.cache_frame_start = 1
    fluid_mod.domain_settings.cache_frame_end = 10
    fluid_mod.domain_settings.use_mesh = True

    # bake liquid (data)
    result = bpy.ops.fluid.bake_data()
    print(f"  bake_data: {result}")

    # bake mesh
    result = bpy.ops.fluid.bake_mesh()
    print(f"  bake_mesh: {result}")
except Exception as e:
    print(f"  ERR: {type(e).__name__}: {e}")

print("\n[DONE]")
