#!/usr/bin/env bash
# Full rebuild from the original Z-Anatomy models. About 20 minutes; needs Python 3.13 + requirements.txt and `npm install`.
# Generated data goes to build/ (ignored by git); deployable files to site/dist/; verification output to reports/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
B=build; mkdir -p $B/work $B/raw reports
GT="npx --no-install gltf-transform"
step() { echo; echo "== $1"; }

step "1/9 source models";        bash pipeline/fetch_source.sh
cd pipeline
step "2/9 import FBX (Blender)";  python3 import_fbx.py ../$B/source/SkeletalSystem100.fbx ../$B/source/MuscularSystem100.fbx ../$B/work/base.blend ../$B/work/catalog.json
                                 python3 dump_meshes.py ../$B/work/base.blend ../$B/work
step "3/9 joint centres + axes"; python3 joints.py
step "4/9 motion signs (first pass)"
                                 python3 rig.py ../$B/work/joints_raw.json
                                 python3 verify_kinematics.py --signs-only
step "5/9 refine pivots, knee rolling table"
                                 python3 refine.py
                                 python3 knee_track.py
step "6/9 final rig + joint checks"
                                 python3 rig.py
                                 python3 verify_kinematics.py | tee ../reports/kinematics.txt
step "7/9 bind muscles + length tests"
                                 python3 bind.py | tee ../reports/binding.txt
                                 python3 verify_muscles.py | tee ../reports/muscles.txt
                                 grep -q "^\([0-9]*\)/\1 expectations met" ../reports/muscles.txt || { echo "MUSCLE TESTS FAILED"; exit 1; }
step "8/9 export + compress";    python3 export.py
                                 python3 make_test_vectors.py
cd "$ROOT"
mkdir -p site/dist
$GT simplify $B/raw/overview.glb $B/raw/overview_s.glb --ratio 0.2 --error 0.0015
for pair in "overview_s:overview" "region_arm:region_arm" "region_leg:region_leg"; do
  src=${pair%%:*}; dst=${pair##*:}
  $GT meshopt  $B/raw/$src.glb site/dist/$dst.glb --level medium        # small, needs WebAssembly to decode
  $GT quantize $B/raw/$src.glb site/dist/$dst.plain.glb                 # larger fallback, no WebAssembly
done
step "9/9 JS = Python check, build page"
node site/src/test_kin.mjs
python3 site/build.py
echo; echo "done. reports/ has the checks; site/dist is deployable; build/artifact is what gets published as a Claude Artifact."
