import numpy as np
from scipy.spatial import cKDTree

rng = np.random.default_rng(0)

def sample_surface(v, t, n):
    """Area-weighted random points on a triangle mesh."""
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    p = area / area.sum()
    idx = rng.choice(len(t), size=n, p=p)
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    return (1 - s)[:, None] * a[idx] + (s * (1 - r2))[:, None] * b[idx] + (s * r2)[:, None] * c[idx]

def dense(m, n=60000):
    return np.vstack([m['v'], sample_surface(m['v'].astype(np.float64), m['t'], n)])

def sample_with_normals(v, t, n):
    v = v.astype(np.float64)
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    cr = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(cr, axis=1)
    keep = area > 0
    p = np.where(keep, area, 0) / area[keep].sum()
    idx = rng.choice(len(t), size=n, p=p)
    r1, r2 = rng.random(n), rng.random(n)
    s = np.sqrt(r1)
    pts = (1 - s)[:, None] * a[idx] + (s * (1 - r2))[:, None] * b[idx] + (s * r2)[:, None] * c[idx]
    nrm = cr[idx] / np.linalg.norm(cr[idx], axis=1, keepdims=True)
    # orient outward: majority of normals should point away from the centroid
    if np.mean(np.sum((pts - v.mean(0)) * nrm, axis=1)) < 0:
        nrm = -nrm
    return pts, nrm

class Surface:
    """Dense surface samples with normals; signed distance (negative = inside)."""
    def __init__(self, m, n=120000):
        self.p, self.n = sample_with_normals(m['v'], m['t'], n)
        self.tree = cKDTree(self.p)
    def transformed(self, M):
        s = Surface.__new__(Surface)
        s.p = self.p @ M[:3, :3].T + M[:3, 3]
        s.n = self.n @ M[:3, :3].T
        s.tree = cKDTree(s.p)
        return s
    def sdist(self, q, k=4):
        d, i = self.tree.query(q, k=k)
        # average the signed offsets along neighbouring normals for robustness
        off = np.einsum('ijk,ijk->ij', q[:, None, :] - self.p[i], self.n[i])
        sgn = np.sign(np.median(off, axis=1))
        return sgn * d[:, 0]

def sphere_fit(p):
    A = np.c_[2 * p, np.ones(len(p))]
    b = (p ** 2).sum(1)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = x[:3]
    r = np.sqrt(x[3] + c @ c)
    return c, r

def ransac_sphere(p, rmin, rmax, iters=4000, tol=0.0012):
    best = (None, None, -1)
    n = len(p)
    for _ in range(iters):
        s = p[rng.choice(n, 4, replace=False)]
        try:
            c, r = sphere_fit(s)
        except np.linalg.LinAlgError:
            continue
        if not (rmin <= r <= rmax) or not np.isfinite(r):
            continue
        inl = np.abs(np.linalg.norm(p - c, axis=1) - r) < tol
        k = inl.sum()
        if k > best[2]:
            best = (c, r, k)
    c, r, _ = best
    inl = np.abs(np.linalg.norm(p - c, axis=1) - r) < tol
    c, r = sphere_fit(p[inl])
    return c, r, inl.sum()

def circle_fit_axis(p, axis):
    """Project points on the plane perpendicular to `axis`, fit a circle; return 3D center (at mean along axis) and radius."""
    axis = axis / np.linalg.norm(axis)
    u = np.cross(axis, [0, 0, 1.0])
    if np.linalg.norm(u) < 1e-6:
        u = np.cross(axis, [0, 1.0, 0])
    u /= np.linalg.norm(u)
    w = np.cross(axis, u)
    q = np.c_[p @ u, p @ w]
    A = np.c_[2 * q, np.ones(len(q))]
    b = (q ** 2).sum(1)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    c2 = x[:2]
    r = np.sqrt(x[2] + c2 @ c2)
    along = (p @ axis).mean()
    return c2[0] * u + c2[1] * w + along * axis, r

def contact(pa, pb, d):
    """Points of pa within distance d of point set pb."""
    dist, _ = cKDTree(pb).query(pa, distance_upper_bound=d)
    return pa[np.isfinite(dist)]

def unit(x):
    x = np.asarray(x, float)
    return x / np.linalg.norm(x)

def rot(axis, ang):
    """Rotation matrix about unit axis by angle (radians), right-hand rule."""
    a = unit(axis)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K

def pca(p):
    c = p.mean(0)
    w, V = np.linalg.eigh(np.cov((p - c).T))
    return c, w[::-1], V[:, ::-1]   # descending variance
