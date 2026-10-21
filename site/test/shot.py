"""Screenshot one pose from a chosen camera (headless Chromium).
usage: python3 site/test/shot.py out.png region '{"kn_flex":90}' 'px,py,pz' 'tx,ty,tz' [w h]"""
import sys, os, json, threading, http.server, functools
from playwright.sync_api import sync_playwright
out, region, ang, pos, tgt = sys.argv[1:6]
w, h = (int(sys.argv[6]), int(sys.argv[7])) if len(sys.argv) > 7 else (900, 900)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Q, directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build', 'artifact')))
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    pg = b.new_page(viewport=dict(width=w + 400 if w >= 900 else w, height=h))
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(f'http://127.0.0.1:{port}/_test.html')
    pg.wait_for_selector('#loading', state='hidden', timeout=60000)
    pg.evaluate(f"window.__dbg.enterRegion('{region}')")
    pg.wait_for_selector('#region:not([hidden])', timeout=60000)
    pg.wait_for_selector('#loading', state='hidden', timeout=60000)
    pg.wait_for_timeout(900)
    pg.evaluate(f"window.__dbg.setAng({ang})")
    pg.evaluate(f"window.__dbg.setView([{pos}],[{tgt}])")
    pg.wait_for_timeout(600)
    pg.locator('#stage').screenshot(path=out)
    if errs: print('ERR', errs)
    b.close()
srv.shutdown()
