"""Bind muscles to the rig.

For every muscle mesh we find which rig segments it attaches to, using two independent sources:
  1. contact: muscle vertices lying within CONTACT mm of a segment's bone surface
  2. attachment areas from the skeleton file (name-matched, incl. group aliases), accepted only if the
     area is physically close to this muscle mesh (names in this model are not always right)
The o/e (origin/insertion) labels of the attachment areas are ignored: several are reversed in the
model, and muscle length does not depend on which end is called origin.

Output per muscle: segments along the kinematic chain, anchor points (for length), and per-vertex
skin weights over the chain segments (for deforming the mesh with the bones).
"""
import json, re, numpy as np
from scipy.spatial import cKDTree
from lib import load, meta, W
from geom import dense

CONTACT = 0.003     # m
TAU = 0.006         # m, softness of skin-weight falloff
ATT_OK = 0.010      # m, attachment area must be this close to the muscle mesh

rig = json.load(open(f'{W}/rig.json'))
B, A, Mu = load('bones'), load('attach'), load('muscles')
MD = meta()

EXCLUDE = re.compile(r'bursa|sheath|retinacul|fascia|septum|aponeurosis|Cross Section|Iliotibial|Cruciform|Synovial', re.I)
EXTRA = {   # muscles outside the limb groups that move the girdle
    'arm': ['Clavicular head of pectoralis major muscle', 'Sternocostal head of pectoralis major muscle',
            '(Abdominal part of pectoralis major muscle)', 'Pectoralis minor muscle', 'Serratus anterior muscle',
            'Subclavius muscle', 'Ascending part of trapezius muscle', 'Descending part of trapezius muscle',
            'Transverse part of trapezius muscle', 'Latissimus dorsi muscle', 'Levator scapulae',
            'Rhomboid major muscle', 'Rhomboid minor muscle'],
    'leg': [],
}
LIMB_GROUP = {'arm': 'Muscular system of upper limb.g', 'leg': 'Muscular system of lower limb.g'}
ALIASES = {
    'Biceps brachii muscle': ['Long head of biceps brachii', 'Short head of biceps brachii'],
    'Triceps brachii muscle': ['Long head of triceps brachii', 'Lateral head of triceps brachii', 'Medial head of triceps brachii'],
    'Deltoid muscle': ['Clavicular part of deltoid muscle', 'Acromial part of deltoid muscle', 'Scapular spinal part of deltoid muscle'],
    'Quadriceps femoris muscle': ['Rectus femoris muscle', 'Vastus lateralis muscle', 'Vastus medialis muscle', 'Vastus intermedius muscle'],
    'Triceps surae muscle': ['Lateral head of gastrocnemius', 'Medial head of gastrocnemius', 'Soleus muscle', 'Calcaneal tendon'],
    'Iliopsoas muscle': ['Iliacus muscle', 'Psoas major'],
    'Biceps femoris muscle': ['Long head of biceps femoris', 'Short head of biceps femoris'],
    'Pectoralis major muscle': ['Clavicular head of pectoralis major muscle', 'Sternocostal head of pectoralis major muscle', '(Abdominal part of pectoralis major muscle)'],
    'Common flexor tendon': ['Superficial head of pronator teres', 'Flexor carpi radialis', 'Palmaris longus muscle',
                             'Humero-ulnar head of flexor digitorum superficialis', 'Humeral head of flexor carpi ulnaris'],
    'Common extensor tendon': ['Extensor carpi radialis brevis', 'Extensor digitorum', 'Extensor digiti minimi', 'Humeral head of extensor carpi ulnaris'],
    'Flexor carpi ulnaris': ['Humeral head of flexor carpi ulnaris', 'Ulnar head of flexor carpi ulnaris'],
    'Extensor carpi ulnaris': ['Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris'],
    'Flexor digitorum superficialis': ['Humero-ulnar head of flexor digitorum superficialis', 'Radial head of flexor digitorum superficialis'],
    'Pronator teres': ['Superficial head of pronator teres', 'Deep head of pronator teres'],
    'Adductor pollicis': ['Oblique head of adductor pollicis', 'Transverse head of adductor pollicis'],
    'Extensor digitorum longus': ['Extensor digitorum longus', 'Tendon of extensor digitorum longus'],
}

def base(n):
    return re.sub(r'\.(r|l)$', '', n)

def norm(s):
    return re.sub(r'\s+muscles?$', '', s.strip('() ').lower())

# attachment areas (right side) grouped by normalised name
att_by = {}
for n in A:
    if not re.search(r'\.[oe]\d*r$', n):
        continue
    b = n.rsplit('.', 1)[0]
    att_by.setdefault(norm(b), []).append(n)
