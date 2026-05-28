"""Inspeciona os node groups GeoNodeWall e GeoNodeCage do Home Builder 5.
Cria uma parede e um cage e lista todos os inputs reais (nome + tipo + default),
alem dos props default da cena (wall_thickness, ceiling_height, door_*, window_*).
"""
import bpy
import importlib

M = "bl_ext.blender_org.home_builder_5"
hb_types = importlib.import_module(f"{M}.hb_types")


def dump_inputs(geo_obj, label):
    mod = geo_obj.obj.modifiers[geo_obj.obj.home_builder.mod_name]
    ng = mod.node_group
    print(f"\n=== INPUTS de {label} (node_group={ng.name}) ===")
    for item in ng.interface.items_tree:
        if getattr(item, "in_out", None) == "INPUT" or getattr(item, "item_type", "") == "SOCKET":
            try:
                ident = item.identifier
                val = mod[ident] if ident in mod else "?"
                stype = getattr(item, "socket_type", "?")
                print(f"  - '{item.name}'  [{stype}]  = {val}")
            except Exception as e:
                print(f"  - '{item.name}'  (erro: {e})")


def main():
    print("\n##### PROPS DA CENA #####")
    props = bpy.context.scene.home_builder
    for attr in ["wall_thickness", "ceiling_height", "door_single_width",
                 "door_height", "window_width", "window_height",
                 "window_height_from_floor"]:
        try:
            print(f"  scene.home_builder.{attr} = {getattr(props, attr)}")
        except Exception as e:
            print(f"  scene.home_builder.{attr} -> {e}")

    wall = hb_types.GeoNodeWall()
    wall.create("InspectWall")
    dump_inputs(wall, "GeoNodeWall")

    cage = hb_types.GeoNodeCage()
    cage.create("InspectCage")
    dump_inputs(cage, "GeoNodeCage")


if __name__ == "__main__":
    main()
