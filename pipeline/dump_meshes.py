"""Dump world-space vertices + triangles of every mesh in base.blend into npz files.
bones.npz   : skeleton meshes that are real bones/cartilage (no .i/.j markers, no attachment areas)
attach.npz  : attachment-area meshes (*.o*l/r, *.e*l/r) plus their parent bone in attach_meta.json
muscles.npz : every mesh from the muscle file, plus group chain in muscle_meta.json
"""
import sys, re, json, bpy, numpy as np

blend, outdir = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend)

ATT = re.compile(r'\.[oe]\d*[lr]$')
MARK = re.compile(r'\.(i|j)$')

def chain(o):
    out = []
    p = o.parent
    while p:
        out.append(p.name)
        p = p.parent
    return out

def arrays(o):
    me = o.data
    me.calc_loop_triangles()
    mw = np.array(o.matrix_world)
    v = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get('co', v)
    v = v.reshape(-1, 3)
    v = v @ mw[:3, :3].T + mw[:3, 3]
    t = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get('vertices', t)
    return v.astype(np.float32), t.reshape(-1, 3)

bones, att, mus = {}, {}, {}
att_meta, mus_meta, bone_meta = {}, {}, {}
for o in bpy.data.objects:
    if o.type != 'MESH' or len(o.data.vertices) == 0:
        continue
    src = o.get('_src')
    name = o.name
    if src == 'skel':
        if MARK.search(name) or name.startswith('Cross Section'):
            continue
        v, t = arrays(o)
        if ATT.search(name):
            att[name + '|v'], att[name + '|t'] = v, t
            att_meta[name] = dict(bone=o.parent.name if o.parent else None)
        else:
            bones[name + '|v'], bones[name + '|t'] = v, t
            bone_meta[name] = dict(chain=chain(o))
    elif src == 'mus':
        v, t = arrays(o)
        mus[name + '|v'], mus[name + '|t'] = v, t
        mus_meta[name] = dict(chain=chain(o))

np.savez_compressed(f'{outdir}/bones.npz', **bones)
np.savez_compressed(f'{outdir}/attach.npz', **att)
np.savez_compressed(f'{outdir}/muscles.npz', **mus)
json.dump(dict(bones=bone_meta, attach=att_meta, muscles=mus_meta),
          open(f'{outdir}/meta.json', 'w'), indent=0)
print('DUMPED', len(bone_meta), len(att_meta), len(mus_meta))
