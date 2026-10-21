"""Import skeleton + muscle FBX once, save a .blend, and dump a JSON catalog of every object.
usage: python3 import_fbx.py <Skeletal.fbx> <Muscular.fbx> <out.blend> <out_catalog.json>   (needs bpy)"""
import sys, json, bpy
from mathutils import Vector

skel, mus, out_blend, out_json = sys.argv[1:5]
bpy.ops.wm.read_factory_settings(use_empty=True)

def imp(path, tag):
    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=path)
    for o in bpy.data.objects:
        if o.name not in before:
            o['_src'] = tag

imp(skel, 'skel')
imp(mus, 'mus')

cat = []
for o in bpy.data.objects:
    rec = dict(name=o.name, type=o.type, src=o.get('_src'),
               parent=o.parent.name if o.parent else None,
               collections=[c.name for c in o.users_collection])
    if o.type == 'MESH' and len(o.data.vertices):
        mw = o.matrix_world
        pts = [mw @ v.co for v in o.data.vertices]
        lo = [min(p[i] for p in pts) for i in range(3)]
        hi = [max(p[i] for p in pts) for i in range(3)]
        c = sum(pts, Vector()) / len(pts)
        rec.update(nv=len(pts), nf=len(o.data.polygons), lo=lo, hi=hi, c=list(c))
    cat.append(rec)

json.dump(cat, open(out_json, 'w'))
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("CATALOG", len(cat))