alias_rev = {}
for g, ms in ALIASES.items():
    for m in ms:
        alias_rev.setdefault(norm(m), []).append(norm(g))

def region_bones(region):
    seg_of = {}
    for s, d in rig['regions'][region]['segments'].items():
        for b in d['bones']:
            seg_of[b] = s
    return seg_of

def chain_to_root(region, s):
    segs = rig['regions'][region]['segments']
    out = [s]
    while s is not None and segs[s]['parent'] is not None:
        s = segs[s]['parent']; out.append(s)
    return out + ['trunk']

def chain_between(region, ss):
    """All segments on tree paths connecting the attached segments (root 'trunk' is static)."""
    paths = [chain_to_root(region, s) if s != 'trunk' else ['trunk'] for s in ss]
    keep = set()
    common = set(paths[0])
    for p in paths[1:]:
        common &= set(p)
    # lowest common ancestor
    lca = next(x for x in paths[0] if x in common)
    for p in paths:
        for x in p:
            keep.add(x)
            if x == lca:
                break
    return keep

def bind(region):
    seg_of = region_bones(region)
    segs = list(rig['regions'][region]['segments'].keys())
    # dense samples per segment, plus the static trunk (every other bone)
    seg_pts = {s: [] for s in segs + ['trunk']}
    for b, m in B.items():
        if b.endswith('.l') and region != 'arm':
            pass
        s = seg_of.get(b, 'trunk')
        seg_pts[s].append(dense(m, 8000 if s == 'trunk' else 30000))
    trees = {s: cKDTree(np.vstack(p)) for s, p in seg_pts.items()}
    order = {s: i for i, s in enumerate(['trunk'] + segs)}

    cands = [n for n in Mu if n.endswith('.r') and not EXCLUDE.search(n)
             and (LIMB_GROUP[region] in MD['muscles'][n]['chain'] or base(n) in EXTRA[region])]
    out = {}
    for n in cands:
        v = Mu[n]['v'].astype(np.float64)
        dist = {s: trees[s].query(v)[0] for s in trees}
        contact = {s: int((d < CONTACT).sum()) for s, d in dist.items()}
        need = max(6, int(0.01 * len(v)))
        attached = {s for s, c in contact.items() if c >= need}
        anchors = {}
        for s in attached:
            sel = v[dist[s] < CONTACT]
            anchors[s] = dict(p=sel.mean(0).tolist(), src='contact', n=len(sel))
        # name-matched attachment areas (validated by proximity)
        keys = [norm(base(n))] + alias_rev.get(norm(base(n)), [])
        vt = cKDTree(v)
        used = []
        for k in keys:
            for an in att_by.get(k, []):
                bone = MD['attach'][an]['bone']
                if bone is None:
                    continue
                av = A[an]['v'].astype(np.float64)
                gap = vt.query(av)[0].min()
                s = seg_of.get(bone, 'trunk')
                if gap > ATT_OK:
                    used.append(f'REJECT {an} ({gap*1000:.0f}mm away)')
                    continue
                used.append(f'{an}->{s}')
                attached.add(s)
                prev = anchors.get(s)
                if prev is None or prev['src'] == 'contact':
                    anchors[s] = dict(p=av.mean(0).tolist(), src='attach:' + an, n=len(av))
                else:   # several areas on one segment: average them
                    anchors[s]['p'] = ((np.array(prev['p']) + av.mean(0)) / 2).tolist()
        moving = [s for s in attached if s != 'trunk']
        if not moving:
            continue
        chain = chain_between(region, sorted(attached, key=order.get))
        chain = sorted(chain, key=order.get)
        out[n] = dict(contact={s: c for s, c in contact.items() if c}, attached=sorted(attached, key=order.get),
                      chain=chain, anchors=anchors, att=used, nv=len(v))
    return out, trees

if __name__ == '__main__':
    res = {}
    for region in ['arm', 'leg']:
        r, _ = bind(region)
        res[region] = r
        print(f'## {region}: {len(r)} muscles')
        for n, d in sorted(r.items()):
            anc = ' '.join(f"{s}[{a['src'][:6]}]" for s, a in sorted(d['anchors'].items(), key=lambda x: d['attached'].index(x[0]) if x[0] in d['attached'] else 99))
            print(f"{base(n):<52} attached={'>'.join(d['attached']):<34} anchors: {anc}")
            rej = [u for u in d['att'] if u.startswith('REJECT')]
            if rej:
                print('     ', '; '.join(rej))
    json.dump(res, open(f'{W}/binding_analysis.json', 'w'), indent=0)
