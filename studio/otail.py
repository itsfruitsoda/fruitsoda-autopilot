def gradbg(c1, c2):
    img = np.zeros((H, W, 3), np.uint8)
    for y in range(H): img[y, :] = [int(c1[i] + (c2[i] - c1[i]) * y / H) for i in range(3)]
    return img

def seaworld(t, sunset=False):
    img = gradbg((255, 150, 110), (255, 226, 176)) if sunset else gradbg((176, 222, 244), (255, 232, 226))
    img[700:] = gradbg((70, 150, 175), (20, 66, 96))[700:] if True else 0
    for k in range(5):
        yy = 760 + k * 150
        pts = [(x, yy + 8 * math.sin(x * .02 + t * 2 + k)) for x in range(0, W + 30, 30)]
        cv2.polylines(img, [np.array(pts, np.int32)], False, (150, 210, 220), 3, cv2.LINE_AA)
    return img

def heart(img, x, y, r, col=(255, 130, 160), a=1.0):
    o = img.copy()
    circle(o, (x - r * .5, y - r * .3), r * .55, col); circle(o, (x + r * .5, y - r * .3), r * .55, col)
    poly(o, [(x - r * 1.0, y - r * .1), (x + r * 1.0, y - r * .1), (x, y + r * 1.05)], col)
    cv2.addWeighted(o, a, img, 1 - a, 0, img)

def hearts(img, cx, cy, t, n=4, sc=1.0):
    for k in range(n):
        p = ((t * .45 + k / n) % 1.0)
        heart(img, cx + math.sin(p * 6 + k * 2) * 70 * sc + (k - n / 2) * 25, cy - p * 260 * sc, (14 + 8 * math.sin(k)) * sc, a=1 - p)

def sparkle(img, x, y, r, a=1.0):
    o = img.copy()
    poly(o, [(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28), (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)], (255, 246, 190))
    cv2.addWeighted(o, a, img, 1 - a, 0, img)

def pup(img, x, y, s, d, t):
    fur, dark = (136, 96, 68), (60, 38, 28)
    ell(img, (x, y + 14 * s), (44 * s, 22 * s), fur)
    circle(img, (x, y - 6 * s), 34 * s, fur)
    circle(img, (x - 22 * s, y - 34 * s), 10 * s, fur); circle(img, (x + 22 * s, y - 34 * s), 10 * s, fur)
    circle(img, (x, y + 2 * s), 24 * s, (226, 196, 156))
    for ex in (-11, 11):
        cv2.ellipse(img, (int(x + ex * s), int(y - 6 * s)), (int(6 * s), int(4 * s)), 0, 0, 180, dark, max(2, int(3 * s)), cv2.LINE_AA)
    ell(img, (x, y + 4 * s), (6 * s, 4 * s), dark)
    for ex in (-17, 17): blend_circle(img, (x + ex * s, y + 6 * s), 7 * s, (255, 140, 150), .55)

def otter(img, x, y, s=1.0, d=1, t=0.0, paw=None, baby=False):
    by = y + 5 * math.sin(t * 1.6 + x * .01)
    fur, belly, dark = (128, 88, 62), (206, 168, 124), (60, 38, 28)
    ell(img, (x + d * 175 * s, by + 10 * s), (70 * s, 26 * s), fur, 8 * d)
    ell(img, (x, by), (150 * s, 60 * s), fur)
    ell(img, (x, by - 14 * s), (120 * s, 36 * s), belly)
    hx, hy = x - d * 165 * s, by - 18 * s
    circle(img, (hx, hy), 66 * s, fur)
    for sx in (-30, 26):
        circle(img, (hx + d * sx * s, hy - 56 * s), 17 * s, fur); circle(img, (hx + d * sx * s, hy - 56 * s), 9 * s, (236, 170, 170))
    circle(img, (hx - d * 6 * s, hy + 10 * s), 48 * s, (226, 196, 156))
    for ex in (-26, 14):
        cx_, cy_ = int(hx + d * ex * s), int(hy - 8 * s)
        cv2.ellipse(img, (cx_, cy_), (int(13 * s), int(9 * s)), 0, 0, 180, dark, max(3, int(5 * s)), cv2.LINE_AA)
        for ln in (-1, 1): cv2.line(img, (cx_ + int(ln * 11 * s), cy_ + int(2 * s)), (cx_ + int(ln * 16 * s), cy_ - int(3 * s)), dark, max(2, int(3 * s)), cv2.LINE_AA)
    for ex in (-42, 28): blend_circle(img, (hx + d * ex * s, hy + 18 * s), 13 * s, (255, 132, 150), .6)
    nx, ny = hx - d * 34 * s, hy + 8 * s
    ell(img, (nx, ny), (16 * s, 11 * s), dark); blend_circle(img, (nx - 4 * s, ny - 4 * s), 4 * s, (255, 255, 255), .8)
    cv2.ellipse(img, (int(nx + d * 10 * s), int(ny + 18 * s)), (int(11 * s), int(8 * s)), 0, 0, 180, dark, max(2, int(3 * s)), cv2.LINE_AA)
    for k in (-1, 0, 1):
        cv2.line(img, (int(nx - d * 6 * s), int(ny + 8 * s + k * 8 * s)), (int(nx - d * 52 * s), int(ny + 4 * s + k * 16 * s)), (245, 235, 220), max(2, int(2.5 * s)), cv2.LINE_AA)
    sh = (x - d * 70 * s, by - 34 * s)
    tgt = paw if paw else (x - d * 30 * s, by - 62 * s)
    cv2.line(img, (int(sh[0]), int(sh[1])), (int(tgt[0]), int(tgt[1])), fur, max(4, int(28 * s)), cv2.LINE_AA)
    ell(img, tgt, (19 * s, 16 * s), (92, 62, 44))
    if baby: pup(img, x + d * 20 * s, by - 62 * s, 1.35 * s, d, t)
    return by

