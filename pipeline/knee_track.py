"""Knee 'rolling' track: a fixed hinge cannot follow the femoral condyles, so for each flexion angle
we add a small translation of the tibia (in the sagittal plane) that keeps the plateau at the rest gap
without sinking into the femur. Stored as a lookup table used by both Python and the viewer.
"""
import json, itertools, numpy as np
from lib import load, W
from geom import Surface, unit, rot

B = load('bones')
J = json.load(open(f'{W}/joints_refined.json'))
signs = json.load(open(f'{W}/rig.json'))['signs']
fem = Surface(B['Femur.r'], 150000)
tib = Surface(B['Tibia.r'], 80000)
d, _ = fem.tree.query(tib.p)
kc, ax = np.array(J['knee']['center']), unit(J['knee']['axis'])
art = tib.p[(d < 0.008) & (tib.p[:, 2] > kc[2] - 0.05)]
art = art[np.random.default_rng(2).choice(len(art), min(3000, len(art)), replace=False)]
med0 = np.median(fem.sdist(art))
u = unit(np.cross(ax, [0, 0, 1.0])); w = np.cross(ax, u)      # sagittal-plane basis (u ~ anterior/posterior, w ~ vertical)

# Solved up to 110 deg. Beyond that a fixed hinge plus a sliding offset cannot avoid the femoral condyles
# (10-14 % of contact points penetrate whatever the shift), so the slider stops at 120 and 120 reuses the
# 110 deg shift.
thetas = list(range(0, 115, 10))
track = []
prev = np.zeros(2)
for th in thetas:
    R = rot(ax, np.radians(signs['kn_flex'] * th))
    q0 = (art - kc) @ R.T + kc
    best = None
    grid = np.arange(-0.008, 0.0081, 0.001)
    for a, b in itertools.product(grid + prev[0], grid + prev[1]):
        q = q0 + a * u + b * w
        sd = fem.sdist(q)
        f = (np.median(sd) - med0) ** 2 * 1e6 + 60 * np.mean(sd < -0.0008) + 0.02 * ((a - prev[0]) ** 2 + (b - prev[1]) ** 2) * 1e6
        if best is None or f < best[0]:
            best = (f, a, b, np.median(sd), np.mean(sd < -0.0008))
    prev = np.array(best[1:3])
    track.append([round(float(best[1]), 5), round(float(best[2]), 5)])
    print(f'{th:>3}°  shift ({best[1]*1000:5.1f}, {best[2]*1000:5.1f}) mm  gap {best[3]*1000:4.1f} mm (rest {med0*1000:.1f})  pen {best[4]*100:4.1f}%')

thetas.append(120); track.append(list(track[-1]))
J['knee_track'] = dict(theta=thetas, shift=track, u=u.tolist(), w=w.tolist())
json.dump(J, open(f'{W}/joints_refined.json', 'w'), indent=1)
