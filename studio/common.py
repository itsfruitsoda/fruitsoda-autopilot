def frame(t):
    s = sid(t); img, jobs = SC[s](t)
    if s in BOUND and t - BOUND[s] < 0.4:
        pimg, _ = SC[PREV[s]](BOUND[s] - 0.01); a = ease((t - BOUND[s]) / 0.4); img = cv2.addWeighted(img, a, pimg, 1 - a, 0)
    z = 1.0 + 0.03 * (t / total); M = cv2.getRotationMatrix2D((W / 2, H * .55), 0, z); img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    img = finish(img, 0.04); img = text_pass(img, jobs)
    i = 0
    for k in range(len(lines)):
        if t >= S[k] - 0.02: i = k
    if s != 'F': img = caption(img, WORDS[i], WT[i], t, cy=1340, key=KEY)
    img = np.array(brand(img))
    cv2.rectangle(img, (0, 0), (int(W * clamp(t / total)), 8), (255, 214, 120), -1)
    return img

n = int(total * 30)
mus = SPEC.get('music', 'happy_life.mp3')
def _ok(p):
    return os.path.exists(p) and subprocess.run(['ffmpeg', '-v', 'error', '-t', '2', '-i', p, '-f', 'null', '-'], capture_output=True).returncode == 0
if not _ok('music/' + mus):
    import urllib.request, urllib.parse
    os.makedirs('music', exist_ok=True)
    nm = os.path.splitext(mus)[0].replace('_', ' ').title()
    try: urllib.request.urlretrieve('https://raw.githubusercontent.com/effacestudios/Royalty-Free-Music-Pack/master/' + urllib.parse.quote(nm) + '.mp3', 'music/' + mus)
    except Exception as e: print('music fetch failed', e)
    if not _ok('music/' + mus):
        _m = [t for t in sorted(glob.glob('music/*.mp3')) if _ok(t)]
        mus = os.path.basename(_m[0]) if _m else mus
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-stream_loop', '-1', '-i', 'music/' + mus, '-t', str(total + 1), '-ar', '44100', '-ac', '1', '/tmp/par2/music.wav'], check=True)
cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-', '-i', '/tmp/par2/vo.wav', '-i', '/tmp/par2/music.wav',
       '-filter_complex', f'[1:a]aresample=44100,apad[v];[2:a]aresample=44100,volume=0.12[m];[v][m]amix=inputs=2:duration=first:normalize=0,atrim=0:{total},loudnorm=I=-14:TP=-1.5[a]',
       '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', '-t', str(total), OUT]
pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
only = sys.argv[3] if len(sys.argv) > 3 else None
if only is not None:
    pr.stdin.close(); pr.kill()
    from PIL import Image
    ts = [float(x) for x in only.split(',')]
    ims = [Image.fromarray(frame(x)).resize((360, 640)) for x in ts]
    cols = min(4, len(ims)); rows = (len(ims) + cols - 1) // cols
    SH = Image.new('RGB', (360 * cols, 640 * rows))
    for i, im in enumerate(ims): SH.paste(im, ((i % cols) * 360, (i // cols) * 640))
    SH.save('/tmp/par2/sheet.png'); sys.exit()
for k in range(n):
    pr.stdin.write(frame(k / 30).tobytes())
pr.stdin.close(); pr.wait(); print('done', OUT)