def wave(img, y, col=(52, 128, 156), a=0.82, t=0.0, x0=0, x1=W, depth=140):
    o = img.copy()
    pts = [(x, y + 7 * math.sin(x * .03 + t * 2.6)) for x in range(int(x0), int(x1) + 20, 20)]
    poly(o, pts + [(x1 + 20, y + depth), (x0, y + depth)], col)
    cv2.addWeighted(o, a, img, 1 - a, 0, img)

def floater(img, x, y, s, d, t, paw=None, baby=False):
    bg = img.copy()
    by = otter(img, x, y, s, d, t, paw, baby)
    wl = by + 14 * s; xa = int(max(0, x - 330 * s)); xb = int(min(W, x + 330 * s)); dep = int(150 * s)
    for cx in range(xa, xb, 4):
        yt = int(wl + 6 * math.sin(cx * .03 + t * 2.6)); img[yt:yt + dep, cx:cx + 4] = bg[yt:yt + dep, cx:cx + 4]
    pts = [(cx, wl + 6 * math.sin(cx * .03 + t * 2.6)) for cx in range(xa, xb, 20)]
    if len(pts) > 1: cv2.polylines(img, [np.array(pts, np.int32)], False, (170, 225, 232), 4, cv2.LINE_AA)

def kelp(img, x, t, top=900):
    pts = [(x + 28 * math.sin(t * 1.4 + y * .012 + x), y) for y in range(1250, top, -25)]
    cv2.polylines(img, [np.array(pts, np.int32)], False, (70, 130, 70), 16, cv2.LINE_AA)
    for i in range(3, len(pts), 5):
        ell(img, (pts[i][0] + 24, pts[i][1]), (28, 10), (90, 160, 80), 20)

