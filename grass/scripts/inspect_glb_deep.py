"""Inspecao mais profunda — checa attributes do mesh (COLOR_0?), bbox, etc."""
import json
import struct
import sys
from pathlib import Path


def parse_glb(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, length = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67, "not a GLB"
    json_len, json_type = struct.unpack("<II", data[12:20])
    json_str = data[20:20 + json_len].rstrip(b"\x00").decode("utf-8")
    return json.loads(json_str)


def main(path):
    g = parse_glb(path)
    print(f"\n== {Path(path).name} ==")
    print(json.dumps(g, indent=2)[:4000])


if __name__ == "__main__":
    main(sys.argv[1])
