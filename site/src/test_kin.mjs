import fs from 'fs';
import { fk, muscleLength, gaitAngles } from './kin.js';
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
process.exit(maxM < 1e-9 && maxL < 1e-9 && maxG < 1e-9 ? 0 : 1);
