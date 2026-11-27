def pond(t):
    img = np.zeros((H, W, 3), np.uint8)
    for y in range(H): img[y, :] = [int(c1 + (c2 - c1) * y / H) for c1, c2 in zip((120, 200, 200), (36, 96, 120))]
    for k in range(16):
        x = (k * 157 + t * 10 * (1 + k % 3)) % (W + 60) - 30; y = (k * 293 + t * (24 + 8 * (k % 4))) % 1400
        blend_circle(img, (x, 1400 - y), 5 + k % 5, (220, 245, 245), 0.4)
    poly(img, [(0, 1250), (W, 1250), (W, H), (0, H)], (176, 150, 112))
    for x in range(0, W, 110): ell(img, (x + 50, 1254), (70, 18), (196, 170, 130))
    for x, h in ((80, 260), (200, 180), (900, 300), (1010, 200)):
        pts = [(x + 22 * math.sin(t * 1.3 + y * .02 + x), y) for y in range(1250, 1250 - h, -20)]
        cv2.polylines(img, [np.array(pts, np.int32)], False, (70, 140, 90), 14, cv2.LINE_AA)
    return img

def axo(img, x, y, s=1.0, t=0.0, leg=1.0, glow=0.0):
    pink, dpink, dark = (248, 196, 204), (232, 150, 170), (50, 30, 40)
    sw = 14 * math.sin(t * 3)
    pts = [(x + 150 * s + i * 22 * s, y + 18 * s * math.sin(t * 3 + i * .7) + sw * i * .1) for i in range(0, 9)]
    for i in range(len(pts) - 1): cv2.line(img, (int(pts[i][0]), int(pts[i][1])), (int(pts[i + 1][0]), int(pts[i + 1][1])), pink, int(max(8, (60 - i * 6) * s)), cv2.LINE_AA)
    ell(img, (x + 60 * s, y - 40 * s), (110 * s, 22 * s), (255, 214, 220), 0)
    ell(img, (x, y), (190 * s, 62 * s), pink)
    ell(img, (x - 10 * s, y + 18 * s), (150 * s, 30 * s), (255, 228, 232))
    for lx, ph in ((-60, 0), (80, 1)):
        for off in (0, 1):
            L = 62 * s * (leg if (lx == 80 and off == 0) else 1.0)
            fx = x + lx * s + off * 26 * s; fy = y + 54 * s
            if L > 4:
                cv2.line(img, (int(fx), int(fy)), (int(fx + 10 * s), int(fy + L)), dpink if off else pink, max(6, int(22 * s)), cv2.LINE_AA)
                circle(img, (fx + 10 * s, fy + L), 12 * s, dpink if off else pink)
    hx, hy = x - 175 * s, y - 6 * s
    for sd in (-1, 1):
        for k in range(3):
            a = (-0.9 + sd * .25 + k * .42 * sd) if True else 0
            ang = -1.15 + k * .38; bx, by = hx + 30 * s, hy - 12 * s + sd * 6 * s
            ex = bx - math.sin(abs(ang)) * 110 * s - 20 * s; ey = by + sd * (30 + k * 38) * s - 52 * s + math.sin(t * 4 + k) * 8 * s
            if sd < 0: ey = by - (36 + k * 34) * s + math.sin(t * 4 + k) * 8 * s
            cv2.line(img, (int(bx), int(by)), (int(ex), int(ey)), (236, 96, 120), max(4, int(9 * s)), cv2.LINE_AA)
            for j in range(4):
                tx = bx + (ex - bx) * (.35 + j * .2); ty = by + (ey - by) * (.35 + j * .2)
                cv2.line(img, (int(tx), int(ty)), (int(tx - 20 * s), int(ty + (-1 if sd < 0 else 1) * 14 * s)), (246, 130, 150), max(3, int(5 * s)), cv2.LINE_AA)
    if glow > 0: blend_circle(img, (hx, hy), 150 * s, (255, 220, 230), .25 * glow)
    ell(img, (hx, hy), (96 * s, 74 * s), pink)
    for ex in (-34, 26):
        circle(img, (hx + ex * s - 6 * s, hy - 14 * s), 11 * s, dark); blend_circle(img, (hx + ex * s - 9 * s, hy - 17 * s), 4 * s, (255, 255, 255), .9)
    cv2.ellipse(img, (int(hx - 4 * s), int(hy + 14 * s)), (int(30 * s), int(18 * s)), 0, 5, 175, dark, max(3, int(5 * s)), cv2.LINE_AA)
    for ex in (-52, 44): blend_circle(img, (hx + ex * s, hy + 6 * s), 14 * s, (255, 120, 150), .55)

def heart(img, x, y, r, col=(236, 90, 120)):
    circle(img, (x - r * .5, y - r * .3), r * .55, col); circle(img, (x + r * .5, y - r * .3), r * .55, col)
    poly(img, [(x - r, y - r * .1), (x + r, y - r * .1), (x, y + r * 1.05)], col)

