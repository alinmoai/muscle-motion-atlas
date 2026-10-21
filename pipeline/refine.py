"""Refine hinge pivots so articular surfaces stay in contact through the range of motion.
For each candidate pivot we rotate the moving bone's articular points and measure the SIGNED
distance to the fixed partner bone (negative = inside the bone). We keep the pivot whose gap stays
closest to the rest gap without penetration. Results go to joints_refined.json.
"""
import json, itertools, numpy as np
from lib import load, W
from geom import Surface, unit, rot, contact, sphere_fit

B = load('bones')
J = json.load(open(f'{W}/joints_raw.json'))
signs = json.load(open(f'{W}/rig.json'))['signs']
SURF = {}
def surf(n, k=120000):
    if n not in SURF:
        SURF[n] = Surface(B[n], k)
    return SURF[n]

def merged(names, k=60000):
    ss = [surf(n, k) for n in names]
    s = Surface.__new__(Surface)
    s.p = np.vstack([x.p for x in ss]); s.n = np.vstack([x.n for x in ss])
    from scipy.spatial import cKDTree
    s.tree = cKDTree(s.p)
    return s

def plane_basis(axis):
    a = unit(axis)
    u = unit(np.cross(a, [0, 0, 1.0]) if abs(a[2]) < 0.9 else np.cross(a, [0, 1.0, 0]))
    return u, np.cross(a, u)

def evaluate(art, fixed, center, axis, angles):
    meds, pens = [], []
    for th in angles:
        R = rot(axis, np.radians(th))
        q = (art - center) @ R.T + center
        sd = fixed.sdist(q)
        meds.append(np.median(sd)); pens.append(np.mean(sd < -0.0008))
    return np.array(meds), np.array(pens)

def objective(meds, pens, med0):
    return np.sum((meds - med0) ** 2) * 1e6 + 40 * np.sum(pens)

def optimise_plane(name, art, fixed, center0, axis, angles, half=0.015, step=0.0015):
    u, w = plane_basis(axis)
    med0 = np.median(fixed.sdist(art))
    best = None
    rngv = np.arange(-half, half + 1e-9, step)
    for a, b in itertools.product(rngv, rngv):
        c = center0 + a * u + b * w
        meds, pens = evaluate(art, fixed, c, axis, angles)
        f = objective(meds, pens, med0)
        if best is None or f < best[0]:
            best = (f, c, meds, pens)
    m0, p0 = evaluate(art, fixed, center0, axis, angles)
    print(f'{name}: rest gap {med0*1000:.1f} mm | before: gaps {np.round(m0*1000,1)} pen {np.round(p0*100,1)}%'
          f' | after: gaps {np.round(best[2]*1000,1)} pen {np.round(best[3]*100,1)}% | moved {np.linalg.norm(best[1]-center0)*1000:.1f} mm')
    return best[1]

def art_points(moving, fixed_names, near):
    m = surf(moving)
    fx = merged(fixed_names) if isinstance(fixed_names, list) else surf(fixed_names)
    d, _ = fx.tree.query(m.p)
    sel = m.p[d < near]
    if len(sel) > 3000:
        sel = sel[np.random.default_rng(1).choice(len(sel), 3000, replace=False)]
    return sel, fx

R = dict(J)

# ---- knee: tibial plateau against femoral condyles (femur fixed, tibia moves) ----
ax = np.array(J['knee']['axis']); sg = signs['kn_flex']
art, fem = art_points('Tibia.r', 'Femur.r', 0.008)
art = art[art[:, 2] > np.array(J['knee']['center'])[2] - 0.05]
kc = optimise_plane('knee', art, fem, np.array(J['knee']['center']), ax, [sg * t for t in (0, 30, 60, 90, 120, 140)])
R['knee'] = dict(J['knee'], center=kc.tolist())

# ---- ankle: talus against tibia+fibula mortise ----
ax = np.array(J['ankle']['axis']); sg = signs['an_flex']
art, mort = art_points('Talus.r', ['Tibia.r', 'Fibula.r'], 0.005)
ac = optimise_plane('ankle', art, mort, np.array(J['ankle']['center']), ax, [sg * t for t in (-20, 0, 20, 35, 50)])
R['ankle'] = dict(J['ankle'], center=ac.tolist())

# ---- elbow: ulna against humerus (check only, refine lightly) ----
ax = np.array(J['elbow']['axis']); sg = signs['el_flex']
art, hum = art_points('Ulna.r', 'Humerus.r', 0.004)
ec = optimise_plane('elbow', art, hum, np.array(J['elbow']['center']), ax, [sg * t for t in (0, 45, 90, 135)], half=0.006, step=0.001)
R['elbow'] = dict(J['elbow'], center=ec.tolist())

# ---- forearm: radius rotating against ulna; optimise each end of the pronation axis ----
p0, p1 = np.array(J['pronation']['p0']), np.array(J['pronation']['p1'])
art_all, uln = art_points('Radius.r', 'Ulna.r', 0.004)
zmid = 0.5 * (p0[2] + p1[2])
prox_art, dist_art = art_all[art_all[:, 2] > zmid], art_all[art_all[:, 2] <= zmid]
sg = signs['pron']
for it in range(2):
    ax = unit(p0 - p1)
    p0 = optimise_plane(f'pronation proximal (iter {it})', prox_art, uln, p0, ax, [sg * t for t in (0, 45, 90, 140)], half=0.008, step=0.001)
    ax = unit(p0 - p1)
    p1 = optimise_plane(f'pronation distal (iter {it})', dist_art, uln, p1, ax, [sg * t for t in (0, 45, 90, 140)], half=0.008, step=0.001)
R['pronation'] = dict(J['pronation'], p0=p0.tolist(), p1=p1.tolist(), axis=unit(p0 - p1).tolist())

# ---- wrist: split motion between radiocarpal (proximal row vs radius) and midcarpal (rest vs proximal row) ----
fe, dv = np.array(J['wrist']['fe_axis']), np.array(J['wrist']['dev_axis'])
prow = ['Scaphoid bone.r', 'Lunate bone.r', 'Triquetrum bone.r']
art_rc = np.vstack([art_points(n, 'Radius.r', 0.004)[0] for n in prow[:2]])
rad = surf('Radius.r')
c0 = sphere_fit(art_rc)[0]
best = None
grid = np.arange(-0.008, 0.0081, 0.002)
med0 = np.median(rad.sdist(art_rc))
for a, b, c in itertools.product(grid, grid, grid):
    cen = c0 + np.array([a, b, c])
    f = 0
    for axis, ang in ((fe, 35), (fe, -35), (dv, 12), (dv, -18)):
        m, p = evaluate(art_rc, rad, cen, axis, [ang])
        f += objective(m, p, med0)
    if best is None or f < best[0]:
        best = (f, cen)
rc = best[1]
for axis, nm in ((fe, 'flex'), (dv, 'dev')):
    m, p = evaluate(art_rc, rad, rc, axis, [-35, 0, 35])
    print(f'radiocarpal {nm}: gaps {np.round(m*1000,1)} pen {np.round(p*100,1)}% (rest {med0*1000:.1f})')
R['radiocarpal'] = dict(center=rc.tolist())

json.dump(R, open(f'{W}/joints_refined.json', 'w'), indent=1)
print('refined joints written')
