"""Export viewer assets:
  overview.glb      whole skeleton in 4 merged meshes (context / right arm / right leg / left leg), simplified later
  region_<r>.glb    region bones (one node per bone under its segment node) + skinned muscles
  region_leg_l.glb  the right leg mirrored to the left (x -> -x), driven by the same rig for two-legged walking
  model.json        rig, muscle metadata (anchors for length), Chinese names, source/licence info
"""
import json, re, os, numpy as np
from lib import load, meta, W
from gltfw import GLB
from bind import vertex_normals
from names import bone_zh, GROUPS
from scipy.spatial import cKDTree

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
LEG_L = {b[:-2] + '.l' for b in LEG}
MIRROR = np.array([-1.0, 1.0, 1.0], np.float32)     # the body's midline is the plane x = 0

# The left leg is drawn as the right leg mirrored, so it reuses the verified rig and muscle paths.
# That is only right if the source model is itself symmetric: check every leg bone and muscle.
def _mirror_gap(D, names):
    worst = 0.0
    for n in names:
        vr = D[n]['v'].astype(np.float64) * MIRROR
        vl = D[n[:-2] + '.l']['v'].astype(np.float64)
        worst = max(worst, cKDTree(vl).query(vr)[0].max())
    return worst
_gap = max(_mirror_gap(B, LEG), _mirror_gap(load('muscles'), json.load(open(f'{W}/bind_leg.json'))['muscles']))
assert _gap < 1e-4, f'source model is not left/right symmetric (max {_gap*1000:.3f} mm); mirroring the right leg would misplace the left'
print(f'left leg = mirrored right leg: max vertex gap {_gap*1000:.4f} mm')

def merged(names):
    vs, ts, ns, off = [], [], [], 0
    for n in names:
        v = B[n]['v'].astype(np.float32); t = B[n]['t']
        vs.append(v); ts.append(t + off); ns.append(vertex_normals(v.astype(np.float64), t)); off += len(v)
    return np.vstack(vs), np.vstack(ts), np.vstack(ns)

# ---------------- overview ----------------
g = GLB()
keep = [n for n in B if not SKIP.search(n)]
for label, names in [('context', [n for n in keep if n not in ARM and n not in LEG and n not in LEG_L]),
                     ('arm', [n for n in keep if n in ARM]), ('leg', [n for n in keep if n in LEG]),
                     ('leg_l', [n for n in keep if n in LEG_L])]:
    v, t, nrm = merged(names)
    g.node(label, mesh=g.mesh(label, v, t, nrm), extras=dict(part=label))
    print('overview', label, len(names), 'bones', len(t), 'tris')
g.save(f'{OUT}/overview.glb')

# ---------------- regions ----------------
model = dict(rig=rig, regions={})
def write_region(r, bj, z, path, mirror=False):
    """Bones under their segment nodes + skinned muscles. mirror=True writes the left-side copy:
    positions and normals mirrored in x, triangle winding reversed so faces still point outwards.
    Node extras keep the right-side names, which index model.json."""
    S = MIRROR if mirror else np.ones(3, np.float32)
    flip = (lambda t: t[:, [0, 2, 1]]) if mirror else (lambda t: t)
    segs = bj['segments']
    g = GLB()
    seg_node = {s: g.node('seg:' + s, extras=dict(seg=s)) for s in segs}
    tris = 0
    for s, d in rig['regions'][r]['segments'].items():
        for bname in d['bones']:
            v = B[bname]['v'].astype(np.float32) * S; t = flip(B[bname]['t'])
            g.node('bone:' + bname, parent=seg_node[s], mesh=g.mesh(bname, v, t, vertex_normals(v.astype(np.float64), t)), extras=dict(bone=bname))
            tris += len(t)
    skin = g.skin([seg_node[s] for s in segs])
    for n in bj['muscles']:
        v, t, nrm, j, w = (z[f'{n}|{k}'] for k in ('v', 't', 'n', 'j', 'w'))
        g.node('muscle:' + n, mesh=g.mesh(n, v * S, flip(t), nrm * S, j, w), skin=skin, extras=dict(muscle=n))
        tris += len(t)
    g.save(path)
    return tris

for r in ['arm', 'leg']:
    bj = json.load(open(f'{W}/bind_{r}.json'))
    z = np.load(f'{W}/bind_{r}.npz')
    segs = bj['segments']
    bones_meta = {b: dict(seg=s, zh=bone_zh(b)) for s, d in rig['regions'][r]['segments'].items() for b in d['bones']}
    mus_meta = {n: {k: d[k] for k in ('name', 'zh', 'group', 'kind', 'renamed', 'source_name', 'anchors', 'why', 'wrap', 'chain')}
                for n, d in bj['muscles'].items()}
    tris = write_region(r, bj, z, f'{OUT}/region_{r}.glb')
    if r == 'leg':
        write_region(r, bj, z, f'{OUT}/region_leg_l.glb', mirror=True)
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
# two-legged walking: the left leg is the right one mirrored in x = 0, half a cycle later
model['regions']['leg']['left'] = dict(file='region_leg_l', mirror_x=True, phase_offset=0.5)

model['source'] = dict(
    model='Z-Anatomy (github.com/LluisV/Z-Anatomy), based on BodyParts3D (DBCLS)',
    licence='CC BY-SA 4.0',
    notes=['Upper/lower trapezius names are swapped in the source model; corrected here by position.',
           'Muscle length is measured along a path of anchor points (attachments + joint pulleys), not along the deformed mesh.',
           'Scapula follows a fixed scapulohumeral rhythm (about 1/3 of arm elevation); real rhythm varies by person and plane.'])
json.dump(model, open(f'{OUT}/model.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('model.json', os.path.getsize(f'{OUT}/model.json') // 1024, 'KB')
