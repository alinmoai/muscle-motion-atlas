"""Build the rig definition (single source of truth for Python verification AND the web viewer).

Segments are rigid groups of bones. Each segment's transform is computed from its parent with
rotations about pivots/axes expressed in the REST world frame, so axes travel with the parent.
Sign conventions are set by the `sign` field after numerical verification (verify_kinematics.py).
"""
import json, sys, numpy as np
from lib import W
from geom import unit

J = {k: {kk: (np.array(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()} if isinstance(v, dict) else np.array(v)
     for k, v in json.load(open(sys.argv[1] if len(sys.argv) > 1 else f'{W}/joints_refined.json')).items()}
# The first pass runs on joints_raw.json, only to fix motion signs for refine.py / knee_track.py;
# the refined-only entries then fall back to their raw equivalents.
J.setdefault('radiocarpal', dict(center=J['wrist']['center']))

def L(x):
    return [round(float(a), 6) for a in x]

CARPUS = ['Scaphoid bone.r', 'Lunate bone.r', 'Triquetrum bone.r', 'Pisiform bone.r']
HAND = ['Trapezium bone.r', 'Trapezoid bone.r', 'Capitate bone.r', 'Hamate bone.r'] + \
       [f'{o} metacarpal bone.r' for o in ['First', 'Second', 'Third', 'Fourth', 'Fifth']] + \
       [f'{p} phalanx of {f} finger of hand.r' for p in ['Proximal', 'Distal'] for f in ['first', 'second', 'third', 'fourth', 'fifth']] + \
       [f'Middle phalanx of {f} finger of hand.r' for f in ['second', 'third', 'fourth', 'fifth']]
FOOT = ['Calcaneus.r', 'Navicular bone.r', 'Cuboid bone.r', 'Medial cuneiform bone.r', 'Intermediate cuneiform bone.r',
        'Lateral cuneiform bone.r', 'Sesamoid bones of foot.r'] + \
       [f'{o} metatarsal bone.r' for o in ['First', 'Second', 'Third', 'Fourth', 'Fifth']]
TOES = [f'{p} phalanx of {f} finger of foot.r' for p in ['Proximal', 'Distal'] for f in ['first', 'second', 'third', 'fourth', 'fifth']] + \
       [f'Middle phalanx of {f} finger of foot.r' for f in ['second', 'third', 'fourth', 'fifth']]

X = np.array([1.0, 0, 0]); Y = np.array([0, 1.0, 0]); Z = np.array([0, 0, 1.0])
hum_long = unit(J['GH']['center'] - J['elbow']['center'])         # proximal
fem_long = unit(J['hip']['center'] - J['knee']['center'])         # proximal
clav_elev_axis = unit(np.cross(J['AC']['center'] - J['SC']['center'], Z))   # horizontal, perpendicular to clavicle

rig = {
  'frame': 'Z up, -Y anterior, -X subject right; metres',
  'regions': {
    'arm': {
      'title': '手臂與肩胛骨',
      'root_bones': 'axial',     # trunk is static
      'segments': {
        'clavicle': dict(parent=None, bones=['Clavicle.r']),
        'scapula':  dict(parent='clavicle', bones=['Scapula.r']),
        'humerus':  dict(parent='scapula', bones=['Humerus.r']),
        'ulna':     dict(parent='humerus', bones=['Ulna.r']),
        'radius':   dict(parent='ulna', bones=['Radius.r']),
        'carpus':   dict(parent='radius', bones=CARPUS),
        'hand':     dict(parent='carpus', bones=HAND),
      },
      'joints': {
        'clavicle': dict(type='coupled', pivot=L(J['SC']['center']), axis=L(clav_elev_axis)),
        'scapula':  dict(type='coupled', pivot=L(J['scap_pivot']), axis=L(J['scapula_normal'])),
        'humerus':  dict(type='ball_world', pivot=L(J['GH']['center']),
                         dofs=[dict(id='sh_flex', axis=L(X)), dict(id='sh_abd', axis=L(Y)), dict(id='sh_rot', axis=L(hum_long))]),
        'ulna':     dict(type='hinge', pivot=L(J['elbow']['center']), dofs=[dict(id='el_flex', axis=L(J['elbow']['axis']))]),
        'radius':   dict(type='hinge', pivot=L(J['pronation']['p0']), dofs=[dict(id='pron', axis=L(J['pronation']['axis']))]),
        'carpus':   dict(type='hinge', pivot=L(J['radiocarpal']['center']),
                         dofs=[dict(id='wr_flex', axis=L(J['wrist']['fe_axis']), frac=0.5), dict(id='wr_dev', axis=L(J['wrist']['dev_axis']), frac=0.5)]),
        'hand':     dict(type='hinge', pivot=L(J['wrist']['center']),
                         dofs=[dict(id='wr_flex', axis=L(J['wrist']['fe_axis']), frac=0.5), dict(id='wr_dev', axis=L(J['wrist']['dev_axis']), frac=0.5)]),
      },
      'rhythm': dict(scapula_per_deg=1/3, clavicle_per_deg=0.06, humerus_rest_dir=L(-hum_long)),
      'dofs': [
        dict(id='sh_flex', label='肩 屈曲／伸展', min=-50, max=180, neg='伸展', pos='屈曲（往前抬）'),
        dict(id='sh_abd',  label='肩 外展',       min=0,   max=180, pos='外展（往旁邊抬）'),
        dict(id='sh_rot',  label='肩 內旋／外旋', min=-60, max=80,  neg='外旋', pos='內旋'),
        dict(id='el_flex', label='肘 屈曲',       min=0,   max=145, pos='屈曲'),
        dict(id='pron',    label='前臂 旋前',     min=-10, max=150, neg='旋後', pos='旋前（掌心轉向後）'),
        dict(id='wr_flex', label='腕 屈曲／伸展', min=-70, max=80,  neg='伸展（手背翹）', pos='屈曲'),
        dict(id='wr_dev',  label='腕 橈偏／尺偏', min=-20, max=35,  neg='橈偏（往拇指側）', pos='尺偏（往小指側）'),
      ],
    },
    'leg': {
      'title': '單腳到腳掌',
      'root_bones': 'axial',
      'segments': {
        'femur':   dict(parent=None, bones=['Femur.r']),
        'patella': dict(parent='femur', bones=['Patella.r']),
        'tibia':   dict(parent='femur', bones=['Tibia.r', 'Fibula.r']),
        'talus':   dict(parent='tibia', bones=['Talus.r']),
        'foot':    dict(parent='talus', bones=FOOT),
        'toes':    dict(parent='foot', bones=TOES),
      },
      'joints': {
        'femur':   dict(type='ball_world', pivot=L(J['hip']['center']),
                        dofs=[dict(id='hip_flex', axis=L(X)), dict(id='hip_abd', axis=L(Y)), dict(id='hip_rot', axis=L(fem_long))]),
        'patella': dict(type='coupled', pivot=L(J['knee']['center']), axis=L(J['knee']['axis'])),
        'tibia':   dict(type='hinge', pivot=L(J['knee']['center']), dofs=[dict(id='kn_flex', axis=L(J['knee']['axis']))],
                        **(dict(track=dict(theta=np.asarray(J['knee_track']['theta']).tolist(), shift=np.asarray(J['knee_track']['shift']).tolist(),
                                           u=L(J['knee_track']['u']), w=L(J['knee_track']['w']))) if 'knee_track' in J else {})),
        'talus':   dict(type='hinge', pivot=L(J['ankle']['center']), dofs=[dict(id='an_flex', axis=L(J['ankle']['axis']))]),
        'foot':    dict(type='hinge', pivot=L(J['subtalar']['center']), dofs=[dict(id='inv', axis=L(J['subtalar']['axis']))]),
        'toes':    dict(type='hinge', pivot=L(J['mtp']['center']), dofs=[dict(id='toe', axis=L(J['mtp']['axis']))]),
      },
      'dofs': [
        dict(id='hip_flex', label='髖 屈曲／伸展', min=-20, max=120, neg='伸展', pos='屈曲（抬腿）'),
        dict(id='hip_abd',  label='髖 外展／內收', min=-20, max=45,  neg='內收', pos='外展'),
        dict(id='hip_rot',  label='髖 內旋／外旋', min=-45, max=40,  neg='外旋', pos='內旋'),
        dict(id='kn_flex',  label='膝 屈曲',       min=0,   max=120, pos='屈曲'),
        dict(id='an_flex',  label='踝 背屈／蹠屈', min=-20, max=50,  neg='背屈（勾腳）', pos='蹠屈（踮腳）'),
        dict(id='inv',      label='足 內翻／外翻', min=-15, max=30,  neg='外翻', pos='內翻'),
        dict(id='toe',      label='腳趾 伸／屈',   min=-40, max=70,  neg='屈（抓地）', pos='伸（往上翹）'),
      ],
    },
  },
  'signs': {},   # filled by verify_kinematics.py   # filled by verify_kinematics.py: dof id -> +1/-1 so that positive slider = named motion
}
json.dump(rig, open(f'{W}/rig.json', 'w'), indent=1, ensure_ascii=False)
print('rig written')