def scene_P(t):
    img = pond(t); jobs = []
    bob = 14 * math.sin(t * 1.5)
    axo(img, 600, 760 + bob, 1.35 if t < S[1] else 1.1, t)
    jobs.append(('text', 'MEET THE AXOLOTL' if t >= S[1] else 'SMILING AND REGROWING', (W / 2, 330), 50, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 60, 80))))
    return img, jobs

def scene_C(t):
    img = pond(t); jobs = []
    p = (t - S[2]) / (S[3] - S[2])
    leg = 1.0 if p < .12 else (0.0 if p < .3 else ease((p - .3) / .6))
    axo(img, 600, 860, 1.2, t, leg=max(0.0, leg))
    msg = 'LOSES A LEG...' if p < .45 else 'GROWS IT BACK'
    jobs.append(('text', msg, (W / 2, 330), 56, (255, 220, 200) if p < .45 else (210, 255, 210), 'Poppins-Bold.ttf', (5, (20, 60, 80))))
    if p >= .45: jobs.append(('text', 'bones + muscles + nerves', (W / 2, 410), 36, (255, 246, 232), 'Poppins-Medium.ttf', (4, (20, 60, 80))))
    return img, jobs

def scene_D(t):
    img = cv2.GaussianBlur(pond(t), (0, 0), 10); jobs = []
    a = back((t - S[3] + .1) / .5)
    items = [('HEART', (270, 800)), ('SPINE', (540, 800)), ('BRAIN', (810, 800))]
    for i, (lab, (x, y)) in enumerate(items):
        q = ease((t - S[3] - .5 - i * .6) / .5)
        circle(img, (x, y), 110 * q, (255, 240, 244))
        if q > .6:
            if i == 0: heart(img, x, y - 6, 52 * q)
            elif i == 1:
                for k in range(5): rrect(img, x - 30, y - 80 + k * 34, x + 30, y - 56 + k * 34, 8, (200, 150, 170))
            else:
                ell(img, (x, y), (62 * q, 48 * q), (236, 170, 190)); cv2.line(img, (int(x), int(y - 44)), (int(x), int(y + 44)), (200, 120, 150), 4, cv2.LINE_AA)
            jobs.append(('text', lab, (x, y + 150), max(10, int(34 * q)), (255, 246, 232), 'Poppins-Bold.ttf', (4, (20, 60, 80))))
    jobs.append(('text', 'IT CAN REPAIR', (W / 2, 330), 56, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 60, 80))))
    if t > S[4]: jobs.append(('text', 'SCIENTISTS STUDY IT', (W / 2, 1010), 40, (255, 220, 160), 'Poppins-Bold.ttf', (5, (20, 60, 80))))
    return img, jobs

def scene_G(t):
    img = pond(t); jobs = []
    axo(img, 600, 800 + 12 * math.sin(t * 1.5), 1.3, t, glow=.5 + .5 * math.sin(t * 2))
    for k in range(5): heart(img, 150 + k * 190 + 10 * math.sin(t * 2 + k), 520 + 30 * math.sin(t * 1.5 + k), 14 + 4 * math.sin(k), (255, 150, 180))
    jobs.append(('text', 'FEATHERY GILLS FOR LIFE' if t < S[6] else 'REAL-LIFE SUPERHERO', (W / 2, 330), 46, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 60, 80))))
    return img, jobs

def scene_F(t):
    img = cv2.GaussianBlur(pond(t), (0, 0), 16)
    from PIL import Image
    lg = np.asarray(Image.open('logo.png').convert('RGB')); ys, xs = np.where(lg.min(axis=2) < 245); lg = lg[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    r = int(190 * back((t - S[-1]) / .5))
    if r > 10:
        s = cv2.resize(lg, (2 * r, 2 * r)); m = np.zeros((2 * r, 2 * r), np.uint8); cv2.circle(m, (r, r), r, 255, -1)
        roi = img[700 - r:700 + r, 540 - r:540 + r]; roi[m > 0] = s[m > 0]
    jobs = [('text', '@itsfruitsoda', (W / 2, 1000), 64, (255, 246, 232), 'Poppins-Bold.ttf', (5, (20, 60, 80)))]
    rrect(img, 300, 1070, 780, 1170, 50, (232, 98, 96)); jobs.append(('text', 'FOLLOW', (W / 2, 1120), 56, (255, 255, 255), 'Poppins-Bold.ttf', None))
    return img, jobs

def sid(t):
    if t < S[2]: return 'P'
    if t < S[3]: return 'C'
    if t < S[5]: return 'D'
    if t < S[-1]: return 'G'
    return 'F'
SC = dict(P=scene_P, C=scene_C, D=scene_D, G=scene_G, F=scene_F)
KEY = set(SPEC.get('key', []))
BOUND = {'C': S[2], 'D': S[3], 'G': S[5], 'F': S[-1]}; PREV = {'C': 'P', 'D': 'C', 'G': 'D', 'F': 'G'}
