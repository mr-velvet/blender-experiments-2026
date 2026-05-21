"""Inspeciona um GLB e imprime info de mesh/skin/anim."""
import json
import struct
import sys
from pathlib import Path


def parse_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67, "not a GLB"
    # Chunk 0 = JSON
    json_len, json_type = struct.unpack("<II", data[12:20])
    json_str = data[20:20 + json_len].rstrip(b"\x00").decode("utf-8")
    return json.loads(json_str)


def main(path):
    g = parse_glb(path)
    print(f"\n== {Path(path).name} ==")
    print(f"meshes: {len(g.get('meshes', []))}")
    print(f"nodes: {len(g.get('nodes', []))}")
    print(f"skins: {len(g.get('skins', []))}")
    for i, s in enumerate(g.get("skins", [])):
        joints = s.get("joints", [])
        print(f"  skin[{i}]: joints={len(joints)} {joints}")
    print(f"animations: {len(g.get('animations', []))}")
    for i, a in enumerate(g.get("animations", [])):
        chans = a.get("channels", [])
        samplers = a.get("samplers", [])
        print(f"  anim[{i}]: name={a.get('name')} channels={len(chans)} samplers={len(samplers)}")
        for c in chans:
            t = c.get("target", {})
            print(f"    -> node={t.get('node')} path={t.get('path')}")
    print(f"materials: {len(g.get('materials', []))}")
    for m in g.get("materials", []):
        print(f"  {m.get('name')}: {list(m.get('pbrMetallicRoughness', {}).keys())}")


if __name__ == "__main__":
    main(sys.argv[1])
