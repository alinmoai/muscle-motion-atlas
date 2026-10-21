// Forward kinematics and muscle length. Mirrors pipe/kin.py; checked against it in test_kin.mjs.
// Matrices are row-major arrays of 16 numbers (M[r*4+c]); points are [x, y, z] in metres.
// Frame: +Z up, -Y anterior, -X = subject's right.

const I4 = () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

export function mul(a, b) {
  const o = new Array(16).fill(0);
  for (let r = 0; r < 4; r++)
    for (let c = 0; c < 4; c++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[r * 4 + k] * b[k * 4 + c];
      o[r * 4 + c] = s;
    }
  return o;
}

export function T(p) {
  const m = I4();
  m[3] = p[0]; m[7] = p[1]; m[11] = p[2];
  return m;
}

function unit(a) {
  const n = Math.hypot(a[0], a[1], a[2]);
  return [a[0] / n, a[1] / n, a[2] / n];
}

// rotation about a unit axis, right-hand rule (Rodrigues)
export function Rm(axis, deg) {
  const [x, y, z] = unit(axis);
  const t = (deg * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t), C = 1 - c;
  return [
    c + x * x * C, x * y * C - z * s, x * z * C + y * s, 0,
    y * x * C + z * s, c + y * y * C, y * z * C - x * s, 0,
    z * x * C - y * s, z * y * C + x * s, c + z * z * C, 0,
    0, 0, 0, 1,
  ];
}

export function about(p, axis, deg) {
  return mul(mul(T(p), Rm(axis, deg)), T([-p[0], -p[1], -p[2]]));
}

export function apply(M, p) {
  return [
    M[0] * p[0] + M[1] * p[1] + M[2] * p[2] + M[3],
    M[4] * p[0] + M[5] * p[1] + M[6] * p[2] + M[7],
    M[8] * p[0] + M[9] * p[1] + M[10] * p[2] + M[11],
  ];
}

function interp(x, xs, ys) {
  if (x <= xs[0]) return ys[0];
  for (let i = 1; i < xs.length; i++) {
    if (x <= xs[i]) {
      const f = (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
      return ys[i - 1] + f * (ys[i] - ys[i - 1]);
    }
  }
  return ys[ys.length - 1];
}

// rig: model.rig ; region: 'arm' | 'leg' ; ang: { dofId: sliderDegrees }
// returns { segment: 4x4 } mapping rest-pose world coordinates to current world coordinates
export function fk(rig, region, ang) {
  const R = rig.regions[region];
  const S = rig.signs || {};
  const s = (k) => (S[k] ?? 1) * (ang[k] ?? 0);
  const J = R.joints;
  const M = {};
  const chainSeg = (seg) => {
    const j = J[seg];
    let L = I4();
    for (const d of j.dofs) L = mul(L, about(j.pivot, d.axis, (d.frac ?? 1) * s(d.id)));
    if (j.track) {
      const th = Math.abs(ang.kn_flex ?? 0);
      const a = interp(th, j.track.theta, j.track.shift.map((x) => x[0]));
      const b = interp(th, j.track.theta, j.track.shift.map((x) => x[1]));
      const u = j.track.u, w = j.track.w;
      L = mul(T([a * u[0] + b * w[0], a * u[1] + b * w[1], a * u[2] + b * w[2]]), L);
    }
    M[seg] = mul(M[R.segments[seg].parent], L);
  };
  if (region === 'arm') {
    const jh = J.humerus;
    const ax = Object.fromEntries(jh.dofs.map((d) => [d.id, d.axis]));
    const Q = mul(mul(Rm(ax.sh_flex, s('sh_flex')), Rm(ax.sh_abd, s('sh_abd'))), Rm(ax.sh_rot, s('sh_rot')));
    const rest = R.rhythm.humerus_rest_dir;
    const cur = apply(Q, rest);
    const dot = Math.min(1, Math.max(-1, cur[0] * rest[0] + cur[1] * rest[1] + cur[2] * rest[2]));
    const e = (Math.acos(dot) * 180) / Math.PI;
    const a = R.rhythm.clavicle_per_deg * e;
    const U = R.rhythm.scapula_per_deg * e;
    M.clavicle = about(J.clavicle.pivot, J.clavicle.axis, (S.clav_elev ?? 1) * a);
    M.scapula = mul(M.clavicle, about(J.scapula.pivot, J.scapula.axis, (S.scap_up ?? 1) * (U - a)));
    const g = jh.pivot;
    const gc = apply(M.scapula, g);
    M.humerus = mul(mul(T(gc), Q), T([-g[0], -g[1], -g[2]]));
    for (const seg of ['ulna', 'radius', 'carpus', 'hand']) chainSeg(seg);
    M._elev = e;
  } else {
    const jf = J.femur;
    let L = I4();
    for (const d of jf.dofs) L = mul(L, about(jf.pivot, d.axis, s(d.id)));
    M.femur = L;
    for (const seg of ['tibia', 'talus', 'foot', 'toes']) chainSeg(seg);
    const jp = J.patella, kn = s('kn_flex'), pt = rig.patella_track;
    const delta = interp(Math.abs(kn), pt.theta, pt.delta);
    const o = pt.u_out;
    M.patella = mul(mul(M.femur, about(jp.pivot, jp.axis, pt.fraction * kn)), T([-delta * o[0], -delta * o[1], -delta * o[2]]));
  }
  M.trunk = I4();
  return M;
}

// length of one muscle (metres) along its anchor path in the current pose
export function muscleLength(m, M, ang) {
  let L = 0, prev = null;
  for (const a of m.anchors) {
    const p = apply(M[a.seg], a.p);
    if (prev) L += Math.hypot(p[0] - prev[0], p[1] - prev[1], p[2] - prev[2]);
    prev = p;
  }
  if (m.wrap) L += m.wrap.sign * m.wrap.r * (((ang[m.wrap.dof] ?? 0) * Math.PI) / 180);
  return L;
}

// a muscle shows a length change only if its anchors sit on at least two different segments
export function measurable(m) {
  return m.kind === 'muscle' && new Set(m.anchors.map((a) => a.seg)).size >= 2;
}

// joint angles at a point of the gait cycle (phase 0..1), linear between the 1 % samples, wrapping at 100 %
export function gaitAngles(gait, phase) {
  const n = gait.n;
  const x = (((phase % 1) + 1) % 1) * n;
  const i = Math.floor(x) % n, j = (i + 1) % n, f = x - Math.floor(x);
  const out = {};
  for (const [k, v] of Object.entries(gait.samples)) out[k] = v[i] + (v[j] - v[i]) * f;
  return out;
}
