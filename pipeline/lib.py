import json, numpy as np, os
# all generated data lives in <repo>/build (git-ignored)
BUILD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'build'))
W = os.path.join(BUILD, 'work')
os.makedirs(W, exist_ok=True)
_cache = {}
def load(kind):
    if kind not in _cache:
        z = np.load(f'{W}/{kind}.npz')
        d = {}
        for k in z.files:
            n, part = k.rsplit('|', 1)
            d.setdefault(n, {})[part] = z[k]
        _cache[kind] = d
    return _cache[kind]
def meta():
    return json.load(open(f'{W}/meta.json'))
