"""Compute joint centres and axes for the right arm and right leg from bone geometry.
Coordinate frame of the model: +Z up, -Y anterior (front), -X = subject's right.
Every axis is oriented so that a POSITIVE angle about it (right-hand rule) gives the motion named
in `motions`; the sign is checked numerically in verify_kinematics.py, not assumed.
"""
import json, numpy as np
from scipy.spatial import cKDTree
from lib import load, W
from geom import dense, ransac_sphere, sphere_fit, circle_fit_axis, contact, unit, pca

B = load('bones')
P = {}
def pts(name, n=60000):
    if name not in P:
        P[name] = dense(B[name], n)
    return P[name]

J = {}
log = []
def note(*a):
    s = ' '.join(str(x) for x in a)
    log.append(s)
    print(s)

# ---------------- ARM ----------------
# Sternoclavicular / acromioclavicular: ends of the clavicle
C = pts('Clavicle.r')
sc = C[C[:, 0] > C[:, 0].max() - 0.008].mean(0)        # medial end (towards midline, +X)
ac = C[C[:, 0] < C[:, 0].min() + 0.008].mean(0)        # lateral end
J['SC'] = dict(center=sc)
J['AC'] = dict(center=ac)

# Glenohumeral: sphere fit of humeral head
H = pts('Humerus.r', 80000)
gh, ghr, _ = ransac_sphere(H[H[:, 2] > H[:, 2].max() - 0.05], 0.017, 0.032)
J['GH'] = dict(center=gh, radius=ghr)
note('GH', gh.round(4), 'r', round(ghr, 4))

# Scapular plane normal (smallest PCA component of scapula)
S = pts('Scapula.r')
_, _, Vs = pca(S)
scap_n = Vs[:, 2]
if scap_n[1] < 0:            # make it point backwards-ish (posterior, +Y)
    scap_n = -scap_n
J['scapula_normal'] = scap_n

# Pivot for scapular upward rotation. Rotating about the AC joint swings the inferior angle too far and
# lifts the scapula off the ribs; the real instantaneous centre moves from the root of the spine towards
# the AC joint during elevation, so use the midpoint of the two.
mb = S[S[:, 0] > S[:, 0].max() - 0.012]          # medial border strip (+X is medial on the right side)
sup_angle, inf_angle = mb[np.argmax(mb[:, 2])], mb[np.argmin(mb[:, 2])]
root_spine = sup_angle + 0.25 * (inf_angle - sup_angle)
J['root_spine'] = root_spine
J['scap_pivot'] = 0.5 * (ac + root_spine)
note('scapula pivot', J['scap_pivot'].round(4))

# Elbow: epicondyles give direction; articular contact gives centre
Hd = H[H[:, 2] < H[:, 2].min() + 0.05]
med_epi = Hd[np.argmax(Hd[:, 0])]
lat_epi = Hd[np.argmin(Hd[:, 0])]
U, R = pts('Ulna.r'), pts('Radius.r')
art = np.vstack([contact(Hd, U, 0.004), contact(Hd, R, 0.004)])
e_axis = unit(lat_epi - med_epi)           # points laterally (-X)
e_c, e_r = circle_fit_axis(art, e_axis)
J['elbow'] = dict(center=e_c, axis=e_axis, radius=e_r)
note('elbow centre', e_c.round(4), 'r', round(e_r, 4), 'axis', e_axis.round(3), 'contact pts', len(art))

# Forearm pronation axis: radial head centre -> ulnar head centre
_, _, Vr = pca(R)
r_long = unit(Vr[:, 0])
if r_long[2] < 0:
    r_long = -r_long
rh = R[R @ r_long > (R @ r_long).max() - 0.010]
rh_c, rh_r = circle_fit_axis(rh, r_long)
_, _, Vu = pca(U)
u_long = unit(Vu[:, 0])
if u_long[2] < 0:
    u_long = -u_long
uh = U[U @ u_long < (U @ u_long).min() + 0.012]
uh_c, uh_r = circle_fit_axis(uh, u_long)
J['pronation'] = dict(p0=rh_c, p1=uh_c, axis=unit(rh_c - uh_c))
note('radial head', rh_c.round(4), 'r', round(rh_r, 4), '| ulnar head', uh_c.round(4), 'r', round(uh_r, 4))

# Wrist: centre at head of capitate; flexion axis ulnar styloid -> radial styloid direction
Cap = pts('Capitate bone.r', 20000)
prox = np.vstack([contact(Cap, pts('Lunate bone.r', 20000), 0.003),
                  contact(Cap, pts('Scaphoid bone.r', 20000), 0.003)])
