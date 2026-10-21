"""Assemble the page.

site/dist/       committed and deployable as plain static files (e.g. GitHub Pages):
                 index.html, model.json, <name>.glb (meshopt, needs WebAssembly) and <name>.plain.glb (fallback)
build/artifact/  what is published as a Claude Artifact: the same page, but models as base64 text,
                 because the Artifact host does not serve .glb files.
                 Also _test.html / _test_nowasm.html for local headless tests (three.js from node_modules).
"""
import base64, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(HERE, 'dist')
ART = os.path.join(ROOT, 'build', 'artifact')
MODELS = ['overview', 'region_arm', 'region_leg']
os.makedirs(DIST, exist_ok=True)
os.makedirs(ART, exist_ok=True)

src = open(os.path.join(HERE, 'src', 'index.html')).read()
kin = open(os.path.join(HERE, 'src', 'kin.js')).read().replace('export function', 'function')
assert '/*__KIN__*/' in src and "'__ASSET_MODE__'" in src
page = src.replace('/*__KIN__*/', kin)

# The Artifact host wraps the page in this skeleton (doctype, charset, viewport, a small reset).
# Plain static hosting does not, so site/dist gets it written in; the local test pages use it too.
skel = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top);padding-bottom:env(safe-area-inset-bottom)}'
        'body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>')
open(os.path.join(DIST, 'index.html'), 'w').write(skel + page.replace("'__ASSET_MODE__'", "'glb'") + '</body></html>')
raw_model = os.path.join(ROOT, 'build', 'raw', 'model.json')
if os.path.exists(raw_model):
    shutil.copy(raw_model, os.path.join(DIST, 'model.json'))

art_page = page.replace("'__ASSET_MODE__'", "'b64'")
open(os.path.join(ART, 'index.html'), 'w').write(art_page)
shutil.copy(os.path.join(DIST, 'model.json'), os.path.join(ART, 'model.json'))
for m in MODELS:
    for suffix in ('', '.plain'):
        data = open(os.path.join(DIST, f'{m}{suffix}.glb'), 'rb').read()
        open(os.path.join(ART, f'{m}{suffix}.b64.txt'), 'w').write(base64.b64encode(data).decode())

# local test pages: local three.js and a debug hook for the screenshot scripts
dbg = ('window.__dbg = { camera, controls, state, scene, viewFor, enterRegion, pick, R: () => R, '
       'setAng: (a) => { Object.assign(state.ang, a); updatePose(); }, '
       'setView: (p, t) => { camTween = null; camera.position.set(...p); controls.target.set(...t); controls.update(); requestRender(); } };\n')
test = art_page.replace('https://cdn.jsdelivr.net/npm/three@0.169.0/', '/three/').replace('boot().catch(', dbg + 'boot().catch(')
csp = '<meta http-equiv="Content-Security-Policy" content="script-src \'self\' \'unsafe-inline\'">'
open(os.path.join(ART, '_test.html'), 'w').write(skel + test + '</body></html>')
open(os.path.join(ART, '_test_nowasm.html'), 'w').write(skel.replace('<head>', '<head>' + csp) + test + '</body></html>')
link = os.path.join(ART, 'three')
if not os.path.lexists(link):
    os.symlink(os.path.join(ROOT, 'node_modules', 'three'), link)
print('built: site/dist/index.html', os.path.getsize(os.path.join(DIST, 'index.html')) // 1024, 'KB; build/artifact ready')
