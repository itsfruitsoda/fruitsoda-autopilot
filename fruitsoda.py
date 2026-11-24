#!/usr/bin/env python3
"""Fruit Soda autopilot: JSON spec -> voiceover + music + animated 1080x1920 short + thumbnail.
Usage:
  python fruitsoda.py plan  [N]            # ask Claude (ANTHROPIC_API_KEY) to write N new specs into specs/
  python fruitsoda.py render [spec ...]    # render specs (default: all in specs/) into out/
  python fruitsoda.py manifest TAG DATE    # write out/manifest.json (release URLs, daily schedule starting DATE)
"""
import os, sys, json, math, glob, subprocess, urllib.request, hashlib, datetime
import numpy as np, cv2, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import *

CTA = "Follow Fruit Soda for a fizzy new fact every day."
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
TTS_DIR = os.environ.get("FS_TTS", os.path.join(HERE, "tts"))
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
PALETTES = [((20,10,50),(3,3,18)), ((0,110,140),(5,40,80)), ((60,70,150),(20,25,70)), ((150,70,30),(60,25,20)),
            ((20,110,190),(8,40,100)), ((30,130,150),(8,50,80)), ((60,25,85),(18,10,40)), ((24,120,80),(8,60,42)),
            ((125,25,70),(50,10,40)), ((70,50,140),(26,20,70))]

# ---------------- logo badge ----------------
if not os.path.exists(os.path.join(HERE, "logo.png")):
    import base64; open(os.path.join(HERE, "logo.png"), "wb").write(base64.b64decode(open(os.path.join(HERE, "logo_b64.txt")).read()))
lg = np.asarray(Image.open(os.path.join(HERE, "logo.png")).convert("RGB")).astype(np.uint8)
ys, xs = np.where(lg.min(axis=2) < 245); lg = lg[ys.min():ys.max()+1, xs.min():xs.max()+1]
_B = {}
def paste_badge(img, cx, cy, r):
    if r not in _B:
        s = int(r*2); im = np.full((s,s,3), 255, np.uint8); hh = int(s*0.74); ww = int(lg.shape[1]*hh/lg.shape[0])
        l = cv2.resize(lg, (ww,hh), interpolation=cv2.INTER_AREA); y0=(s-hh)//2; x0=(s-ww)//2; im[y0:y0+hh, x0:x0+ww] = l
        m = np.zeros((s,s), np.uint8); cv2.circle(m, (r,r), r-2, 255, -1, cv2.LINE_AA); _B[r] = (im, m)
    im, m = _B[r]; x0, y0 = int(cx-r), int(cy-r); roi = img[y0:y0+2*r, x0:x0+2*r]
    a = (m.astype(float)/255)[..., None]; roi[:] = (im*a + roi*(1-a)).astype(np.uint8)
    cv2.circle(img, (int(cx),int(cy)), r-1, (255,255,255), 4, cv2.LINE_AA)

def wrap(words, fnt, maxw):
    lines = [[]]; cur = 0
    for w in words:
        wl = fnt.getlength(w+' ')
        if cur+wl > maxw and lines[-1]: lines.append([]); cur = 0
        lines[-1].append(w); cur += wl
    return lines
DARK = (10,10,30)
def fit_text(c, text, cx, cy, maxw, size, col, maxlines=3, stroke=7):
    while size > 40:
        ls = wrap(text.split(), font(size), maxw)
        if len(ls) <= maxlines and max(font(size).getlength(' '.join(l)) for l in ls) <= maxw: break
        size -= 6
    lh = int(size*1.15); y = cy - (len(ls)-1)*lh/2
    for l in ls: c.text(' '.join(l), (cx, y), size, col, stroke=stroke, sc=DARK); y += lh
    return len(ls)*lh

# ---------------- generic visual kinds ----------------
def v_big(c, v, p, t):
    pop = back(clamp(p*4)); sz = int(170*max(0.3, pop))
    h = fit_text(c, v.get('t',''), 540, 800, 900, sz, YEL)
    if v.get('s'): fit_text(c, v['s'], 540, 800+h/2+90, 880, 56, WHITE, 2, 5)
def v_num(c, v, p, t):
    n = float(v.get('n', 0)); val = n*ease(clamp(p*1.6)); txt = f"{val:,.0f}" if n >= 100 or n == int(n) else f"{val:.1f}"
    txt = v.get('pre','') + txt + v.get('suf','')
    fit_text(c, txt, 540, 760, 940, 230, YEL, 1, 9)
    if v.get('u'): fit_text(c, v['u'], 540, 960, 900, 60, WHITE, 2, 5)
