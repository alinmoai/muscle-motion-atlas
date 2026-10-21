"""Regression test for ping-pong playback (headless Chromium, needs build/artifact).
1. press play while standing in the preset pose -> the limb starts moving at once
2. switch preset during playback -> playback continues with the new movement
3. walking loops through the gait cycle; the cycle scrubber pauses and resumes it
usage: python3 site/test/playback.py"""
import os, threading, http.server, functools, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'artifact')
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

def track(pg, key, secs):
    vals = []
    for _ in range(int(secs / 0.25)):
        vals.append(pg.evaluate(f"window.__dbg.state.ang.{key}"))
        pg.wait_for_timeout(250)
    return vals

fails = []
def check(name, ok, detail):
    print(('PASS ' if ok else 'FAIL ') + name + '  ' + detail)
    if not ok:
        fails.append(name)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport=dict(width=1100, height=700))
    pg.goto(f'http://127.0.0.1:{srv.server_address[1]}/_test.html')
    pg.wait_for_selector('#loading', state='hidden', timeout=60000)
    pg.evaluate("window.__dbg.enterRegion('arm')")
    pg.wait_for_selector('#region:not([hidden])'); pg.wait_for_selector('#loading', state='hidden', timeout=60000)
    pg.evaluate("window.__dbg.scene.visible = false")      # keep the software renderer from skewing timing
    chip = lambda t: pg.click(f'#presets .chip >> text={t}')

    chip('屈肘'); pg.wait_for_timeout(1500)
    pg.click('#play')
    v = track(pg, 'el_flex', 1.25)
    check('play from the preset pose moves within 1 s', min(v) < 105, f'el_flex {v[0]:.0f} -> {min(v):.0f}')

    chip('側平舉')
    abd = track(pg, 'sh_abd', 2.5)
    playing = pg.evaluate("!!window.__dbg.state.play") and pg.inner_text('#play') == '停止播放'
    check('switching preset keeps playing', playing, f'button: {pg.inner_text("#play")}')
    check('switching preset reaches the new pose', max(abd) > 85, f'sh_abd max {max(abd):.0f}')
    later = track(pg, 'sh_abd', 3.5)
    check('then keeps going back and forth', min(later) < 10 and max(later) > 80, f'sh_abd range {min(later):.0f}..{max(later):.0f}')

    pg.click('#play')
    pg.wait_for_timeout(1800)
    a = track(pg, 'sh_abd', 1.0)
    check('stop button stops', max(a) - min(a) < 0.5 and not pg.evaluate("!!window.__dbg.state.play"), f'sh_abd {a[0]:.1f}..{a[-1]:.1f}')
    # ---- walking ----
    pg.click('#back'); pg.wait_for_timeout(500)
    pg.evaluate("window.__dbg.enterRegion('leg')")
    pg.wait_for_selector('#loading', state='hidden', timeout=60000); pg.wait_for_timeout(800)
    pg.evaluate("window.__dbg.scene.visible = false")
    chip('走路')
    seen, hip, knee = set(), [], []
    for _ in range(22):                       # 5.5 s > one 4 s cycle
        st = pg.evaluate("({a: window.__dbg.state.ang, p: document.querySelector('#gait-phase').textContent})")
        hip.append(st['a']['hip_flex']); knee.append(st['a']['kn_flex']); seen.add(st['p'].split('（')[0])
        pg.wait_for_timeout(250)
    check('walking runs through the cycle', min(hip) < -5 and max(hip) > 28 and max(knee) > 55,
          f'hip {min(hip):.0f}..{max(hip):.0f}, knee max {max(knee):.0f}')
    check('phase names follow the cycle', len(seen) >= 6, f'{len(seen)} phases seen: {"、".join(sorted(seen))}')
    check('gait panel shown', pg.is_visible('#gait'), '')
    pg.evaluate("(() => { const s = document.querySelector('#gait-scrub'); s.value = 73; s.dispatchEvent(new Event('input', {bubbles: true})); })()")
    pg.wait_for_timeout(300)
    a = pg.evaluate("window.__dbg.state.ang")
    check('scrubbing pauses at that moment', not pg.evaluate("!!window.__dbg.state.play") and abs(a['kn_flex'] - 62) < 1.5,
          f"knee {a['kn_flex']:.1f} at 73% ({pg.inner_text('#gait-phase')})")
    pg.click('#play'); pg.wait_for_timeout(600)       # 0.6 s of a 4 s cycle = +15 %
    pct = pg.evaluate("window.__dbg.state.gaitPhase * 100")
    check('play resumes from the scrubbed moment', 75 < pct < 95, f'{pct:.0f}% after 0.6 s (expected about 88%)')
    chip('抬膝'); pg.wait_for_timeout(300)
    check('another preset ends walking', not pg.is_visible('#gait') and pg.inner_text('#play') == '停止播放', '')
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
