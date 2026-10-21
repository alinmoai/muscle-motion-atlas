"""Write random poses with reference matrices and muscle lengths computed by kin.py, so that the
JavaScript port (site/src/kin.js) can be checked against it (site/src/test_kin.mjs)."""
import json, numpy as np
from lib import BUILD
from kin import fk, apply

model = json.load(open(f'{BUILD}/raw/model.json'))
rig = model['rig']
rng = np.random.default_rng(5)
vec = []
for region in ['arm', 'leg']:
    dofs = rig['regions'][region]['dofs']
    for _ in range(25):
        ang = {d['id']: float(rng.uniform(d['min'], d['max'])) for d in dofs}
        M = fk(rig, region, ang)
        L = {}
        for n, m in model['regions'][region]['muscles'].items():
            P = [apply(M[a['seg']], a['p']) if a['seg'] != 'trunk' else np.array(a['p']) for a in m['anchors']]
            l = sum(np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1))
            if m.get('wrap'):
                l += m['wrap']['sign'] * m['wrap']['r'] * np.radians(ang.get(m['wrap']['dof'], 0))
            L[n] = float(l)
        vec.append(dict(region=region, ang=ang, M={s: np.asarray(v).reshape(-1).tolist() for s, v in M.items() if not s.startswith('_')}, L=L))
json.dump(vec, open(f'{BUILD}/raw/test_vectors.json', 'w'))
print('test vectors:', len(vec))
