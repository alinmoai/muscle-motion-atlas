import fs from 'fs';
import { fk, muscleLength, gaitAngles, mirrorX, apply } from './kin.js';
const model = JSON.parse(fs.readFileSync(new URL('../../build/raw/model.json', import.meta.url)));
const vec = JSON.parse(fs.readFileSync(new URL('../../build/raw/test_vectors.json', import.meta.url)));
let maxM = 0, maxL = 0, n = 0;
for (const v of vec) {
  const M = fk(model.rig, v.region, v.ang);
  for (const [s, ref] of Object.entries(v.M)) ref.forEach((x, i) => { maxM = Math.max(maxM, Math.abs(x - M[s][i])); });
  for (const [name, ref] of Object.entries(v.L)) {
    const L = muscleLength(model.regions[v.region].muscles[name], M, v.ang);
    maxL = Math.max(maxL, Math.abs(L - ref)); n++;
  }
}
console.log(`poses ${vec.length}, muscle lengths compared ${n}`);
console.log(`max matrix difference ${maxM.toExponential(2)}, max length difference ${(maxL * 1000).toFixed(6)} mm`);
// gait lookup: exact at the 1 % samples, halfway between them, and wrapping from 99 % back to 0 %
const g = model.regions.leg.gait;
let maxG = 0;
for (let i = 0; i < g.n; i++) {
  const j = (i + 1) % g.n;
  const at = gaitAngles(g, i / g.n), mid = gaitAngles(g, (i + 0.5) / g.n), wrapped = gaitAngles(g, 1 + i / g.n);
  for (const [k, v] of Object.entries(g.samples)) {
    maxG = Math.max(maxG, Math.abs(at[k] - v[i]), Math.abs(mid[k] - (v[i] + v[j]) / 2), Math.abs(wrapped[k] - v[i]));
  }
}
console.log(`gait lookup max difference ${maxG.toExponential(2)} over ${g.n} samples`);
// mirrored left leg: S·M·S applied to a mirrored point must equal the mirror of M applied to the point,
// and every muscle length must equal the right leg's (a mirror preserves distances)
let maxMir = 0, maxMirL = 0;
const mir = (p) => [-p[0], p[1], p[2]];
for (const v of vec.filter((x) => x.region === 'leg')) {
  const M = fk(model.rig, 'leg', v.ang), ML = mirrorX(M);
  for (const [name, m] of Object.entries(model.regions.leg.muscles)) {
    let L = 0, prev = null;
    for (const a of m.anchors) {
      const pl = apply(ML[a.seg], mir(a.p)), pr = mir(apply(M[a.seg], a.p));
      maxMir = Math.max(maxMir, Math.hypot(pl[0] - pr[0], pl[1] - pr[1], pl[2] - pr[2]));
      if (prev) L += Math.hypot(pl[0] - prev[0], pl[1] - prev[1], pl[2] - prev[2]);
      prev = pl;
    }
    if (m.wrap) L += m.wrap.sign * m.wrap.r * (((v.ang[m.wrap.dof] ?? 0) * Math.PI) / 180);
    maxMirL = Math.max(maxMirL, Math.abs(L - v.L[name]));
  }
}
console.log(`mirrored leg: max point difference ${maxMir.toExponential(2)} m, max length difference ${(maxMirL * 1000).toExponential(2)} mm`);
process.exit(maxM < 1e-9 && maxL < 1e-9 && maxG < 1e-9 && maxMir < 1e-9 && maxMirL < 1e-9 ? 0 : 1);
