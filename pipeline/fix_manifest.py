import json
p = r'C:\Users\manu\ved\blender-experiments-2026\out\manifest.json'
m = json.load(open(p))
for it in m:
    for k in ('glb', 'render'):
        v = it[k]
        v = v.replace('\\', '/')
        if 'blender-experiments-2026/' in v:
            v = v.split('blender-experiments-2026/', 1)[-1]
        it[k] = v
json.dump(m, open(p, 'w'), indent=2)
print(m[0])
print('total:', len(m))
