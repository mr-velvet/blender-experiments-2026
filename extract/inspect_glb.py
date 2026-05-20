"""Le um GLB e imprime bb + node positions."""
import sys, struct, json
from pathlib import Path

src = sys.argv[1]
with open(src, "rb") as f:
    data = f.read()

assert data[:4] == b"glTF"
version, length = struct.unpack_from("<II", data, 4)
json_len, json_type = struct.unpack_from("<II", data, 12)
assert json_type == 0x4E4F534A  # JSON
gltf = json.loads(data[20:20+json_len].decode("utf-8"))

bin_offset = 20 + json_len
bin_len, bin_type = struct.unpack_from("<II", data, bin_offset)
assert bin_type == 0x004E4942  # BIN
bin_data = data[bin_offset+8:bin_offset+8+bin_len]

print(f"file: {src}")
print(f"  nodes: {len(gltf.get('nodes', []))}")
print(f"  meshes: {len(gltf.get('meshes', []))}")
print(f"  scene roots: {gltf['scenes'][0].get('nodes', [])}")

for i, n in enumerate(gltf.get("nodes", [])):
    t = n.get("translation", [0,0,0])
    print(f"  node[{i}] name={n.get('name','?')} translation={t} mesh={n.get('mesh')}")

# bb global from positions
for i, m in enumerate(gltf.get("meshes", [])[:5]):
    for pi, p in enumerate(m.get("primitives", [])[:1]):
        pos_acc_idx = p["attributes"]["POSITION"]
        acc = gltf["accessors"][pos_acc_idx]
        mn = acc.get("min"); mx = acc.get("max")
        print(f"  mesh[{i}] prim[{pi}] pos.min={mn} pos.max={mx}")
