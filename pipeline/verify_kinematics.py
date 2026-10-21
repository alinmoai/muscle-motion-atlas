"""Numerically fix the sign of every DOF and check that joints stay congruent.
A positive slider value must produce the motion named in the DOF label; this is decided by
measuring where a landmark goes, never by looking at a picture.
"""
import json, sys, numpy as np
from scipy.spatial import cKDTree
from lib import load, W
from geom import dense, contact, unit
from kin import fk, apply, about, T

rig = json.load(open(f'{W}/rig.json'))
rig['signs'] = {}
rig.pop('patella_track', None)
B = load('bones')
P = {}
def pts(n, k=40000):
    if n not in P:
        P[n] = dense(B[n], k)
    return P[n]
J = json.load(open(f'{W}/joints_raw.json'))

report = []
def rep(s):
    report.append(s); print(s)

# landmarks (rest)
elbow = np.array(J['elbow']['center'])
wrist = np.array(J['wrist']['center'])
R = pts('Radius.r'); rad_sty = R[np.argmin(R[:, 2])]
mc3 = pts('Third metacarpal bone.r'); mc3_head = mc3[mc3[:, 2] < mc3[:, 2].min() + 0.008].mean(0)
ac = np.array(J['AC']['center'])
S = pts('Scapula.r'); inf_angle = S[np.argmin(S[:, 2])]
knee = np.array(J['knee']['center'])
ankle = np.array(J['ankle']['center'])
mtp = np.array(J['mtp']['center'])
h1, h5 = np.array(J['mtp']['p1']), np.array(J['mtp']['p5'])
toe2 = pts('Distal phalanx of second finger of foot.r').mean(0)

def disp(region, seg, p, ang, base=None):
    M0 = fk(rig, region, base or {})
    M1 = fk(rig, region, {**(base or {}), **ang})
    return apply(M1[seg], p) - apply(M0[seg], p)

# (dof, region, segment, landmark, test-angle, criterion(delta) -> True if positive slider gives named motion, base pose)
tests = [
    ('clav_elev', 'arm', 'clavicle', ac,         None, lambda d: d[2] > 0, None),
    ('scap_up',   'arm', 'scapula', inf_angle,   None, lambda d: d[0] < 0, None),
    ('sh_flex',   'arm', 'humerus', elbow,       30, lambda d: d[1] < 0, None),
    ('sh_abd',    'arm', 'humerus', elbow,       30, lambda d: d[0] < 0, None),
    ('el_flex',   'arm', 'ulna',    wrist,       30, lambda d: d[1] < 0, None),
    ('sh_rot',    'arm', 'ulna',    wrist,       30, lambda d: d[0] > 0, {'el_flex': 90}),
    ('pron',      'arm', 'radius',  rad_sty,     30, lambda d: d[1] < 0, None),
    ('wr_flex',   'arm', 'hand',    mc3_head,    30, lambda d: d[1] < 0, None),
    ('wr_dev',    'arm', 'hand',    mc3_head,    20, lambda d: d[0] > 0, None),
    ('hip_flex',  'leg', 'femur',   knee,        30, lambda d: d[1] < 0, None),
    ('hip_abd',   'leg', 'femur',   knee,        20, lambda d: d[0] < 0, None),
    ('hip_rot',   'leg', 'foot',    mtp,         20, lambda d: d[0] > 0, None),
    ('kn_flex',   'leg', 'tibia',   ankle,       30, lambda d: d[1] > 0, None),
    ('an_flex',   'leg', 'toes',    mtp,         20, lambda d: d[2] < 0, None),
    ('toe',       'leg', 'toes',    toe2,        30, lambda d: d[2] > 0, None),
]
for dof, region, seg, p, a, ok, base in tests:
    if dof in ('clav_elev', 'scap_up'):
        # coupled joints: test the raw rotation directly
        j = rig['regions']['arm']['joints']['clavicle' if dof == 'clav_elev' else 'scapula']
        d = (about(j['pivot'], j['axis'], 10.0) @ np.r_[p, 1])[:3] - p
    else:
        d = disp(region, seg, p, {dof: a}, base)
    sgn = 1 if ok(d) else -1
    rig['signs'][dof] = sgn
    rep(f'sign {dof:<9} = {sgn:+d}   (landmark moved {np.round(d * 1000, 1)} mm at +{a or 10}°)')

# inversion: medial (1st MT) head rises relative to lateral (5th MT) head
M0 = fk(rig, 'leg', {}); M1 = fk(rig, 'leg', {'inv': 20})
d0 = apply(M0['foot'], h1)[2] - apply(M0['foot'], h5)[2]
d1 = apply(M1['foot'], h1)[2] - apply(M1['foot'], h5)[2]
rig['signs']['inv'] = 1 if d1 > d0 else -1
rep(f"sign inv       = {rig['signs']['inv']:+d}   (1st-5th MT head height diff {d0*1000:.1f} -> {d1*1000:.1f} mm)")

# re-check every criterion with the final signs (must all pass now)
fails = 0
for dof, region, seg, p, a, ok, base in tests:
    if dof in ('clav_elev', 'scap_up'):
        continue
    d = disp(region, seg, p, {dof: a}, base)
    if not ok(d):
        fails += 1; rep(f'FAIL after sign fix: {dof}')
rep(f'direction checks re-run with final signs: {len(tests) - 2 - fails}/{len(tests) - 2} pass')
if fails:
    sys.exit('direction checks failed')
if '--signs-only' in sys.argv:          # first pass: refine.py and knee_track.py only need the signs
    json.dump(rig, open(f'{W}/rig.json', 'w'), indent=1, ensure_ascii=False)
    sys.exit(0)

