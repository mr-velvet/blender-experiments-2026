"""Inspeciona GLB: lista nodes, animations, channels, duration."""
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
        # primeiro chunk = JSON
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
    for i, n in enumerate(j.get('nodes', [])[:15]):
        print(f"  [{i}] {n.get('name', '?')}  mesh={n.get('mesh', '-')}")
    if len(j.get('nodes', [])) > 15:
        print(f"  ... +{len(j['nodes']) - 15} more")
    print(f"")
    print(f"MESHES: {len(j.get('meshes', []))}")
    print(f"MATERIALS: {len(j.get('materials', []))}")
    print(f"")
    anims = j.get('animations', [])
    print(f"ANIMATIONS: {len(anims)}")
    for i, a in enumerate(anims):
        ch = a.get('channels', [])
        samp = a.get('samplers', [])
        print(f"  [{i}] name={a.get('name')!r} channels={len(ch)} samplers={len(samp)}")
        # duracao = ultimo input value do primeiro sampler
        if samp:
            acc_idx = samp[0].get('input')
            if acc_idx is not None:
                acc = j['accessors'][acc_idx]
                print(f"       sampler[0].input: count={acc.get('count')} min={acc.get('min')} max={acc.get('max')}")
        # tipos de paths
        paths = {}
        for c in ch:
            p = c.get('target', {}).get('path', '?')
            paths[p] = paths.get(p, 0) + 1
        print(f"       paths: {paths}")

if __name__ == "__main__":
    main()