def v_bars(c, v, p, t):
    items = v.get('items', []); mx = max([float(x[1]) for x in items] + [1e-9]); y = 560
    cols = [PINK, YEL, TEAL, BLUE, RED]
    for i, (lab, val) in enumerate(items):
        g = ease(clamp(p*1.5 - i*0.18)); w = max(8, 620*float(val)/mx*g)
        c.text(str(lab), (110, y), 46, WHITE, anchor='lm', stroke=4, sc=DARK)
        c.rrect(110, y+40, 110+w, y+120, 30, cols[i % 5]); c.text(str(val)+v.get('u',''), (110+w+20, y+80), 50, WHITE, anchor='lm', stroke=4, sc=DARK)
        y += min(210, 700//max(1,len(items)))
def v_list(c, v, p, t):
    items = v.get('items', []); n = max(1, len(items)); y = 520; step = min(190, 760//n)
    for i, it in enumerate(items):
        a = back(clamp(p*(n+1)*0.9 - i))
        if a <= 0.02: continue
        x0 = 80 + (1-a)*-300
        c.rrect(x0, y, x0+920, y+step-30, 40, (255,255,255), a=0.92); c.circ((x0+70, y+(step-30)/2), 38, PINK)
        c.text(str(i+1), (x0+70, y+(step-30)/2), 44, WHITE); c.text(str(it), (x0+130, y+(step-30)/2), 46, NAVY, anchor='lm')
        y += step
def v_vs(c, v, p, t):
    a = back(clamp(p*3)); L = v.get('l', ['A','']); R = v.get('r', ['B',''])
    for (x0, x1, d, col, sh) in ((50, 500, L, PINK, -1), (580, 1030, R, TEAL, 1)):
        off = (1-a)*300*sh
        c.rrect(x0+off, 520, x1+off, 1120, 50, col)
        fit_text(c, d[0], (x0+x1)/2+off, 760, 400, 90, WHITE, 3, 5)
        if len(d) > 1: fit_text(c, d[1], (x0+x1)/2+off, 980, 400, 46, WHITE, 3, 3)
    c.circ((540, 820), 62*a, YEL); c.text('VS', (540, 820), int(54*max(0.2, a)), NAVY)
def v_q(c, v, p, t):
    s = int(560*(1+0.05*math.sin(t*5))); c.text('?', (540, 820), s, YEL, stroke=12, sc=DARK)
    if v.get('t'): fit_text(c, v['t'], 540, 1160, 900, 64, WHITE, 2, 6)
def v_time(c, v, p, t):
    items = v.get('items', []); n = max(1, len(items)); c.line((120, 840), (960, 840), WHITE, 10)
    for i, (lab, sub) in enumerate(items):
        a = back(clamp(p*(n+1)*0.9 - i))
        if a <= 0.02: continue
        x = 120 + 840*(i/max(1, n-1)); c.circ((x, 840), 34*a, PINK); up = (i % 2 == 0)
        c.text(str(lab), (x, 840+(-110 if up else 110)), 52, YEL, stroke=5, sc=DARK)
        c.text(str(sub), (x, 840+(-175 if up else 175)), 36, WHITE, stroke=4, sc=DARK)
KINDS = dict(big=v_big, num=v_num, bars=v_bars, list=v_list, vs=v_vs, q=v_q, time=v_time)

# ---------------- voice + music ----------------
def ensure_models():
    os.makedirs(TTS_DIR, exist_ok=True)
    for f in ("kokoro-v1.0.int8.onnx", "voices-v1.0.bin"):
        p = os.path.join(TTS_DIR, f)
        if not os.path.exists(p): print("downloading", f); urllib.request.urlretrieve(MODEL_URL + f, p)
_K = None
def voice(spec, path):
    global _K
    from kokoro_onnx import Kokoro
    if _K is None: ensure_models(); _K = Kokoro(os.path.join(TTS_DIR, "kokoro-v1.0.int8.onnx"), os.path.join(TTS_DIR, "voices-v1.0.bin"))
    SR = 24000; segs = [np.zeros(int(0.12*SR))]; t = 0.12; info = []
    lines = [l['text'] for l in spec['lines']]
    for i, line in enumerate(lines):
        s, _ = _K.create(line, voice='am_michael', speed=1.08, lang='en-us'); s = np.asarray(s, np.float32)
        idx = np.where(np.abs(s) > 0.01)[0]; s = s[idx[0]:idx[-1]+1] if len(idx) else s
        gap = int((0.35 if i < len(lines)-1 else 0.9)*SR); info.append(dict(start=t, end=t+len(s)/SR, text=line))
        segs += [s, np.zeros(gap)]; t += len(s)/SR + gap/SR
    sf.write(path, np.concatenate(segs).astype(np.float32), SR); return dict(total=t, lines=info)

MSR = 44100
def _note(f, d, kind, amp):
    t = np.arange(int(d*MSR))/MSR
    if kind == 'pluck': w = np.sin(2*np.pi*f*t)+0.4*np.sin(4*np.pi*f*t)+0.2*np.sin(6*np.pi*f*t); env = np.exp(-t*7)
    elif kind == 'bass': w = np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t); env = np.exp(-t*3.5)*(1-np.exp(-t*80))
    else: w = sum(np.sin(2*np.pi*f*m*t+i) for i, m in enumerate([1,1.005,2]))/3; env = np.minimum(1, t*4)*np.exp(-t*0.8)
    return w*env*amp
def music(seed, bpm, dur, root, path):
    beat = 60/bpm; n = int(dur*MSR)+MSR; out = np.zeros(n); rs = np.random.RandomState(1)
    kt = np.arange(int(.25*MSR))/MSR; kick = np.sin(2*np.pi*np.cumsum(120*np.exp(-kt*18)+45)/MSR)*np.exp(-kt*12)
    ht = np.arange(int(.06*MSR))/MSR; hat = np.diff(rs.randn(len(ht)), prepend=0)*np.exp(-ht*60)*0.5
    def put(x, t0, g=1.0):
        i = int(t0*MSR)
        if i < n: j = min(n, i+len(x)); out[i:j] += x[:j-i]*g
    prog = [(0,4,7),(9,0,4),(5,9,0),(7,11,2)]; f0 = lambda s, o=0: root*2**((s+12*o)/12)
    for b in range(int(dur/(beat*4))+2):
        ch = prog[b % 4]; t0 = b*beat*4
        put(_note(f0(ch[0],-1), beat*3.5, 'bass', .55), t0); put(_note(f0(ch[0],-1), beat*1.5, 'bass', .45), t0+beat*2.5)
        for s in ch: put(_note(f0(s), beat*4, 'pad', .08), t0)
        for i in range(8): put(_note(f0(ch[[0,1,2,1,0,2,1,2][i]], 1), beat*.9, 'pluck', .20 if i % 2 == 0 else .14), t0+i*beat/2)
        for i in range(4):
            put(kick, t0+i*beat, .8); put(hat, t0+i*beat+beat/2, .35)
            if i in (1, 3): put(hat, t0+i*beat, .35)
    out = out[:int(dur*MSR)]; out /= np.max(np.abs(out))+1e-9; f = int(1.5*MSR); out[-f:] *= np.linspace(1, 0, f)
    sf.write(path, out.astype(np.float32), MSR)

# ---------------- frame builder ----------------
def caption(c, words, times, t, y0):
    chunks = [(k, min(k+6, len(words))) for k in range(0, len(words), 6)]; ci = 0
    for n, (a, b) in enumerate(chunks):
        if t >= times[a]: ci = n
    a, b = chunks[ci]; fnt = font(70); ls = wrap(words[a:b], fnt, 940); idx = a; ytop = y0 - len(ls)*45
    for r, l in enumerate(ls):
        tw = sum(fnt.getlength(w+' ') for w in l) - fnt.getlength(' '); x = 540 - tw/2; y = ytop + r*95
        for w in l:
            act = [k for k in range(a, b) if t >= times[k]]
            c.text(w, (x, y), 70, YEL if (act and idx == max(act)) else WHITE, anchor='lm', stroke=9, sc=DARK)
            x += fnt.getlength(w+' '); idx += 1

_yy,_xx=np.mgrid[0:H,0:W]; VIG=(1-0.30*np.clip((((_xx-W/2)/(W/2))**2+((_yy-H/2)/(H/2))**2)-0.35,0,1))[...,None].astype(np.float32)
def build(spec, tm):
    lines = tm['lines']; total = tm['total']+0.4; n = len(lines)
    pal = spec.get('bg') or PALETTES[int(hashlib.md5(spec['id'].encode()).hexdigest(), 16) % len(PALETTES)]
    bg = gradient(tuple(pal[0]), tuple(pal[1])); vis = [l.get('v') or {'k':'big','t':spec['hook']} for l in spec['lines']]
    wt = []
    for L in lines:
        ws = L['text'].split(); ln = np.array([len(w)+2 for w in ws], float); cs = np.concatenate([[0], np.cumsum(ln)])/ln.sum()
        wt.append((ws, [L['start']+(L['end']-L['start'])*x for x in cs[:-1]]))
    rs = np.random.RandomState(7); bub = [(rs.uniform(0,W), rs.uniform(0,2400), rs.uniform(60,160), rs.uniform(8,30)) for _ in range(34)]
    def frame(t):
        c = Cv(bg); o = c.img.copy()
        for x, off, sp, r in bub:
            cv2.circle(o, (int(x+14*math.sin(t*1.3+off)), int(H+60-((t*sp+off) % (H+120)))), int(r), (255,255,255), 3, cv2.LINE_AA)
        c.img = cv2.addWeighted(o, .22, c.img, .78, 0)
        ray = np.zeros((H//4, W//4), np.uint8)
        for k in range(5):
            a = t*0.15 + k*1.26; cv2.fillConvexPoly(ray, np.array([[135,-50],[135+int(650*math.cos(a)),-50+int(650*math.sin(a))],[135+int(650*math.cos(a+.16)),-50+int(650*math.sin(a+.16))]]), 255)
        ray = cv2.resize(cv2.GaussianBlur(ray, (0,0), 10), (W,H)); c.img = cv2.add(c.img, (np.dstack([ray]*3)*0.10).astype(np.uint8))
        i = 0
        for k, L in enumerate(lines):
            if t >= L['start']-0.05: i = k
        L = lines[i]; nxt = lines[i+1]['start'] if i+1 < n else total; p = clamp((t-L['start'])/max(.1, nxt-L['start'])); last = (i == n-1)
        paste_badge(c.img, 110, 140, 62); c.text('FRUIT SODA', (190,140), 44, WHITE, anchor='lm')
        c.rrect(700, 105, 1010, 175, 35, PINK); c.text(spec['cat'][:14], (855,140), 34, WHITE)
        if not last:
            pop = back(clamp(t/0.5)); hl = wrap(spec['hook'].split(), font(66), 900)
            for r, l in enumerate(hl): c.text(' '.join(l), (540, 285+r*78), int(66*max(.2, pop)), YEL, stroke=7, sc=DARK)
            v = vis[i]; KINDS.get(v.get('k', 'big'), v_big)(c, v, p, t)
        else:
            r = int(230*back(clamp(p*3)))
            if r > 10: paste_badge(c.img, 540, 780, r)
            c.text('@itsfruitsoda', (540,1085), 64, WHITE, stroke=6, sc=DARK); c.rrect(290,1150,790,1260,55,PINK); c.text('FOLLOW', (540,1205), 60, WHITE)
        if t >= lines[0]['start']-0.05: caption(c, *wt[i], t, 1560 if last else 1470)
        out = c.done()
        out = out.copy(); cv2.rectangle(out, (0,0), (int(W*clamp(t/total)),12), (255,214,64), -1)
        dt = t-L['start']
        if 0 <= dt < 0.28 and i > 0:
            z = 1+0.045*(1-dt/0.28)**2; M = cv2.getRotationMatrix2D((W/2,H/2), 0, z); out = cv2.warpAffine(out, M, (W,H), borderMode=cv2.BORDER_REFLECT)
        return (out*VIG).astype(np.uint8)
    return frame, total

def render(path):
    spec = json.load(open(path)); spec['lines'] = [l if isinstance(l, dict) else {'text': l} for l in spec['lines']]
    if spec['lines'][-1]['text'] != CTA: spec['lines'].append({'text': CTA})
    vid = spec['id']; tmp = os.path.join(OUT, '_' + vid); os.makedirs(tmp, exist_ok=True)
    tm = voice(spec, f'{tmp}/vo.wav'); h = int(hashlib.md5(vid.encode()).hexdigest(), 16)
    music(h % 100, 92+h % 26, 40, [196.0, 220.0, 233.08, 246.94, 261.63, 277.18, 293.66][h % 7], f'{tmp}/music.wav')
    frame, total = build(spec, tm); n = int(total*FPS); mp4 = os.path.join(OUT, f'fruit_soda_{vid}.mp4')
    cmd = ['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',f'{tmp}/vo.wav','-i',f'{tmp}/music.wav',
           '-filter_complex', f'[1:a]aresample=44100,apad[v];[2:a]aresample=44100,volume=0.20[m];[v][m]amix=inputs=2:duration=first:normalize=0,atrim=0:{total},loudnorm=I=-14:TP=-1.5[a]',
           '-map','0:v','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-t',str(total), mp4]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(n): pr.stdin.write(frame(k/FPS).tobytes())
    pr.stdin.close(); pr.wait(); thumb(spec, frame, os.path.join(OUT, f'fruit_soda_{vid}_thumb.jpg')); print('done', mp4); return spec

def thumb(spec, frame, path):
    th = spec.get('thumb', {}); text = th.get('text') or spec['hook']; s = th.get('t', 9)
    im = Image.fromarray(frame(s)); crop = im.crop((0,500,1080,1108)).resize((1280,720))
    bgi = im.resize((1280,2275)).crop((0,700,1280,1420)).filter(ImageFilter.GaussianBlur(8)); c = Image.blend(bgi, crop, .9); c = Image.blend(c, Image.new('RGB', c.size, (10,10,30)), .55); d = ImageDraw.Draw(c)
    f = ImageFont.truetype(FD+'Poppins-Bold.ttf', 118); y = 60
    for line in text.split('\n'):
        for dx, dy in [(-6,-6),(6,6),(-6,6),(6,-6),(0,8)]: d.text((50+dx, y+dy), line, font=f, fill=NAVY)
        d.text((50, y), line, font=f, fill=YEL); y += 135
    l = Image.open(os.path.join(HERE, 'logo.png')).convert('RGBA'); l.thumbnail((190,190)); c.paste(l, (1060,510), l); c.save(path, quality=92)

# ---------------- plan (Claude writes specs) ----------------
PROMPT = open(os.path.join(HERE, 'plan_prompt.md')).read() if os.path.exists(os.path.join(HERE, 'plan_prompt.md')) else ''
def plan(n):
    key = os.environ['ANTHROPIC_API_KEY']; used = ', '.join(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(HERE, 'specs', '*.json')) + glob.glob(os.path.join(HERE, 'done', '*.json')))
    body = dict(model=os.environ.get('FS_MODEL', 'claude-sonnet-5-5'), max_tokens=12000, messages=[{'role':'user','content': PROMPT + f"\n\nWrite {n} NEW specs. Already used ids/topics (do not repeat): {used}\nReturn ONLY a JSON array."}])
    rq = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode(), {'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'})
    txt = json.load(urllib.request.urlopen(rq, timeout=300))['content'][0]['text']; txt = txt[txt.index('['): txt.rindex(']')+1]
    for sp in json.loads(txt): json.dump(sp, open(os.path.join(HERE, 'specs', sp['id'] + '.json'), 'w'), indent=1); print('spec', sp['id'])

# ---------------- manifest ----------------
def manifest(tag, start):
    base = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/releases/download/{tag}/"; d0 = datetime.date.fromisoformat(start); items = []; k = 0
    for p in sorted(glob.glob(os.path.join(HERE, 'specs', '*.json'))):
        sp = json.load(open(p)); day = d0 + datetime.timedelta(days=k + (k // 6))   # Mon-Sat, skip Sunday
        items.append(dict(id=sp['id'], date=str(day), title=sp.get('yt_title', sp['hook']), description=sp.get('desc', ''), caption=sp.get('caption', ''), tags=sp.get('tags', ''), audience=sp.get('audience', 'global'), country=sp.get('country', ''),
                          video=base + f"fruit_soda_{sp['id']}.mp4", thumb=base + f"fruit_soda_{sp['id']}_thumb.jpg")); k += 1
    json.dump(dict(tag=tag, items=items), open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1); print(len(items), 'items')

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'render'
    if cmd == 'plan': plan(int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    elif cmd == 'render':
        for p in (sys.argv[2:] or sorted(glob.glob(os.path.join(HERE, 'specs', '*.json')))): render(p)
    elif cmd == 'manifest': manifest(sys.argv[2], sys.argv[3])
