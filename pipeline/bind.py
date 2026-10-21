"""Final muscle binding: overrides from anatomical review, joint-level via points, ordered anchors,
skin weights. Writes work/bind_<region>.npz (geometry + weights) and work/bind_<region>.json (metadata)."""
import json, re, numpy as np
from scipy.spatial import cKDTree
from lib import load, meta, W
from geom import unit, pca
from muscles import bind, base, ALIASES, TAU, A, Mu, MD, rig, region_bones, chain_between
from names import NAME_FIX, ZH, GROUPS

J = json.load(open(f'{W}/joints_refined.json'))

def att_centroid(names):
    pts = [A[n]['v'].astype(np.float64).mean(0) for n in names if n in A]
    return np.mean(pts, 0)

FDS_E = [n for n in A if n.startswith('Flexor digitorum superficialis.e') and n.endswith('r')]
EDL_E = [n for n in A if n.startswith('Extensor digitorum longus.e') and n.endswith('r')]

# Review of the automatic binding against anatomy. Each entry says WHY.
OVERRIDES = {
    'arm': {
        'Brachialis muscle': dict(drop=['radius'], why='inserts on the ulna only; radius contact is incidental'),
        'Clavicular part of deltoid muscle': dict(drop=['scapula'], why='runs clavicle -> humerus over the humeral head'),
        'Flexor digitorum profundus': dict(drop=['radius'], why='arises from ulna; does not attach to the radius'),
        'Radial head of flexor digitorum superficialis': dict(add={'hand': FDS_E}, why='FDS tendons insert on middle phalanges'),
        'Short head of biceps brachii': dict(add={'radius': ['Biceps brachii muscle.er']}, why='common biceps tendon inserts on radial tuberosity'),
        'Sternocostal head of pectoralis major muscle': dict(drop=['clavicle'], why='arises from sternum/costal cartilages, not clavicle'),
        'Subscapularis muscle': dict(drop=['trunk'], why='lies on the ribs but attaches only scapula -> humerus'),
        'Supraspinatus muscle': dict(drop=['clavicle'], why='passes under the AC joint; attaches scapula -> humerus'),
        'Transverse part of trapezius muscle': dict(drop=['clavicle'], why='middle fibres insert on acromion / scapular spine'),
        'Ulnar head of flexor carpi ulnaris': dict(drop=['humerus'], add={'carpus': ['Flexor carpi ulnaris.er']},
                                                  why='arises from olecranon/ulna, inserts on pisiform'),
        'Abductor pollicis brevis': dict(drop=['carpus'], why='finger joints are not modelled; keep hand intrinsics rigid with the hand'),
        'Abductor digiti minimi of hand': dict(drop=['carpus'], why='finger joints are not modelled; keep hand intrinsics rigid with the hand'),
        'Descending part of trapezius muscle': dict(point={'scapula': 'lower_trap_root', 'trunk': 'lower_trap_origin'},
                                                    why='lower fibres insert on the medial end (root) of the scapular spine'),
    },
    'leg': {
        'Calcaneal tendon': dict(kind='tendon', chain=['tibia', 'talus', 'foot'], why='tendon of triceps surae'),
        'Tendon of extensor digitorum longus': dict(kind='tendon', chain=['tibia', 'talus', 'foot', 'toes'], why='tendon'),
        'Extensor digitorum longus': dict(add={'toes': EDL_E}, why='tendons insert on toes 2-5'),
        'Lateral head of gastrocnemius': dict(add={'foot': ['Triceps surae muscle.er']}, why='inserts on calcaneus via the Achilles tendon'),
        'Medial head of gastrocnemius': dict(drop=['tibia'], add={'foot': ['Triceps surae muscle.er']}, why='inserts on calcaneus via the Achilles tendon'),
        'Soleus muscle': dict(add={'foot': ['Triceps surae muscle.er']}, why='inserts on calcaneus via the Achilles tendon'),
        'Rectus femoris muscle': dict(drop=['femur', 'tibia'], why='AIIS -> patella; does not attach to femur'),
        'Fibularis longus muscle': dict(point={'foot': 'fl_cuboid'}, why='tendon turns under the cuboid (its pulley) on the way to the 1st metatarsal'),
        'Semitendinosus muscle': dict(drop=['femur'], why='ischial tuberosity -> medial tibia; lies on the femur without attaching'),
        'Semimembranosus muscle': dict(drop=['femur'], why='ischial tuberosity -> posteromedial tibia; lies on the femur without attaching'),
        'Vastus lateralis muscle': dict(drop=['tibia'], why='quadriceps inserts on the patella'),
        'Vastus medialis muscle': dict(drop=['tibia'], why='quadriceps inserts on the patella'),
        'Vastus intermedius muscle': dict(drop=['tibia'], why='quadriceps inserts on the patella'),
    },
}
FORCE = {   # muscles the contact test misses because their distal attachment is not in this model
    'leg': {'Tensor fasciae latae.r': dict(why='inserts into the iliotibial tract -> lateral tibia (Gerdy tubercle)')},
}
# Via points where tendons wrap a joint (retinacula, condyles, malleoli): centroid of the muscle where it
# crosses a plane near the joint, attached to the segment that carries the pulley.
_fem_ax = unit(np.array(J['hip']['center']) - np.array(J['knee']['center']))
_tib_ax = unit(np.array(J['knee']['center']) - np.array(J['ankle']['center']))
VIA = {
    'arm': [dict(name='wrist', seg='radius', center=J['radiocarpal']['center'], normal=J['wrist']['forearm'],
                 prox={'trunk', 'clavicle', 'scapula', 'humerus', 'ulna', 'radius'}, dist={'hand'},
                 skip={'Humeral head of flexor carpi ulnaris', 'Ulnar head of flexor carpi ulnaris',
                       'Humeral head of extensor carpi ulnaris', 'Ulnar head of extensor carpi ulnaris'})],
    'leg': [  # knee: just below the joint line, on the tibia (pes anserinus / hamstring tendons curve here)
            dict(name='knee', seg='tibia', center=list(np.array(J['knee']['center']) - 0.015 * _fem_ax), normal=list(_fem_ax),
                 prox={'trunk', 'femur'}, dist={'tibia', 'talus', 'foot', 'toes'}, skip=set()),
            # ankle: malleolar grooves / extensor retinaculum, just above the malleoli tips
            dict(name='ankle', seg='tibia', center=list(np.array(J['ankle']['center']) + 0.012 * _tib_ax), normal=list(_tib_ax),
                 prox={'trunk', 'femur', 'tibia'}, dist={'talus', 'foot', 'toes'}, skip=set()),
            # MTP: tendons pass dorsal or plantar to the metatarsal heads
            dict(name='mtp', seg='foot', center=J['mtp']['center'], normal=J['subtalar']['foot_long'],
                 prox={'trunk', 'femur', 'tibia', 'talus', 'foot'}, dist={'toes'}, skip=set())],
}
EXTRA_VIA = {   # (segment, point) inserted just before the distal end
    'Obturator internus': lambda: [('trunk', Mu['Sciatic bursa of obturator internus.r']['v'].astype(np.float64).mean(0), 'via:lesser sciatic notch')],
    'Tensor fasciae latae': lambda: [('femur', (lambda v: v[v[:, 2] < v[:, 2].min() + 0.02].mean(0))(Mu['Tensor fasciae latae.r']['v'].astype(np.float64)), 'via:iliotibial tract over greater trochanter')],
}
WRAP = {   # tendon wrapping around a rotating bone: length += sign * r * angle (rad)
    'Long head of biceps brachii': dict(dof='pron', r=0.010, sign=1, why='biceps tendon winds round the radius in pronation'),
    'Short head of biceps brachii': dict(dof='pron', r=0.010, sign=1, why='biceps tendon winds round the radius in pronation'),
}