# ---------- patella track: keep the patella resting on the femur through knee flexion ----------
F = pts('Femur.r', 120000); Pa = pts('Patella.r', 20000)
treeF = cKDTree(F)
kn = rig['regions']['leg']['joints']['patella']
kc, kax = np.array(kn['pivot']), unit(kn['axis'])
pc = Pa.mean(0)
u_out = pc - kc; u_out -= (u_out @ kax) * kax; u_out = unit(u_out)
back = Pa[treeF.query(Pa)[0] < 0.010]                      # articular (posterior) face of the patella
gap0 = np.percentile(treeF.query(back)[0], 5)
frac = 0.7
thetas, deltas = [], []
for th in range(0, 145, 5):
    best = None
    for dl in np.arange(-0.004, 0.030, 0.0005):
        Mloc = about(kc, kax, rig['signs']['kn_flex'] * frac * th) @ T(-dl * u_out)
        q = back @ Mloc[:3, :3].T + Mloc[:3, 3]
        g = np.percentile(treeF.query(q)[0], 5)
        if best is None or abs(g - gap0) < best[1]:
            best = (dl, abs(g - gap0))
    thetas.append(th); deltas.append(round(float(best[0]), 5))
rig['patella_track'] = dict(theta=thetas, delta=deltas, fraction=frac, u_out=[float(x) for x in u_out])
rep(f'patella track: slide towards knee axis {deltas[0]*1000:.1f} mm @0°, {deltas[9]*1000:.1f} mm @45°, {deltas[18]*1000:.1f} mm @90°, {deltas[-1]*1000:.1f} mm @140°')

json.dump(rig, open(f'{W}/rig.json', 'w'), indent=1, ensure_ascii=False)

# ---------- congruency: articular surfaces should stay at roughly the same distance ----------
def congruency(region, child_seg, child_bone, parent_seg, parent_bone, dof, angles, base=None, near=0.004):
    C = pts(child_bone); Pp = pts(parent_bone, 80000)
    art = contact(C, Pp, near)
    while len(art) < 200 and near < 0.02:
        near += 0.002
        art = contact(C, Pp, near)
    out = []
    for a in angles:
        M = fk(rig, region, {**(base or {}), dof: a})
        q = apply(M[child_seg], art)
        pp = apply(M[parent_seg], Pp) if parent_seg else Pp
        d = cKDTree(pp).query(q)[0]
        out.append(f'{a:>4}°: median {np.median(d)*1000:4.1f} mm, 95% {np.percentile(d, 95)*1000:4.1f} mm')
    rep(f'{child_bone} vs {parent_bone} ({dof}, {len(art)} pts within {near*1000:.0f}mm): ' + ' | '.join(out))

rep('--- joint congruency (articular points of the moving bone -> partner surface) ---')
congruency('arm', 'ulna', 'Ulna.r', 'humerus', 'Humerus.r', 'el_flex', [0, 45, 90, 135])
congruency('arm', 'radius', 'Radius.r', 'humerus', 'Humerus.r', 'el_flex', [0, 45, 90, 135])
congruency('arm', 'radius', 'Radius.r', 'ulna', 'Ulna.r', 'pron', [0, 45, 90, 140])
congruency('arm', 'hand', 'Lunate bone.r', 'radius', 'Radius.r', 'wr_flex', [-60, -30, 0, 30, 70])
congruency('arm', 'humerus', 'Humerus.r', 'scapula', 'Scapula.r', 'sh_abd', [0, 60, 120, 170], near=0.006)
congruency('leg', 'femur', 'Femur.r', None, 'Hip bone.r', 'hip_flex', [0, 45, 90, 120])
congruency('leg', 'tibia', 'Tibia.r', 'femur', 'Femur.r', 'kn_flex', [0, 45, 90, 135], near=0.006)
congruency('leg', 'patella', 'Patella.r', 'femur', 'Femur.r', 'kn_flex', [0, 45, 90, 135], near=0.010)
congruency('leg', 'talus', 'Talus.r', 'tibia', 'Tibia.r', 'an_flex', [-20, 0, 25, 50])
congruency('leg', 'foot', 'Calcaneus.r', 'talus', 'Talus.r', 'inv', [-15, 0, 15, 30])

# ---------- collisions: moving bone getting inside a neighbour (points closer than 1 mm) ----------
def collide(region, seg_a, bone_a, seg_b, bone_b, dof, angles, base=None):
    A = pts(bone_a); Bp = pts(bone_b, 80000)
    out = []
    for a in angles:
        M = fk(rig, region, {**(base or {}), dof: a})
        qa = apply(M[seg_a], A)
        qb = apply(M[seg_b], Bp) if seg_b else Bp
        n = (cKDTree(qb).query(qa)[0] < 0.001).sum()
        out.append(f'{a}°:{n}')
    rep(f'collision pts {bone_a} vs {bone_b} ({dof}): ' + ' '.join(out))
rep('--- collision counts (sample points closer than 1 mm) ---')
collide('arm', 'humerus', 'Humerus.r', 'scapula', 'Scapula.r', 'sh_abd', [0, 60, 90, 120, 150, 180])
collide('arm', 'humerus', 'Humerus.r', 'scapula', 'Scapula.r', 'sh_flex', [0, 60, 90, 120, 150, 180])
collide('arm', 'scapula', 'Scapula.r', None, 'Second rib.r', 'sh_abd', [0, 90, 180])
collide('arm', 'ulna', 'Ulna.r', 'humerus', 'Humerus.r', 'el_flex', [0, 90, 145])
collide('leg', 'tibia', 'Tibia.r', 'femur', 'Femur.r', 'kn_flex', [0, 45, 90, 140])
collide('leg', 'femur', 'Femur.r', None, 'Hip bone.r', 'hip_flex', [0, 60, 90, 120])

open(f'{W}/kinematics_report.txt', 'w').write('\n'.join(report))
