"""Inspeciona GLB: nodes, skins, animations, channels, duration."""
import json
import struct
import sys
from pathlib import Path

def read_glb(path):
    with open(path, "rb") as f:
        magic = f.read(4)
        if magic != b"glTF":
            raise SystemExit("not a GLB file")
        version, length = struct.unpack("<II", f.read(8))
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        if chunk_type != 0x4E4F534A:
            raise SystemExit("first chunk not JSON")
        json_data = json.loads(f.read(chunk_len).decode("utf-8"))
        return json_data, length

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        raise SystemExit("usage: inspect_glb.py <file.glb>")

    j, total = read_glb(path)
    sz_kb = Path(path).stat().st_size / 1024
    print(f"FILE: {path}")
    print(f"SIZE: {sz_kb:.1f}KB ({total} bytes)")
    print(f"")
    print(f"NODES: {len(j.get('nodes', []))}")
    print(f"MESHES: {len(j.get('meshes', []))}")
    print(f"MATERIALS: {len(j.get('materials', []))}")
    print(f"SKINS: {len(j.get('skins', []))}")
    for i, s in enumerate(j.get('skins', [])):
        joints = s.get('joints', [])
        print(f"  [{i}] name={s.get('name')!r} joints={len(joints)} skeleton={s.get('skeleton')}")
        # Listar primeiros bones
        for ji in joints[:10]:
            node = j['nodes'][ji] if ji < len(j['nodes']) else None
            print(f"     joint[{ji}] = {node.get('name') if node else '?'}")
        if len(joints) > 10:
            print(f"     ... +{len(joints) - 10} more joints")
    print(f"")
    anims = j.get('animations', [])
    print(f"ANIMATIONS: {len(anims)}")
    for i, a in enumerate(anims):
        ch = a.get('channels', [])
        samp = a.get('samplers', [])
        print(f"  [{i}] name={a.get('name')!r} channels={len(ch)} samplers={len(samp)}")
        if samp:
            acc_idx = samp[0].get('input')
            if acc_idx is not None:
                acc = j['accessors'][acc_idx]
                print(f"       sampler[0].input: count={acc.get('count')} min={acc.get('min')} max={acc.get('max')}")
        paths = {}
        for c in ch:
            p = c.get('target', {}).get('path', '?')
            paths[p] = paths.get(p, 0) + 1
        print(f"       paths: {paths}")

if __name__ == "__main__":
    main()