def vertex_normals(v, t):
    n = np.zeros_like(v)
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    for k in range(3):
        np.add.at(n, t[:, k], fn)
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return (n / ln).astype(np.float32)

def run(region):
    res, trees = bind(region)
    segs = ['trunk'] + list(rig['regions'][region]['segments'].keys())
    sidx = {s: i for i, s in enumerate(segs)}
    order = {s: i for i, s in enumerate(segs)}
    ov = OVERRIDES[region]
    # forced muscles
    for n, f in FORCE.get(region, {}).items():
        v = Mu[n]['v'].astype(np.float64)
        anchors = {}
        if n.startswith('Tensor fasciae latae'):
            anchors['trunk'] = dict(p=att_centroid(['Tensor fasciae latae.or']).tolist(), src='attach')
            it = Mu['Iliotibial tract.r']['v'].astype(np.float64)
            low = it[it[:, 2] < it[:, 2].min() + 0.02].mean(0)
            anchors['tibia'] = dict(p=low.tolist(), src='iliotibial tract distal end')
        res[n] = dict(attached=sorted(anchors, key=order.get), anchors=anchors, nv=len(v), forced=f['why'])

    meta_out, geo = {}, {}
    for n, d in res.items():
        b = base(n)
        o = ov.get(b, {})
        anchors = {s: np.array(a['p']) for s, a in d['anchors'].items()}
        for s in o.get('drop', []):
            anchors.pop(s, None)
        for s, names in o.get('add', {}).items():
            anchors[s] = att_centroid(names)
        for s, how in o.get('point', {}).items():
            if how == 'lower_trap_root':
                av = A['Descending part of trapezius muscle.or']['v'].astype(np.float64)
                anchors[s] = av[av[:, 0] > np.percentile(av[:, 0], 75)].mean(0)      # medial quarter (+X is medial)
            elif how == 'lower_trap_origin':
                # origin runs T4-T12; use the lower half of the mesh's contact with the spine for the line of pull
                vv = Mu[n]['v'].astype(np.float64)
                cv = vv[trees['trunk'].query(vv)[0] < 0.004]
                anchors[s] = cv[cv[:, 2] < np.median(cv[:, 2])].mean(0)
            elif how == 'fl_cuboid':
                vv = Mu[n]['v'].astype(np.float64)
                cub = cKDTree(np.vstack([load('bones')['Cuboid bone.r']['v']]))
                anchors[s] = vv[cub.query(vv)[0] < 0.004].mean(0)
        attached = sorted(anchors, key=order.get)
        kind = o.get('kind', 'muscle')
        if 'chain' in o:
            chain = o['chain']
        else:
            chain = sorted(chain_between(region, attached), key=order.get)
        v = Mu[n]['v'].astype(np.float64)
        t = Mu[n]['t']
        # anchor path: proximal anchors (segment order) -> joint vias (proximal->distal) -> final distal end.
        # Contacts beyond the first joint via are dropped: they are the tendon sliding over bones, not pulleys.
        ends = sorted(anchors.items(), key=lambda x: order[x[0]])
        vias = []
        for vj in VIA[region]:
            if b in vj['skip']:
                continue
            if set(attached) & vj['prox'] and set(attached) & vj['dist']:
                c, nn = np.array(vj['center']), unit(vj['normal'])
                slab = v[np.abs((v - c) @ nn) < 0.007]
                if len(slab) >= 5:
                    vias.append((vj['seg'], slab.mean(0), 'via:' + vj['name']))
        extra = EXTRA_VIA[b]() if b in EXTRA_VIA else []
        first_joint = vias[0][2][4:] if vias else None
        for i, (sv, pv, rv) in enumerate(vias):
            if rv == 'via:knee' and b in ('Sartorius muscle', 'Gracilis muscle'):
                # pes anserinus tendons pass together behind the knee axis; this model draws sartorius/gracilis
                # slightly in front of it, so they share semitendinosus's pulley point
                st = Mu['Semitendinosus muscle.r']['v'].astype(np.float64)
                c, nn = np.array(VIA['leg'][0]['center']), unit(VIA['leg'][0]['normal'])
                vias[i] = (sv, st[np.abs((st - c) @ nn) < 0.007].mean(0), 'via:knee (pes anserinus, shared)')
            if rv == 'via:mtp' and b in ('Dorsal interossei muscles of foot', 'Plantar interossei muscles'):
                # interossei pass plantar to the deep transverse metatarsal ligament, i.e. below the MTP axis (they flex the MTP)
                mc, ma = np.array(J['mtp']['center']), unit(J['mtp']['axis'])
                up = unit(np.cross(ma, J['subtalar']['foot_long']))
                if up[2] < 0:
                    up = -up
                q = pv - ((pv - mc) @ up) * up - 0.006 * up
                vias[i] = (sv, q, 'via:mtp (plantar to the metatarsal heads)')
            if rv == 'via:ankle' and b in ('Fibularis longus muscle', 'Fibularis brevis muscle'):
                # fibular tendons turn round the tip of the lateral malleolus
                lm = np.array(J['ankle']['lateral_malleolus'])
                nn = unit(VIA['leg'][1]['normal'])
                sl = v[np.abs((v - lm) @ nn) < 0.007]
                if len(sl) >= 5:
                    vias[i] = (sv, sl.mean(0), 'via:lateral malleolus')
        if vias:
            first_dist = VIA[region][[x['name'] for x in VIA[region]].index(first_joint)]['dist']
            prox_part = [(s_, p_, 'end') for s_, p_ in ends if s_ not in first_dist]
            alist = prox_part + vias + extra + [(ends[-1][0], ends[-1][1], 'end')]
        else:
            alist = [(s_, p_, 'end') for s_, p_ in ends[:-1]] + extra + [(ends[-1][0], ends[-1][1], 'end')]
        # skin weights over chain segments
        D = np.stack([trees[s].query(v)[0] for s in chain], 1)
        # softer blending for vertices far from every bone (flat sheets like pectoralis/latissimus)
        dmin = D.min(1, keepdims=True)
        Wt = np.exp(-(D - dmin) / (TAU + 0.5 * dmin))
        k = min(3, len(chain))
        top = np.argsort(-Wt, 1)[:, :k]
        wsel = np.take_along_axis(Wt, top, 1)
        wsel /= wsel.sum(1, keepdims=True)
        joints = np.zeros((len(v), 4), np.uint8)
        weights = np.zeros((len(v), 4), np.float32)
        joints[:, :k] = np.vectorize(lambda i: sidx[chain[i]])(top)
        weights[:, :k] = wsel
        true = NAME_FIX.get(b, b)
        group = next((g for g, _, ms in GROUPS[region] if true in ms), None)
        meta_out[n] = dict(source_name=b, name=true, zh=ZH.get(true, true), group=group, kind=kind,
                           renamed=b != true, chain=chain,
                           anchors=[dict(seg=s, p=[round(float(x), 5) for x in p], role=r) for s, p, r in alist],
                           why=o.get('why') or d.get('forced'), wrap=WRAP.get(b))
        geo[n] = dict(v=v.astype(np.float32), t=t.astype(np.uint32), n=vertex_normals(v, t), j=joints, w=weights)
    missing = [m for _, _, ms in GROUPS[region] for m in ms if m not in {x['name'] for x in meta_out.values()}]
    nogroup = [x['name'] for x in meta_out.values() if x['group'] is None]
    print(f'{region}: {len(meta_out)} muscles bound; in groups but not bound: {missing}; bound but ungrouped: {nogroup}')
    np.savez_compressed(f'{W}/bind_{region}.npz', **{f'{n}|{k}': a for n, g in geo.items() for k, a in g.items()})
    json.dump(dict(segments=segs, muscles=meta_out), open(f'{W}/bind_{region}.json', 'w'), indent=0, ensure_ascii=False)
    return meta_out

if __name__ == '__main__':
    for r in ['arm', 'leg']:
        m = run(r)
        for n, d in sorted(m.items(), key=lambda x: x[1]['group'] or ''):
            print(f"  [{d['group']}] {d['zh']:<14} {' > '.join(a['seg'] + ('*' if a['role'] != 'end' else '') for a in d['anchors'])}")
