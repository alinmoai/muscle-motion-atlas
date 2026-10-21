"""Minimal glTF 2.0 (GLB) writer for static and skinned triangle meshes."""
import json, struct, numpy as np

class GLB:
    def __init__(self):
        self.bin = bytearray()
        self.g = dict(asset=dict(version='2.0', generator='anatomy-pipeline'), scene=0, scenes=[dict(nodes=[])],
                      nodes=[], meshes=[], accessors=[], bufferViews=[], buffers=[], materials=[dict(name='default')])

    def _view(self, arr, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin)
        b = np.ascontiguousarray(arr).tobytes()
        self.bin += b
        v = dict(buffer=0, byteOffset=off, byteLength=len(b))
        if target:
            v['target'] = target
        self.g['bufferViews'].append(v)
        return len(self.g['bufferViews']) - 1

    def _acc(self, arr, ctype, typ, target=None, minmax=False, normalized=False):
        bv = self._view(arr, target)
        a = dict(bufferView=bv, componentType=ctype, count=int(arr.shape[0]), type=typ)
        if minmax:
            a['min'] = [float(x) for x in arr.min(0)]
            a['max'] = [float(x) for x in arr.max(0)]
        if normalized:
            a['normalized'] = True
        self.g['accessors'].append(a)
        return len(self.g['accessors']) - 1

    def node(self, name, parent=None, mesh=None, skin=None, extras=None):
        n = dict(name=name)
        if mesh is not None:
            n['mesh'] = mesh
        if skin is not None:
            n['skin'] = skin
        if extras:
            n['extras'] = extras
        self.g['nodes'].append(n)
        i = len(self.g['nodes']) - 1
        if parent is None:
            self.g['scenes'][0]['nodes'].append(i)
        else:
            self.g['nodes'][parent].setdefault('children', []).append(i)
        return i

    def mesh(self, name, v, t, n, joints=None, weights=None):
        v = np.asarray(v, np.float32); n = np.asarray(n, np.float32)
        t = np.asarray(t)
        idx = t.reshape(-1).astype(np.uint16 if v.shape[0] < 65536 else np.uint32)
        attrs = dict(POSITION=self._acc(v, 5126, 'VEC3', 34962, minmax=True),
                     NORMAL=self._acc(n, 5126, 'VEC3', 34962))
        if joints is not None:
            attrs['JOINTS_0'] = self._acc(np.asarray(joints, np.uint8), 5121, 'VEC4', 34962)
            attrs['WEIGHTS_0'] = self._acc(np.asarray(weights, np.float32), 5126, 'VEC4', 34962)
        ind = self._acc(idx, 5123 if idx.dtype == np.uint16 else 5125, 'SCALAR', 34963)
        self.g['meshes'].append(dict(name=name, primitives=[dict(attributes=attrs, indices=ind, material=0)]))
        return len(self.g['meshes']) - 1

    def skin(self, joint_nodes, name='rig'):
        ibm = np.tile(np.eye(4, dtype=np.float32).reshape(1, 16), (len(joint_nodes), 1))
        acc = self._acc(ibm, 5126, 'MAT4')
        self.g.setdefault('skins', []).append(dict(name=name, joints=joint_nodes, inverseBindMatrices=acc))
        return len(self.g['skins']) - 1

    def save(self, path):
        while len(self.bin) % 4:
            self.bin.append(0)
        self.g['buffers'] = [dict(byteLength=len(self.bin))]
        js = json.dumps(self.g, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        while len(js) % 4:
            js += b' '
        out = bytearray()
        out += struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin))
        out += struct.pack('<II', len(js), 0x4E4F534A) + js
        out += struct.pack('<II', len(self.bin), 0x004E4942) + self.bin
        open(path, 'wb').write(out)