def scene_P(t):
    img = seaworld(t); jobs = []
    if t < S[2]:
        floater(img, 540, 820, 1.35, 1, t)
        if t > S[0] + 1.2: hearts(img, 480, 700, t, 2)
        if t > S[0] + 1.2: jobs.append(('text', 'Z z z', (300, 650), 52, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
        jobs.append(('text', 'SEA OTTERS SLEEP AT SEA', (W / 2, 330), 44, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
    else:
        p = ease((t - S[2]) / (S[3] - S[2]))
        floater(img, 540 + 240 * p, 820, 1.35, 1, t)
        for k in range(3):
            xa = 120 + k * 330 + 60 * math.sin(t * 2 + k)
            cv2.arrowedLine(img, (int(xa), 1060 + k * 40), (int(xa + 200), 1060 + k * 40), (255, 246, 232), 10, cv2.LINE_AA, tipLength=.3)
        jobs.append(('text', 'CURRENTS DRIFT THEM APART', (W / 2, 330), 40, (255, 200, 170), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
    return img, jobs

def scene_C(t):
    img = seaworld(t); jobs = []
    p = ease((t - S[3]) / 1.0)
    floater(img, 300 - 160 * (1 - p), 800, 1.0, 1, t, paw=(530, 760))
    floater(img, 780 + 160 * (1 - p), 800, 1.0, -1, t, paw=(550, 760))
    q = ease((t - S[3] - 1.2) / 0.8)
    if q > 0:
        floater(img, 300, 1000, 1.0 * q + .01, 1, t, paw=(530, 960))
        floater(img, 780, 1000, 1.0 * q + .01, -1, t, paw=(550, 960))
    hearts(img, 540, 740, t, 5)
    jobs.append(('text', 'THEY HOLD HANDS', (W / 2, 330), 52, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
    if q > .5: jobs.append(('text', 'A "RAFT" OF OTTERS', (W / 2, 1180), 44, (255, 220, 160), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
    return img, jobs

def scene_D(t):
    img = seaworld(t); jobs = []
    if t < S[5]:
        for kx in (260, 400, 690, 830): kelp(img, kx, t)
        floater(img, 540, 840, 1.25, 1, t, baby=True)
        o = img.copy(); cv2.ellipse(o, (540, 830), (110, 24), 0, 0, 360, (70, 130, 70), -1, cv2.LINE_AA); cv2.addWeighted(o, .8, img, .2, 0, img)
        jobs.append(('text', 'KELP SEATBELT', (W / 2, 330), 56, (210, 250, 190), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
    else:
        floater(img, 540, 840, 1.45, 1, t, paw=(500, 720))
        a = ease((t - S[5] - 0.4) / 0.5)
        circle(img, (540, 770), 26 * a, (150, 150, 158)); circle(img, (532, 764), 8 * a, (190, 190, 196))
        cv2.arrowedLine(img, (800, 560), (580, 745), (255, 246, 232), 8, cv2.LINE_AA, tipLength=.2) if a > .6 else None
        jobs.append(('text', 'A FAVORITE ROCK', (W / 2, 330), 52, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 50, 70))))
        if a > .6: jobs.append(('text', 'kept in a skin pocket', (800, 520), 34, (255, 246, 232), 'Poppins-Medium.ttf', (4, (20, 50, 70))))
    return img, jobs

def scene_G(t):
    img = seaworld(t, True); jobs = []
    for (x, y, d, pw) in ((300, 800, 1, (530, 760)), (780, 800, -1, (550, 760))):
        floater(img, x, y, 1.0, d, t, paw=pw)
    floater(img, 540, 1010, 1.1, 1, t, baby=True)
    hearts(img, 540, 790, t, 6)
    for k in range(6): sparkle(img, 90 + k * 180 + 20 * math.sin(t * 2 + k), 560 + 70 * math.sin(k * 2.3), 18 + 8 * math.sin(t * 3 + k), .5 + .5 * math.sin(t * 3 + k))
    jobs += [('text', 'TINY PAWS', (W / 2, 330), 64, (255, 246, 232), 'Lora-Variable.ttf', (6, (90, 40, 40))), ('text', 'BIG TEAMWORK', (W / 2, 410), 64, (255, 220, 170), 'Lora-Variable.ttf', (6, (90, 40, 40)))]
    return img, jobs

def scene_F(t):
    img = cv2.GaussianBlur(seaworld(t, True), (0, 0), 16)
    from PIL import Image
    lg = np.asarray(Image.open('logo.png').convert('RGB')); ys, xs = np.where(lg.min(axis=2) < 245); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    r = int(190 * back((t - S[-1]) / .5))
    if r > 10:
        s = cv2.resize(lg, (2 * r, 2 * r)); m = np.zeros((2 * r, 2 * r), np.uint8); cv2.circle(m, (r, r), r, 255, -1)
        roi = img[700 - r:700 + r, 540 - r:540 + r]; roi[m > 0] = s[m > 0]
    jobs = [('text', '@itsfruitsoda', (W / 2, 1000), 64, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 50, 70)))]
    rrect(img, 300, 1070, 780, 1170, 50, (232, 98, 96)); jobs.append(('text', 'FOLLOW', (W / 2, 1120), 56, (255, 255, 255), 'Poppins-Bold.ttf', None))
    return img, jobs

def sid(t):
    if t < S[3]: return 'P'
    if t < S[4]: return 'C'
    if t < S[6]: return 'D'
    if t < S[-1]: return 'G'
    return 'F'
SC = dict(P=scene_P, C=scene_C, D=scene_D, G=scene_G, F=scene_F)
KEY = set(SPEC.get('key', []))
BOUND = {'C': S[3], 'D': S[4], 'G': S[6], 'F': S[-1]}; PREV = {'C': 'P', 'D': 'C', 'G': 'D', 'F': 'G'}
