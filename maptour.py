"""Map-tour visual for Fruit Soda: camera zooms region to region, labels accumulate. Registers KINDS['map']."""
import os, sys, json, math, urllib.request
import numpy as np, cv2
from engine import *
F = sys.modules.get('fruitsoda') or sys.modules['__main__']
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = {'india': ('https://raw.githubusercontent.com/Subhash9325/GeoJSON-Data-of-Indian-States/master/Indian_States', 'NAME_1',
                 {'Andaman and Nicobar', 'Lakshadweep'}, {'Odisha': 'Orissa', 'Uttarakhand': 'Uttaranchal'}, (82.5, 21.8))}
COLS = [(255,61,129),(255,170,0),(0,168,150),(0,150,255),(230,57,70),(150,90,255),(255,120,40),(60,190,90)]
K0, SX, CY = 34.0, 0.93, 935
_M = {}
def load(name):
    if name in _M: return _M[name]
    url, key, skip, alias, ctr = SRC[name]; os.makedirs(os.path.join(HERE, 'maps'), exist_ok=True)
    raw = os.path.join(HERE, 'maps', name + '.raw.json')
    if not os.path.exists(raw): urllib.request.urlretrieve(url, raw)
    d = json.load(open(raw)); out = {}
    for f in d['features']:
        nm = f['properties'][key]
        if nm in skip: continue
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        rings = sorted([np.array(p[0], np.float32) for p in polys], key=lambda a: -(np.ptp(a[:,0])*np.ptp(a[:,1])))
        keep = []
        for j, a in enumerate(rings):
            if j > 0 and np.ptp(a[:,0])*np.ptp(a[:,1]) < 0.02: continue
            s = cv2.approxPolyDP(a.reshape(-1,1,2), 0.03, True).reshape(-1, 2)
            if len(s) >= 3: keep.append(s)
        big = keep[0]; out[nm] = dict(polys=keep, bbox=(float(big[:,0].min()), float(big[:,0].max()), float(big[:,1].min()), float(big[:,1].max())))
    _M[name] = (out, alias, ctr); return _M[name]

def target(m, region):
    regs, alias, ctr = m
    r = alias.get(region, region)
    if not r or r not in regs: return (ctr[0], ctr[1], 1.0)
    x0, x1, y0, y1 = regs[r]['bbox']; cx, cy = (x0+x1)/2, (y0+y1)/2
    z = max(1.0, min(5.5, 480/(max((x1-x0)*SX, (y1-y0))*K0))); return (cx, cy, z)

def v_map(c, v, p, t):
    m = load(v.get('map', 'india')); regs, alias, ctr = m; prev = v.get('prev', []); cur = v.get('r', '')
    a = target(m, prev[-1][0] if prev else ''); b = target(m, cur); e = ease(clamp(p/0.3))
    lon, lat = lerp(a[0], b[0], e), lerp(a[1], b[1], e); z = math.exp(lerp(math.log(a[2]), math.log(b[2]), e)); k = K0*z
    def proj(P): return np.stack([(P[:,0]-lon)*k*SX+540, (lat-P[:,1])*k+CY], 1).astype(np.int32)
    top, bot = c.img[:340].copy(), c.img[1420:].copy()
    marks = {alias.get(r, r): (COLS[j % 8], lab) for j, (r, lab) in enumerate(prev)}
    if cur: marks[alias.get(cur, cur)] = (COLS[len(prev) % 8], v.get('t', ''))
    for nm, rg in regs.items():
        for P in rg['polys']:
            q = proj(P)
            if q[:,0].max() < -50 or q[:,0].min() > W+50 or q[:,1].max() < 200 or q[:,1].min() > 1500: continue
            col = marks[nm][0] if nm in marks else (176,190,214)
            if nm == alias.get(cur, cur) and nm in marks: col = mix(col, WHITE, 0.15*(1+math.sin(t*6))/2)
            c.poly(q, col); c.poly(q, (255,255,255), th=2)
    for nm, (col, lab) in marks.items():
        x0, x1, y0, y1 = regs[nm]['bbox']; cx = (x0+x1)/2; cy = (y0+y1)/2
        sx, sy = (cx-lon)*k*SX+540, (lat-cy)*k+CY; is_cur = (nm == alias.get(cur, cur))
        sz = int((54*max(0.2, back(clamp((p-0.25)/0.3))) if is_cur else 36)); sz = max(sz, 8)
        w = font(sz).getlength(lab)+46
        if sx < 80 or sx > W-80 or sy < 380 or sy > 1390: continue
        c.rrect(sx-w/2, sy-sz*0.8, sx+w/2, sy+sz*0.8, int(sz*0.6), col); c.rrect(sx-w/2, sy-sz*0.8, sx+w/2, sy+sz*0.8, int(sz*0.6), (255,255,255), th=3)
        c.text(lab, (sx, sy), sz, WHITE, stroke=3, sc=(10,10,30))
        if is_cur and cur: c.text(cur.upper(), (sx, sy+sz*0.8+34), 34, WHITE, stroke=5, sc=(10,10,30))
    c.img[:340] = top; c.img[1420:] = bot
F.KINDS['map'] = v_map
