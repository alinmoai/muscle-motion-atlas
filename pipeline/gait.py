"""Normal walking for the right leg: sagittal joint angles over one gait cycle.

The keyframes follow the phase values given in two teaching handouts on normal gait:
  University of Missouri PM&R, "Normal Gait"
  (https://medicine.missouri.edu/sites/default/files/pm-r/Normal_Gait.pdf)
  Newcastle FRCS revision, "Normal gait"
  (https://lists.ncl.ac.uk/wws/d_read/orthnorth/Basic%20Science%202013/Normal%20gait%20-%20FRCS%20revision.pdf)
Values they give: stance 0-60 %, swing 60-100 %; at initial contact hip 30 deg flexion, knee 5 deg,
ankle neutral; knee flexes to 15-20 deg in loading response and is least flexed around 40 %;
hip reaches maximum extension at 50 % and maximum flexion (~30 deg) at the end of mid swing;
ankle dorsiflexes to ~15 deg in terminal stance and plantarflexes ~20 deg in pre-swing;
knee flexion peaks at ~60 deg at the end of initial swing. Cadence 80-110 steps/min.

The curve between keyframes is a shape-preserving (PCHIP) interpolation, sampled every 1 %. It is a typical
healthy adult at normal speed, not a measurement of anyone. Only the sagittal plane is modelled:
hip ab/adduction, hip rotation and subtalar motion stay at 0, and the pelvis does not move.
"""
import numpy as np
from scipy.interpolate import PchipInterpolator

N = 100   # samples per cycle (every 1 %)

# percent of cycle -> degrees, in the slider convention of rig.json:
# hip_flex + = flexion, kn_flex + = flexion, an_flex + = plantarflexion, toe + = MTP extension
KEYS = {
    'hip_flex': [(0, 30), (10, 28), (30, 10), (50, -10), (62, 0), (75, 22), (87, 32), (100, 30)],
    'kn_flex':  [(0, 5), (15, 18), (40, 5), (50, 10), (62, 38), (73, 62), (87, 30), (97, 5), (100, 5)],
    'an_flex':  [(0, 0), (7, 7), (25, -4), (48, -12), (62, 18), (75, 3), (87, -1), (100, 0)],
    # toe extension rises as the heel lifts in terminal stance, peaks at toe-off; mild extension in swing
    'toe':      [(0, 8), (12, 2), (35, 2), (50, 25), (60, 45), (70, 20), (82, 10), (100, 8)],
}

PHASES = [  # start %, end %, Rancho Los Amigos name, Chinese
    (0, 3, 'Initial contact', '初始著地'),
    (3, 10, 'Loading response', '承重反應期'),
    (10, 30, 'Mid stance', '站立中期'),
    (30, 50, 'Terminal stance', '站立末期'),
    (50, 60, 'Pre-swing', '擺盪前期'),
    (60, 73, 'Initial swing', '擺盪初期'),
    (73, 87, 'Mid swing', '擺盪中期'),
    (87, 100, 'Terminal swing', '擺盪末期'),
]


def gait_table(rig):
    """Joint angles at 0, 1, ..., 99 % of the cycle, clipped to each slider's range."""
    rng = {d['id']: (d['min'], d['max']) for d in rig['regions']['leg']['dofs']}
    x = np.arange(N)
    samples = {}
    for dof, keys in KEYS.items():
        px, py = zip(*keys)
        assert px[0] == 0 and px[-1] == 100 and py[0] == py[-1], dof
        # shape-preserving (PCHIP), so the curve never overshoots a keyframe; one cycle is copied on
        # each side so the joins at 0 / 100 % are smooth
        ex = np.concatenate([np.array(px[:-1]) - 100, px, np.array(px[1:]) + 100])
        ey = np.concatenate([py[:-1], py, py[1:]])
        s = PchipInterpolator(ex, ey)(x)
        lo, hi = rng[dof]
        samples[dof] = [round(float(v), 3) for v in np.clip(s, lo, hi)]
    return dict(n=N, samples=samples, stance_pct=60,
                phases=[dict(start=a, end=b, en=en, zh=zh) for a, b, en, zh in PHASES],
                real_cycle_s=[round(2 * 60 / 110, 2), round(2 * 60 / 80, 2)])


def poses(table):
    """One angle dict per sample, other leg sliders at 0."""
    return [{k: v[i] for k, v in table['samples'].items()} for i in range(table['n'])]


if __name__ == '__main__':
    import json
    from lib import W
    t = gait_table(json.load(open(f'{W}/rig.json')))
    for k, v in t['samples'].items():
        v = np.array(v)
        print(f'{k:<9} min {v.min():6.1f} at {v.argmin():>2}%   max {v.max():6.1f} at {v.argmax():>2}%')