w_c, w_r = sphere_fit(prox)
rad_sty = R[np.argmin(R[:, 2])]
uln_sty = U[np.argmin(U[:, 2])]
fe = unit(rad_sty - uln_sty)               # lateral-ish
forearm = unit(e_c - w_c)                  # pointing proximally
fe = unit(fe - (fe @ forearm) * forearm)
dev = unit(np.cross(forearm, fe))
J['wrist'] = dict(center=w_c, fe_axis=fe, dev_axis=dev, forearm=forearm)
note('wrist centre', w_c.round(4), 'capitate head r', round(w_r, 4), 'contact pts', len(prox))

# ---------------- LEG ----------------
F = pts('Femur.r', 80000)
hip, hipr, _ = ransac_sphere(F[F[:, 2] > F[:, 2].max() - 0.06], 0.018, 0.032)
J['hip'] = dict(center=hip, radius=hipr)
note('hip', hip.round(4), 'r', round(hipr, 4))

Fd = F[F[:, 2] < F[:, 2].min() + 0.06]
med_fe = Fd[np.argmax(Fd[:, 0])]
lat_fe = Fd[np.argmin(Fd[:, 0])]
k_axis = unit(lat_fe - med_fe)
cond = Fd[Fd[:, 2] < Fd[:, 2].min() + 0.035]
post = cond[cond[:, 1] > np.median(cond[:, 1])]      # posterior half of the condyles (+Y)
k_c, k_r = circle_fit_axis(np.vstack([post, cond[cond[:, 2] < cond[:, 2].min() + 0.006]]), k_axis)
J['knee'] = dict(center=k_c, axis=k_axis, radius=k_r)
note('knee centre', k_c.round(4), 'r', round(k_r, 4), 'axis', k_axis.round(3))

T, Fi = pts('Tibia.r'), pts('Fibula.r')
mm = T[np.argmin(T[:, 2])]      # medial malleolus tip
lm = Fi[np.argmin(Fi[:, 2])]    # lateral malleolus tip
a_axis = unit(lm - mm)
a_c = 0.5 * (mm + lm)
J['ankle'] = dict(center=a_c, axis=a_axis, medial_malleolus=mm, lateral_malleolus=lm)
note('ankle', a_c.round(4), 'axis', a_axis.round(3), 'MM', mm.round(3), 'LM', lm.round(3))

# Foot long axis: posterior calcaneus -> head of 2nd metatarsal
Ca = pts('Calcaneus.r')
heel = Ca[np.argmax(Ca[:, 1])]
mt2 = pts('Second metatarsal bone.r', 20000)
mt2_head = mt2[mt2[:, 1] < mt2[:, 1].min() + 0.01].mean(0)
foot_long = unit(mt2_head - heel)             # anterior
up = np.array([0, 0, 1.0])
lat_dir = unit(np.cross(foot_long, up))       # for right foot: points to subject's right? (checked below)
if lat_dir[0] > 0:
    lat_dir = -lat_dir                        # make it point to subject's right (-X) = lateral for right foot
# Subtalar axis (Inman): 42 deg up from horizontal, 23 deg medial from the long axis, through the talus
med_dir = -lat_dir
horiz = unit(np.cos(np.radians(23)) * foot_long + np.sin(np.radians(23)) * med_dir)
st_axis = unit(np.cos(np.radians(42)) * horiz + np.sin(np.radians(42)) * up)
Ta = pts('Talus.r')
st_c = Ta.mean(0)
J['subtalar'] = dict(center=st_c, axis=st_axis, foot_long=foot_long)
note('subtalar centre', st_c.round(4), 'axis', st_axis.round(3), 'foot long', foot_long.round(3))

# MTP: through heads of 1st and 5th metatarsals
def mt_head(name):
    m = pts(name, 20000)
    d = m @ foot_long
    head = m[d > d.max() - 0.012]
    c, r = sphere_fit(head)
    return c, r
h1, r1 = mt_head('First metatarsal bone.r')
h5, r5 = mt_head('Fifth metatarsal bone.r')
J['mtp'] = dict(p1=h1, p5=h5, center=0.5 * (h1 + h5), axis=unit(h1 - h5))
note('MTP heads', h1.round(4), round(r1, 4), h5.round(4), round(r5, 4))

out = {k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()} if isinstance(v, dict) else v.tolist()
       for k, v in J.items()}
json.dump(out, open(f'{W}/joints_raw.json', 'w'), indent=1)
