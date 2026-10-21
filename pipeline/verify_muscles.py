"""Muscle-length sign test: for each motion, textbook agonists must shorten and antagonists lengthen.
Length = polyline through the muscle's anchors, each anchor moving with its bone."""
import json, sys, numpy as np
from lib import W
from kin import fk, apply

rig = json.load(open(f'{W}/rig.json'))

def lengths(region, meta, ang):
    M = fk(rig, region, ang)
    out = {}
    for n, d in meta['muscles'].items():
        if d['kind'] != 'muscle' or len(d['anchors']) < 2:
            continue
        segs = set(a['seg'] for a in d['anchors'])
        if len(segs) < 2:
            continue
        P = [apply(M[a['seg']], a['p']) if a['seg'] != 'trunk' else np.array(a['p']) for a in d['anchors']]
        L = sum(np.linalg.norm(P[i + 1] - P[i]) for i in range(len(P) - 1))
        if d.get('wrap'):
            w = d['wrap']
            L += w['sign'] * w['r'] * np.radians(rig['signs'].get(w['dof'], 1) * 0 + ang.get(w['dof'], 0.0))
        out[d['zh']] = L
    return out

TESTS = {
 'arm': [
  ('肩屈曲 90°', {'sh_flex': 90}, ['三角肌 前束', '胸大肌 鎖骨頭', '喙肱肌', '肱二頭肌 短頭'], ['闊背肌', '三角肌 後束', '大圓肌', '肱三頭肌 長頭']),
  ('肩外展 90°', {'sh_abd': 90}, ['三角肌 中束', '棘上肌', '斜方肌上束', '前鋸肌'], ['闊背肌', '大圓肌', '胸大肌 胸肋頭', '大菱形肌', '小菱形肌', '提肩胛肌', '胸小肌']),
  ('肩內旋 60°', {'sh_rot': 60}, ['肩胛下肌', '大圓肌', '闊背肌', '胸大肌 胸肋頭'], ['棘下肌', '小圓肌', '三角肌 後束']),
  ('肘屈曲 90°', {'el_flex': 90}, ['肱二頭肌 長頭', '肱二頭肌 短頭', '肱肌', '肱橈肌', '旋前圓肌 淺頭'], ['肱三頭肌 長頭', '肱三頭肌 外側頭', '肱三頭肌 內側頭', '肘肌']),
  ('前臂旋前 90°', {'pron': 90}, ['旋前圓肌 淺頭', '旋前圓肌 深頭', '旋前方肌'], ['旋後肌', '肱二頭肌 長頭']),
  ('腕屈曲 60°', {'wr_flex': 60}, ['橈側屈腕肌', '尺側屈腕肌 肱骨頭', '掌長肌', '屈指深肌', '屈指淺肌 肱尺頭'], ['橈側伸腕長肌', '橈側伸腕短肌', '伸指肌', '伸食指肌']),
  ('腕尺偏 30°', {'wr_dev': 30}, ['尺側屈腕肌 肱骨頭', '尺側伸腕肌 尺骨頭'], ['橈側伸腕長肌', '外展拇長肌']),
 ],
 'leg': [
  ('髖屈曲 90°', {'hip_flex': 90}, ['髂肌', '腰大肌', '股直肌', '縫匠肌', '闊筋膜張肌', '恥骨肌'], ['臀大肌', '股二頭肌 長頭', '半腱肌', '半膜肌']),
  ('髖外展 30°', {'hip_abd': 30}, ['臀中肌', '臀小肌', '闊筋膜張肌'], ['內收長肌', '內收短肌', '內收大肌', '股薄肌', '恥骨肌']),
  ('髖內旋 30°', {'hip_rot': 30}, [], ['梨狀肌', '閉孔內肌', '股方肌', '上孖肌', '下孖肌']),
  ('膝屈曲 90°', {'kn_flex': 90}, ['半腱肌', '半膜肌', '股二頭肌 長頭', '股二頭肌 短頭', '腓腸肌 外側頭', '腓腸肌 內側頭', '股薄肌', '縫匠肌'], ['股直肌', '股外側肌', '股內側肌', '股中間肌']),
  ('踝蹠屈 30°', {'an_flex': 30}, ['腓腸肌 外側頭', '腓腸肌 內側頭', '比目魚肌', '脛後肌', '腓骨長肌', '腓骨短肌', '屈趾長肌', '屈拇長肌（足）'], ['脛前肌', '伸趾長肌', '伸拇長肌（足）', '第三腓骨肌']),
  ('足內翻 20°', {'inv': 20}, ['脛後肌'], ['腓骨長肌', '腓骨短肌', '第三腓骨肌']),
  ('腳趾伸 40°', {'toe': 40}, ['伸趾短肌', '伸趾長肌', '伸拇長肌（足）'], ['屈趾長肌', '屈拇長肌（足）', '屈趾短肌', '足背側骨間肌', '蹠側骨間肌', '足部蚓狀肌']),
 ],
}
TH = 0.01
total = fails = 0
lines = []
for region, tests in TESTS.items():
    meta = json.load(open(f'{W}/bind_{region}.json'))
    L0 = lengths(region, meta, {})
    for title, ang, short, long_ in tests:
        L1 = lengths(region, meta, ang)
        bad = []
        for m in short:
            total += 1
            if m not in L0: bad.append(f'{m}: 無長度'); continue
            r = L1[m] / L0[m]
            if not (r < 1 - TH or L1[m] - L0[m] < -0.002): bad.append(f'{m} 應縮短 但 {r:.3f}')
        for m in long_:
            total += 1
            if m not in L0: bad.append(f'{m}: 無長度'); continue
            r = L1[m] / L0[m]
            if not (r > 1 + TH or L1[m] - L0[m] > 0.002): bad.append(f'{m} 應拉長 但 {r:.3f}')
        fails += len(bad)
        ch = sorted(((L1[m] / L0[m], m) for m in L0), key=lambda x: x[0])
        top_s = ', '.join(f'{m} {(r-1)*100:+.0f}%' for r, m in ch[:5] if r < 0.99)
        top_l = ', '.join(f'{m} {(r-1)*100:+.0f}%' for r, m in ch[::-1][:5] if r > 1.01)
        lines.append(f'{"PASS" if not bad else "FAIL"} {title}\n   縮最多: {top_s}\n   拉最多: {top_l}' + ('\n   !! ' + '; '.join(bad) if bad else ''))
print('\n'.join(lines))
print(f'\n{total - fails}/{total} expectations met')
open(f'{W}/muscle_report.txt', 'w').write('\n'.join(lines) + f'\n\n{total - fails}/{total} expectations met\n')
