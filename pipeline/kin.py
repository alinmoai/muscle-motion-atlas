"""Forward kinematics for the rig (mirrors the JavaScript implementation in the viewer)."""
import json, numpy as np
from lib import W
from geom import rot, unit

def T(p):
    M = np.eye(4); M[:3, 3] = p; return M

def Rm(axis, deg):
    M = np.eye(4); M[:3, :3] = rot(axis, np.radians(deg)); return M

def about(pivot, axis, deg):
    p = np.asarray(pivot, float)
    return T(p) @ Rm(axis, deg) @ T(-p)

def load_rig():
    return json.load(open(f'{W}/rig.json'))

def fk(rig, region, ang):
    """ang: dof id -> slider degrees. Returns segment -> 4x4 (rest world -> current world)."""
    R = rig['regions'][region]
    S = rig.get('signs', {})
    s = lambda k: S.get(k, 1) * ang.get(k, 0.0)
    J = R['joints']
    M = {}
    if region == 'arm':
        jh = J['humerus']
        ax = {d['id']: d['axis'] for d in jh['dofs']}
        Q = Rm(ax['sh_flex'], s('sh_flex')) @ Rm(ax['sh_abd'], s('sh_abd')) @ Rm(ax['sh_rot'], s('sh_rot'))
        rest = np.array(R['rhythm']['humerus_rest_dir'])
        cur = Q[:3, :3] @ rest
        e = np.degrees(np.arccos(np.clip(cur @ rest, -1, 1)))
        a = R['rhythm']['clavicle_per_deg'] * e
        U = R['rhythm']['scapula_per_deg'] * e
        M['clavicle'] = about(J['clavicle']['pivot'], J['clavicle']['axis'], S.get('clav_elev', 1) * a)
        M['scapula'] = M['clavicle'] @ about(J['scapula']['pivot'], J['scapula']['axis'], S.get('scap_up', 1) * (U - a))
        gh = np.asarray(jh['pivot'])
        gh_cur = (M['scapula'] @ np.r_[gh, 1])[:3]
        M['humerus'] = T(gh_cur) @ Q @ T(-gh)
        for seg in ['ulna', 'radius', 'carpus', 'hand']:
            j = J[seg]
            L = np.eye(4)
            for d in j['dofs']:
                L = L @ about(j['pivot'], d['axis'], d.get('frac', 1.0) * s(d['id']))
            M[seg] = M[R['segments'][seg]['parent']] @ L
        M['_elev'] = e
    else:
        jf = J['femur']
        L = np.eye(4)
        for d in jf['dofs']:
            L = L @ about(jf['pivot'], d['axis'], s(d['id']))
        M['femur'] = L
        for seg in ['tibia', 'talus', 'foot', 'toes']:
            j = J[seg]
            L = np.eye(4)
            for d in j['dofs']:
                L = L @ about(j['pivot'], d['axis'], d.get('frac', 1.0) * s(d['id']))
            tr = j.get('track')
            if tr:
                th = abs(ang.get('kn_flex', 0.0))
                a = np.interp(th, tr['theta'], [x[0] for x in tr['shift']])
                b = np.interp(th, tr['theta'], [x[1] for x in tr['shift']])
                L = T(a * np.array(tr['u']) + b * np.array(tr['w'])) @ L
            M[seg] = M[R['segments'][seg]['parent']] @ L
        # patella: rotates about the knee axis by a fraction of knee flexion, then slides towards the axis
        jp = J['patella']
        kn = s('kn_flex')
        pt = rig.get('patella_track')
        if pt:
            th = np.array(pt['theta']); dl = np.array(pt['delta']); fr = pt['fraction']
            delta = np.interp(abs(kn), th, dl)
            out = np.array(pt['u_out'])
            M['patella'] = M['femur'] @ about(jp['pivot'], jp['axis'], fr * kn) @ T(-delta * out)
        else:
            M['patella'] = M['femur'] @ about(jp['pivot'], jp['axis'], 0.7 * kn)
    return M

def apply(M, p):
    p = np.asarray(p, float)
    return p @ M[:3, :3].T + M[:3, 3]
