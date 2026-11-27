import numpy as np, cv2, math, random
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
import os as _os
FD = _os.environ.get('FS_FONTS', '/usr/share/fonts/truetype/google-fonts/')

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def back(x):
    x = clamp(x); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def grad(top, bot, h=H, w=W):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, np.float32)[None, None, :]; b = np.array(bot, np.float32)[None, None, :]
    return np.repeat((a + (b - a) * t).astype(np.uint8), w, axis=1)

def poly(img, pts, col):
    cv2.fillPoly(img, [np.array(pts, np.int32)], col, cv2.LINE_AA)

def circle(img, c, r, col): cv2.circle(img, (int(c[0]), int(c[1])), int(r), col, -1, cv2.LINE_AA)

def ell(img, c, ax, col, ang=0): cv2.ellipse(img, (int(c[0]), int(c[1])), (int(ax[0]), int(ax[1])), ang, 0, 360, col, -1, cv2.LINE_AA)

def rrect(img, x0, y0, x1, y1, r, col):
    r = int(min(r, (x1 - x0) / 2, (y1 - y0) / 2))
    cv2.rectangle(img, (int(x0 + r), int(y0)), (int(x1 - r), int(y1)), col, -1, cv2.LINE_AA)
    cv2.rectangle(img, (int(x0), int(y0 + r)), (int(x1), int(y1 - r)), col, -1, cv2.LINE_AA)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): circle(img, (cx, cy), r, col)

def limb(img, p0, p1, w, col):
    cv2.line(img, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, int(w), cv2.LINE_AA)
    circle(img, p0, w / 2, col); circle(img, p1, w / 2, col)

def blend_circle(img, c, r, col, a):
    o = img.copy(); circle(o, c, r, col); cv2.addWeighted(o, a, img, 1 - a, 0, img)

def glow(img, c, r, col, a=0.5):
    m = np.zeros((H // 4, W // 4), np.float32)
    cv2.circle(m, (int(c[0] / 4), int(c[1] / 4)), int(r / 4), 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), r / 10); m = cv2.resize(m, (W, H))[..., None]
    img[:] = np.clip(img.astype(np.float32) * (1 - m * a) + np.array(col, np.float32) * m * a, 0, 255).astype(np.uint8)

def hills(img, base, amp, f, ph, col, t=0.0, drift=0.0):
    xs = np.arange(0, W + 30, 30)
    pts = [(x, base + amp * math.sin((x + t * drift) * f + ph) + amp * .4 * math.sin((x + t * drift) * f * 2.3 + ph * 1.7)) for x in xs]
    poly(img, pts + [(W + 30, H + 10), (0, H + 10)], col)

def tree(img, x, y, s, trunk, leaf, sway=0.0):
    rrect(img, x - 9 * s, y - 120 * s, x + 9 * s, y, 4 * s, trunk)
    for dx, dy, r in ((0, -170, 62), (-42, -135, 46), (42, -135, 46), (6, -215, 44)):
        circle(img, (x + dx * s + sway * (-dy / 100) * s, y + dy * s), r * s, leaf)

def cloud(img, x, y, s, col):
    for dx, dy, r in ((0, 0, 50), (55, 12, 42), (-55, 14, 38), (28, -24, 40)):
        circle(img, (x + dx * s, y + dy * s), r * s, col)
    rrect(img, x - 95 * s, y + 8 * s, x + 95 * s, y + 52 * s, 20 * s, col)

def grain(seed=3):
    rs = np.random.RandomState(seed)
    return (rs.randn(H // 2, W // 2, 1) * 6).astype(np.float32)

GRAIN = cv2.resize(grain()[..., 0], (W, H))[..., None]
_vy, _vx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.34 * np.clip(((_vx - W / 2) / (W / 2)) ** 2 * .8 + ((_vy - H / 2) / (H / 2)) ** 2 - 0.30, 0, 1))[..., None].astype(np.float32)

def finish(img, warm=0.0):
    f = img.astype(np.float32)
    f = f * VIG + GRAIN
    if warm: f = f * np.array([1 + warm, 1 + warm * .35, 1 - warm * .5], np.float32)
    return np.clip(f, 0, 255).astype(np.uint8)

_F = {}
def font(name, size, var=None):
    k = (name, size, var)
    if k not in _F:
        f = ImageFont.truetype(FD + name, size)
        if var:
            try: f.set_variation_by_axes([var])
            except Exception: pass
        _F[k] = f
    return _F[k]

def text_pass(img, jobs):
    im = Image.fromarray(img); d = ImageDraw.Draw(im, 'RGBA')
    for j in jobs:
        kind = j[0]
        if kind == 'text':
            _, t, c, size, col, fname, stroke = j
            f = font(fname, size)
            if stroke: d.text(c, t, font=f, fill=col, anchor='mm', stroke_width=stroke[0], stroke_fill=stroke[1])
            else: d.text(c, t, font=f, fill=col, anchor='mm')
    return np.asarray(im)

def wrap_lines(words, f, maxw):
    lines, cur = [], []
    for w in words:
        trial = ' '.join(cur + [w])
        if f.getlength(trial) > maxw and cur: lines.append(cur); cur = [w]
        else: cur.append(w)
    if cur: lines.append(cur)
    return lines

def caption(img, words, times, t, cy=1300, maxw=860, size=60, key=()):
    f = font('Lora-Variable.ttf', size, 700)
    shown = [i for i, ts in enumerate(times) if t >= ts - 0.02]
    if not shown: return img
    lines = wrap_lines(words, f, maxw)
    im = Image.fromarray(img); d = ImageDraw.Draw(im, 'RGBA')
    nl = len(lines); lh = int(size * 1.28); y0 = cy - (nl - 1) * lh / 2
    pw = max(f.getlength(' '.join(l)) for l in lines) + 90; ph = nl * lh + 34
    d.rounded_rectangle((W / 2 - pw / 2, y0 - lh / 2 - 8, W / 2 + pw / 2, y0 - lh / 2 - 8 + ph), 40, fill=(60, 36, 30, 95))
    k = 0
    for r, l in enumerate(lines):
        tw = f.getlength(' '.join(l)); x = W / 2 - tw / 2
        for w in l:
            vis = k in shown
            cur = vis and (k == shown[-1])
            col = (255, 214, 120) if (cur or w.strip('.,!?').lower() in key) else (255, 246, 232)
            if vis: d.text((x, y0 + r * lh), w, font=f, fill=col, anchor='lm', stroke_width=3, stroke_fill=(70, 40, 32))
            x += f.getlength(w + ' '); k += 1
    return np.asarray(im)

def brand(img, logo=None):
    im = Image.fromarray(img); d = ImageDraw.Draw(im, 'RGBA')
    f = font('Poppins-Bold.ttf', 34)
    d.text((W / 2, 150), 'FRUIT SODA', font=f, fill=(255, 244, 226, 235), anchor='mm', stroke_width=3, stroke_fill=(90, 50, 40))
    return np.asarray(im)
