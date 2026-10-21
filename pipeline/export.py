"""Export viewer assets:
  overview.glb      whole skeleton in 3 merged meshes (context / right arm / right leg), simplified later
  region_<r>.glb    region bones (one node per bone under its segment node) + skinned muscles
  model.json        rig, muscle metadata (anchors for length), Chinese names, source/licence info
"""
import json, re, os, numpy as np
from lib import load, meta, W
from gltfw import GLB
from bind import vertex_normals
from names import bone_zh, GROUPS

OUT = os.path.join(W, '..', 'raw')
os.makedirs(OUT, exist_ok=True)
B = load('bones')
MD = meta()
rig = json.load(open(f'{W}/rig.json'))

SKIP = re.compile(r'tooth|incisor|canine|premolar|molar|Malleus|Incus|Stapes|cells of ethmoid|Sinus of|Nasal septal|alar cartilage|'
                  r'process of nasal|Arytenoid|Corniculate|Cricoid|Thyroid cartilage|Vomer|Ethmoid|concha|Palatine|Lacrimal', re.I)

def region_set(r):
    return {b for s in rig['regions'][r]['segments'].values() for b in s['bones']}

ARM, LEG = region_set('arm'), region_set('leg')

def merged(names):
    vs, ts, ns, off = [], [], [], 0
    for n in names:
        v = B[n]['v'].astype(np.float32); t = B[n]['t']
        vs.append(v); ts.append(t + off); ns.append(vertex_normals(v.astype(np.float64), t)); off += len(v)
    return np.vstack(vs), np.vstack(ts), np.vstack(ns)

# ---------------- overview ----------------
g = GLB()
keep = [n for n in B if not SKIP.search(n)]
for label, names in [('context', [n for n in keep if n not in ARM and n not in LEG]),
                     ('arm', [n for n in keep if n in ARM]), ('leg', [n for n in keep if n in LEG])]:
    v, t, nrm = merged(names)
    g.node(label, mesh=g.mesh(label, v, t, nrm), extras=dict(part=label))
    print('overview', label, len(names), 'bones', len(t), 'tris')
g.save(f'{OUT}/overview.glb')

# ---------------- regions ----------------
model = dict(rig=rig, regions={})
for r in ['arm', 'leg']:
    bj = json.load(open(f'{W}/bind_{r}.json'))
    z = np.load(f'{W}/bind_{r}.npz')
    segs = bj['segments']
    g = GLB()
    seg_node = {s: g.node('seg:' + s, extras=dict(seg=s)) for s in segs}
    bones_meta = {}
    tris = 0
    for s, d in rig['regions'][r]['segments'].items():
        for bname in d['bones']:
            v = B[bname]['v'].astype(np.float32); t = B[bname]['t']
            g.node('bone:' + bname, parent=seg_node[s], mesh=g.mesh(bname, v, t, vertex_normals(v.astype(np.float64), t)), extras=dict(bone=bname))
            bones_meta[bname] = dict(seg=s, zh=bone_zh(bname))
            tris += len(t)
    skin = g.skin([seg_node[s] for s in segs])
    mus_meta = {}
    for n, d in bj['muscles'].items():
        v, t, nrm, j, w = (z[f'{n}|{k}'] for k in ('v', 't', 'n', 'j', 'w'))
        g.node('muscle:' + n, mesh=g.mesh(n, v, t, nrm, j, w), skin=skin, extras=dict(muscle=n))
        tris += len(t)
        mus_meta[n] = {k: d[k] for k in ('name', 'zh', 'group', 'kind', 'renamed', 'source_name', 'anchors', 'why', 'wrap', 'chain')}
    g.save(f'{OUT}/region_{r}.glb')
    groups = [dict(id=gid, label=lab) for gid, lab, _ in GROUPS[r]]
    # landmarks the viewer keeps in frame while the limb moves
    Jr = rig['regions'][r]['joints']
    cen = lambda b: B[b]['v'].astype(np.float64).mean(0).tolist()
    if r == 'arm':
        lms = [('clavicle', Jr['clavicle']['pivot']), ('humerus', Jr['humerus']['pivot']), ('ulna', Jr['ulna']['pivot']),
               ('hand', Jr['hand']['pivot']), ('hand', cen('Distal phalanx of third finger of hand.r')),
               ('hand', cen('Distal phalanx of first finger of hand.r'))]
    else:
        heel = B['Calcaneus.r']['v'].astype(np.float64); heel = heel[np.argmax(heel[:, 1])].tolist()
        hipbone = B['Hip bone.r']['v'].astype(np.float64)
        crest = hipbone[np.argmax(hipbone[:, 2])].tolist()      # iliac crest: the gluteal and iliacus muscles reach up to it
        lms = [('femur', Jr['femur']['pivot']), ('tibia', Jr['tibia']['pivot']), ('talus', Jr['talus']['pivot']),
               ('foot', heel), ('toes', cen('Distal phalanx of second finger of foot.r')), ('trunk', cen('Hip bone.r')),
               ('trunk', crest)]
    landmarks = [dict(seg=sg, p=[round(float(x), 5) for x in pt]) for sg, pt in lms]
    model['regions'][r] = dict(segments=segs, bones=bones_meta, muscles=mus_meta, groups=groups, landmarks=landmarks)
    print('region', r, 'tris', tris, 'muscles', len(mus_meta))

from gait import gait_table
model['regions']['leg']['gait'] = gait_table(rig)

model['source'] = dict(
    model='Z-Anatomy (github.com/LluisV/Z-Anatomy), based on BodyParts3D (DBCLS)',
    licence='CC BY-SA 4.0',
    notes=['Upper/lower trapezius names are swapped in the source model; corrected here by position.',
           'Muscle length is measured along a path of anchor points (attachments + joint pulleys), not along the deformed mesh.',
           'Scapula follows a fixed scapulohumeral rhythm (about 1/3 of arm elevation); real rhythm varies by person and plane.'])
json.dump(model, open(f'{OUT}/model.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('model.json', os.path.getsize(f'{OUT}/model.json') // 1024, 'KB')
