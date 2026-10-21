"""Regression test for ping-pong playback (headless Chromium, needs build/artifact).
1. press play while standing in the preset pose -> the limb starts moving at once
2. switch preset during playback -> playback continues with the new movement
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
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
