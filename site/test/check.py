"""Headless browser smoke test of build/artifact at phone (light) and desktop (dark) sizes; screenshots to build/shots."""
import threading, http.server, functools, sys, os, time
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'artifact')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'shots')
os.makedirs(OUT, exist_ok=True)

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 8765), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
logs = []

def wait_idle(pg, ms=1500):
    pg.wait_for_timeout(ms)

with sync_playwright() as p:
    b = p.chromium.launch(args=ARGS)
    for name, vp, scheme in [('phone', dict(width=400, height=860), 'light'), ('desk', dict(width=1280, height=800), 'dark')]:
        ctx = b.new_context(viewport=vp, color_scheme=scheme)
        pg = ctx.new_page()
        pg.on('console', lambda m, n=name: logs.append(f'[{n}] {m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e, n=name: logs.append(f'[{n}] PAGEERROR {e}'))
        pg.goto('http://127.0.0.1:8765/_test.html')
        pg.wait_for_selector('#loading', state='hidden', timeout=60000)
        wait_idle(pg)
        pg.screenshot(path=f'{OUT}/{name}_1_home.png')
        pg.click('.region-btn[data-region="arm"]')
        pg.wait_for_selector('#region:not([hidden])', timeout=60000)
        pg.wait_for_selector('#loading', state='hidden', timeout=60000)
        wait_idle(pg, 1200)
        pg.screenshot(path=f'{OUT}/{name}_2_arm.png')
        pg.click('#presets .chip >> text=屈肘')
        wait_idle(pg, 2500)
        pg.screenshot(path=f'{OUT}/{name}_3_arm_elbow.png')
        print(name, 'ledger after 屈肘:', pg.inner_text('#ledger').replace('\n', ' | '))
        pg.click('#presets .chip >> text=側舉過頭')
        wait_idle(pg, 2500)
        pg.screenshot(path=f'{OUT}/{name}_4_arm_abd.png')
        print(name, 'ledger after 側舉過頭:', pg.inner_text('#ledger').replace('\n', ' | '))
        # select a muscle through the ledger
        pg.click('#ledger .lg-row >> nth=0')
        wait_idle(pg, 800)
        pg.screenshot(path=f'{OUT}/{name}_5_arm_pick.png')
        print(name, 'pick card:', pg.inner_text('#pick').replace('\n', ' | '))
        pg.click('#back')
        wait_idle(pg, 1200)
        pg.click('.region-btn[data-region="leg"]')
        pg.wait_for_selector('#loading', state='hidden', timeout=60000)
        wait_idle(pg, 1200)
        pg.click('#presets .chip >> text=深蹲')
        wait_idle(pg, 2500)
        pg.screenshot(path=f'{OUT}/{name}_6_leg_squat.png')
        print(name, 'ledger after 深蹲:', pg.inner_text('#ledger').replace('\n', ' | '))
        pg.click('#presets .chip >> text=踮腳')
        wait_idle(pg, 2500)
        pg.screenshot(path=f'{OUT}/{name}_7_leg_tiptoe.png')
        pg.click('#tab-muscles')
        wait_idle(pg, 500)
        pg.screenshot(path=f'{OUT}/{name}_8_leg_list.png', full_page=False)
        # page must not scroll sideways
        print(name, 'horizontal overflow:', pg.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth'))
        ctx.close()
    b.close()
srv.shutdown()
print('\n'.join(logs) if logs else 'no console errors/warnings')
